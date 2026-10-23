"""grafo dirigido de la red vial y carga validada de la matriz de adyacencia."""

from __future__ import annotations

import csv
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

MATRIZ_POR_DEFECTO = (
    Path(__file__).resolve().parents[2] / "docs" / "Matriz_Logistica_del_Valle_40_nodos.csv"
)
TIEMPO_MAXIMO_TRAMO = 500.0
_PATRON_NODO = re.compile(r"^N\d{2}$")
_SIN_CONEXION = {"", "-", "—"}
_TAMANO_MAXIMO_CSV = 1_000_000


class RedInvalida(ValueError):
    """la matriz o la red no cumplen el formato esperado."""


class RutaInvalida(ValueError):
    """la ruta usa un tramo que no existe en la red."""

    def __init__(self, mensaje: str, tramo: tuple[str, str] | None = None) -> None:
        super().__init__(mensaje)
        self.tramo = tramo


def validar_tiempo(tiempo: float) -> float:
    tiempo = float(tiempo)
    if not math.isfinite(tiempo) or not 0 < tiempo <= TIEMPO_MAXIMO_TRAMO:
        raise RedInvalida(f"tiempo de tramo fuera de rango (0, {TIEMPO_MAXIMO_TRAMO}]: {tiempo}")
    return tiempo


@dataclass(frozen=True)
class Red:
    """red dirigida inmutable; arcos[o][d] son los minutos de o a d."""

    nodos: tuple[str, ...]
    arcos: Mapping[str, Mapping[str, float]]

    def __post_init__(self) -> None:
        nodos = tuple(self.nodos)
        conjunto = set(nodos)
        if len(conjunto) != len(nodos):
            raise RedInvalida("hay nodos repetidos")
        extra = set(self.arcos) - conjunto
        if extra:
            raise RedInvalida(f"arcos desde nodos desconocidos: {sorted(extra)}")
        congelados = {}
        for origen in nodos:
            salientes = {}
            for destino, tiempo in self.arcos.get(origen, {}).items():
                if destino not in conjunto:
                    raise RedInvalida(f"arco hacia nodo desconocido: {origen}->{destino}")
                if destino == origen:
                    raise RedInvalida(f"no se permiten lazos: {origen}->{destino}")
                salientes[destino] = validar_tiempo(tiempo)
            congelados[origen] = MappingProxyType(salientes)
        # se congela todo para que nadie mute la red original por accidente
        object.__setattr__(self, "nodos", nodos)
        object.__setattr__(self, "arcos", MappingProxyType(congelados))

    def tiempo(self, origen: str, destino: str) -> float | None:
        return self.arcos.get(origen, {}).get(destino)

    def lista_arcos(self) -> list[tuple[str, str, float]]:
        return [(o, d, t) for o in self.nodos for d, t in self.arcos[o].items()]

    def costo(self, ruta: Sequence[str]) -> float:
        if len(ruta) < 2:
            raise RutaInvalida("una ruta necesita al menos dos nodos")
        total = 0.0
        for origen, destino in zip(ruta, ruta[1:]):
            tiempo = self.tiempo(origen, destino)
            if tiempo is None:
                raise RutaInvalida(f"no existe el tramo {origen}->{destino}", (origen, destino))
            total += tiempo
        return total

    def es_valida(self, ruta: Sequence[str]) -> bool:
        try:
            self.costo(ruta)
        except RutaInvalida:
            return False
        return True

    def con_tiempo(self, origen: str, destino: str, tiempo: float) -> Red:
        self._exigir_arco(origen, destino)
        return self._con_cambio(origen, destino, validar_tiempo(tiempo))

    def sin_arco(self, origen: str, destino: str) -> Red:
        self._exigir_arco(origen, destino)
        return self._con_cambio(origen, destino, None)

    def _exigir_arco(self, origen: str, destino: str) -> None:
        if self.tiempo(origen, destino) is None:
            raise RedInvalida(f"no existe el tramo {origen}->{destino}")

    def _con_cambio(self, origen: str, destino: str, tiempo: float | None) -> Red:
        arcos = {o: dict(salientes) for o, salientes in self.arcos.items()}
        if tiempo is None:
            del arcos[origen][destino]
        else:
            arcos[origen][destino] = tiempo
        return Red(self.nodos, arcos)


@dataclass(frozen=True)
class Incidente:
    """tiempo None = tramo cerrado; si no, nuevo tiempo del tramo."""

    origen: str
    destino: str
    tiempo: float | None = None

    def describir(self) -> str:
        cambio = "cerrado" if self.tiempo is None else f"{self.tiempo:g} min"
        return f"{self.origen}->{self.destino} {cambio}"


def aplicar_incidentes(red: Red, incidentes: Sequence[Incidente]) -> Red:
    for incidente in incidentes:
        if incidente.tiempo is None:
            red = red.sin_arco(incidente.origen, incidente.destino)
        else:
            red = red.con_tiempo(incidente.origen, incidente.destino, incidente.tiempo)
    return red


def cargar_red(ruta: str | Path = MATRIZ_POR_DEFECTO) -> Red:
    """lee la matriz origen x destino; vacío o guion = sin conexión directa."""
    ruta = Path(ruta)
    if not ruta.is_file():
        raise RedInvalida(f"no se encontró la matriz: {ruta}")
    if ruta.stat().st_size > _TAMANO_MAXIMO_CSV:
        raise RedInvalida("la matriz es demasiado grande")
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        filas = [fila for fila in csv.reader(archivo) if any(c.strip() for c in fila)]
    if len(filas) < 2:
        raise RedInvalida("la matriz está vacía")

    nodos = [c.strip() for c in filas[0][1:]]
    for nodo in nodos:
        if not _PATRON_NODO.match(nodo):
            raise RedInvalida(f"nombre de nodo inválido: {nodo!r}")
    if len(filas) - 1 != len(nodos):
        raise RedInvalida("la matriz no es cuadrada")

    arcos: dict[str, dict[str, float]] = {}
    for i, fila in enumerate(filas[1:]):
        origen = fila[0].strip()
        if origen != nodos[i]:
            raise RedInvalida(f"la fila {i + 1} debería ser {nodos[i]} y es {origen!r}")
        celdas = fila[1:]
        if len(celdas) != len(nodos):
            raise RedInvalida(f"la fila {origen} no tiene {len(nodos)} columnas")
        arcos[origen] = {}
        for destino, celda in zip(nodos, celdas):
            valor = celda.strip()
            if valor in _SIN_CONEXION:
                continue
            try:
                tiempo = float(valor)
            except ValueError as error:
                raise RedInvalida(f"valor no numérico en {origen}->{destino}: {valor!r}") from error
            if destino == origen:
                if tiempo != 0:
                    raise RedInvalida(f"la diagonal de {origen} debe ser 0")
                continue
            arcos[origen][destino] = tiempo
    return Red(tuple(nodos), arcos)
