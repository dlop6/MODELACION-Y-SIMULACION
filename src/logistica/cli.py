"""exporta rutas, experimentos y gráficas a csv y png de forma reproducible."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from pathlib import Path

from logistica.comparacion import LIMITE_PUNTUAL_MIN, comparar_rutas, tabla_rutas
from logistica.escenarios import ESCENARIOS
from logistica.experimentos import (
    REPLICAS_MAXIMAS,
    Parametros,
    barrido_vehiculos,
    construir_planes,
    correr_pareado,
    tabla_corridas,
    tabla_resumen,
)
from logistica.exportar import filas_a_csv
from logistica.graficas import fig_barrido, fig_metricas, fig_red
from logistica.metricas import INDICADORES_CLAVE
from logistica.pedidos import DURACION_MAXIMA_H, DURACION_MINIMA_H
from logistica.politicas import DESTINOS, plan_actual, plan_optimo
from logistica.red import MATRIZ_POR_DEFECTO, Incidente, Red, aplicar_incidentes, cargar_red
from logistica.simulacion import DESCARGA_MAXIMA, VEHICULOS_MAXIMOS

# los dos incidentes de estudio: el atajo más usado cerrado y su vecino congestionado
INCIDENTES_ESTUDIO = (
    (Incidente("N01", "N17"),),
    (Incidente("N09", "N17", 18.0),),
)


def _rango(tipo: Callable, minimo: float, maximo: float) -> Callable[[str], float]:
    def convertir(texto: str):
        try:
            valor = tipo(texto)
        except ValueError as error:
            raise argparse.ArgumentTypeError(f"valor inválido: {texto!r}") from error
        if not minimo <= valor <= maximo:
            raise argparse.ArgumentTypeError(f"debe estar en [{minimo}, {maximo}]")
        return valor

    return convertir


def crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m logistica.cli", description=__doc__)
    parser.add_argument("--matriz", type=Path, default=MATRIZ_POR_DEFECTO)
    parser.add_argument("--salida", type=Path, default=Path("resultados"))
    parser.add_argument("--replicas", type=_rango(int, 1, REPLICAS_MAXIMAS), default=30)
    parser.add_argument("--semilla", type=_rango(int, 0, 2**31 - 1), default=1)
    parser.add_argument("--vehiculos", type=_rango(int, 1, VEHICULOS_MAXIMOS), default=8)
    parser.add_argument("--duracion", type=_rango(float, DURACION_MINIMA_H, DURACION_MAXIMA_H), default=8.0)
    parser.add_argument("--descarga", type=_rango(float, 0, DESCARGA_MAXIMA), default=0.0)
    parser.add_argument("--limite", type=_rango(float, 1, 24 * 60), default=LIMITE_PUNTUAL_MIN)
    parser.add_argument("--flota-min", type=_rango(int, 1, VEHICULOS_MAXIMOS), default=4)
    parser.add_argument("--flota-max", type=_rango(int, 1, VEHICULOS_MAXIMOS), default=20)
    parser.add_argument("--k", type=_rango(int, 2, 10), default=3, help="rutas por destino y sentido")
    return parser


def escribir_csv(ruta: Path, filas: Sequence[dict]) -> None:
    ruta.write_text(filas_a_csv(filas), encoding="utf-8")


def _guardar(figura, ruta: Path) -> None:
    figura.savefig(ruta, dpi=120)


def exportar_red(red: Red, salida: Path) -> None:
    _guardar(fig_red(red), salida / "red.png")
    actual, optimo = plan_actual(red), plan_optimo(red)
    for destino in DESTINOS:
        resaltar = {
            "actual (ida y regreso)": actual[destino].ida.nodos,
            "algoritmo ida": optimo[destino].ida.nodos,
            "algoritmo regreso": optimo[destino].regreso.nodos,
        }
        _guardar(fig_red(red, resaltar, f"rutas hacia {destino}"), salida / f"rutas_{destino}.png")


def exportar_incidentes(red: Red, parametros: Parametros, k: int, salida: Path) -> None:
    rutas, resumen = [], []
    for incidentes in INCIDENTES_ESTUDIO:
        nombre = ", ".join(i.describir() for i in incidentes)
        modificada = aplicar_incidentes(red, incidentes)
        rutas += [{"incidente": nombre} | f for f in tabla_rutas(comparar_rutas(modificada, k), parametros.descarga, parametros.limite_puntual)]
        planes, errores = construir_planes(modificada)
        resumen += [{"incidente": nombre} | f for f in tabla_resumen(correr_pareado(planes, ESCENARIOS, parametros))]
        resumen += [{"incidente": nombre, "politica": p, "nota": e} for p, e in errores.items()]
    escribir_csv(salida / "incidentes_rutas.csv", rutas)
    escribir_csv(salida / "incidentes_resumen.csv", resumen)


def main(argv: Sequence[str] | None = None) -> int:
    parser = crear_parser()
    args = parser.parse_args(argv)
    if args.flota_min > args.flota_max:
        parser.error("--flota-min no puede ser mayor que --flota-max")
    parametros = Parametros(args.duracion, args.vehiculos, args.descarga, args.limite, args.replicas, args.semilla)
    red = cargar_red(args.matriz)
    salida = args.salida.resolve()
    salida.mkdir(parents=True, exist_ok=True)

    escribir_csv(salida / "rutas.csv", tabla_rutas(comparar_rutas(red, args.k), args.descarga, args.limite))
    exportar_red(red, salida)

    planes, _ = construir_planes(red)
    corridas = correr_pareado(planes, ESCENARIOS, parametros)
    resumen = tabla_resumen(corridas)
    escribir_csv(salida / "replicas.csv", tabla_corridas(corridas))
    escribir_csv(salida / "resumen.csv", resumen)

    barrido = tabla_resumen(barrido_vehiculos(planes, ESCENARIOS, parametros, range(args.flota_min, args.flota_max + 1)))
    escribir_csv(salida / "barrido.csv", barrido)
    for indicador in INDICADORES_CLAVE:
        _guardar(fig_metricas(resumen, indicador), salida / f"metricas_{indicador}.png")
        _guardar(fig_barrido(barrido, indicador), salida / f"barrido_{indicador}.png")

    exportar_incidentes(red, parametros, args.k, salida)
    print(f"resultados guardados en {salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
