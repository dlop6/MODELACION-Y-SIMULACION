"""tabla comparativa por destino: ruta actual contra las del algoritmo."""

from __future__ import annotations

from dataclasses import dataclass

from logistica.politicas import BODEGA, DESTINOS, RUTAS_ACTUALES, PlanInvalido, ruta_declarada
from logistica.red import Red
from logistica.rutas import Ruta, yen

LIMITE_PUNTUAL_MIN = 75.0


@dataclass(frozen=True)
class FilaComparacion:
    destino: str
    opcion: str
    ida: Ruta | None
    regreso: Ruta | None
    nota: str = ""

    @property
    def valida(self) -> bool:
        return self.ida is not None and self.regreso is not None

    @property
    def ciclo(self) -> float | None:
        return self.ida.tiempo + self.regreso.tiempo if self.valida else None


def comparar_rutas(red: Red, k: int = 3) -> list[FilaComparacion]:
    """por destino: la actual, la de dijkstra y k-1 alternativas de yen."""
    filas = []
    for destino in DESTINOS:
        filas.append(_fila_actual(red, destino))
        idas = yen(red, BODEGA, destino, k)
        regresos = yen(red, destino, BODEGA, k)
        # se emparejan por posición: la i-ésima ida con el i-ésimo regreso
        for i, (ida, regreso) in enumerate(zip(idas, regresos)):
            opcion = "algoritmo" if i == 0 else f"alternativa {i}"
            filas.append(FilaComparacion(destino, opcion, ida, regreso))
    return filas


def es_puntual_sin_espera(
    fila: FilaComparacion, descarga: float = 0.0, limite: float = LIMITE_PUNTUAL_MIN
) -> bool | None:
    if fila.ida is None:
        return None
    return fila.ida.tiempo + descarga <= limite


def tabla_rutas(
    filas: list[FilaComparacion], descarga: float = 0.0, limite: float = LIMITE_PUNTUAL_MIN
) -> list[dict]:
    """versión plana de la comparación, lista para csv o dataframe."""
    ciclos_actuales = {f.destino: f.ciclo for f in filas if f.opcion == "actual"}
    tabla = []
    for fila in filas:
        actual = ciclos_actuales.get(fila.destino)
        tabla.append(
            {
                "destino": fila.destino,
                "opcion": fila.opcion,
                "ruta_ida": _texto(fila.ida),
                "tiempo_ida": fila.ida.tiempo if fila.ida else None,
                "ruta_regreso": _texto(fila.regreso),
                "tiempo_regreso": fila.regreso.tiempo if fila.regreso else None,
                "ciclo": fila.ciclo,
                "ahorro_ciclo_vs_actual": actual - fila.ciclo if actual is not None and fila.valida else None,
                "puntual_sin_espera": es_puntual_sin_espera(fila, descarga, limite),
                "nota": fila.nota,
            }
        )
    return tabla


def _texto(ruta: Ruta | None) -> str:
    return "-".join(ruta.nodos) if ruta else ""


def _fila_actual(red: Red, destino: str) -> FilaComparacion:
    nodos = RUTAS_ACTUALES[destino]
    try:
        ida = ruta_declarada(red, nodos, destino, "ida")
        regreso = ruta_declarada(red, nodos[::-1], destino, "regreso")
    except PlanInvalido as error:
        return FilaComparacion(destino, "actual", None, None, f"inválida: {error}")
    return FilaComparacion(destino, "actual", ida, regreso)
