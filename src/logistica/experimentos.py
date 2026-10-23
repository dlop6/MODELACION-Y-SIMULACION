"""experimentos pareados: mismos pedidos para las dos políticas en cada réplica."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, replace

from logistica.comparacion import LIMITE_PUNTUAL_MIN
from logistica.escenarios import Escenario
from logistica.metricas import Metricas, calcular_metricas, resumir
from logistica.pedidos import Pedido, generar_pedidos
from logistica.politicas import DESTINOS, PlanInvalido, TiemposRuta, plan_actual, plan_optimo, tiempos
from logistica.red import Red
from logistica.simulacion import ConfigSim, ResultadoSim, simular

REPLICAS_MAXIMAS = 200
PLANIFICADORES = {"actual": plan_actual, "algoritmo": plan_optimo}

Planes = dict[str, dict[str, TiemposRuta]]


@dataclass(frozen=True)
class Parametros:
    duracion_h: float = 8.0
    vehiculos: int = 8
    descarga: float = 0.0
    limite_puntual: float = LIMITE_PUNTUAL_MIN
    replicas: int = 30
    semilla_base: int = 1

    def __post_init__(self) -> None:
        if not 1 <= self.replicas <= REPLICAS_MAXIMAS:
            raise ValueError(f"réplicas fuera de [1, {REPLICAS_MAXIMAS}]")
        if not 0 < self.limite_puntual <= 24 * 60:
            raise ValueError("límite de puntualidad fuera de rango")
        # la config de la simulación valida vehículos y descarga
        ConfigSim(self.vehiculos, self.descarga)


@dataclass(frozen=True)
class Corrida:
    escenario: str
    politica: str
    replica: int
    semilla: int
    vehiculos: int
    metricas: Metricas


def construir_planes(red: Red) -> tuple[Planes, dict[str, str]]:
    """planes que se pueden recorrer y, aparte, el motivo de los que no."""
    planes, errores = {}, {}
    for nombre, planificar in PLANIFICADORES.items():
        try:
            planes[nombre] = tiempos(planificar(red))
        except PlanInvalido as error:
            errores[nombre] = str(error)
    return planes, errores


def simular_politicas(
    planes: Mapping[str, Mapping[str, TiemposRuta]],
    pedidos: Sequence[Pedido],
    parametros: Parametros,
) -> dict[str, tuple[ResultadoSim, Metricas]]:
    """la misma lista de pedidos pasa por cada política."""
    config = ConfigSim(parametros.vehiculos, parametros.descarga)
    salida = {}
    for politica, plan in planes.items():
        resultado = simular(pedidos, plan, config)
        salida[politica] = (
            resultado,
            calcular_metricas(resultado, parametros.duracion_h * 60, parametros.limite_puntual),
        )
    return salida


def correr_pareado(
    planes: Mapping[str, Mapping[str, TiemposRuta]],
    escenarios: Sequence[Escenario],
    parametros: Parametros,
) -> list[Corrida]:
    corridas = []
    for escenario in escenarios:
        for replica in range(parametros.replicas):
            semilla = parametros.semilla_base + replica
            # una sola lista de pedidos por réplica, compartida por todas las políticas
            pedidos = generar_pedidos(escenario.pedidos_por_hora, parametros.duracion_h, DESTINOS, semilla)
            for politica, (_, metricas) in simular_politicas(planes, pedidos, parametros).items():
                corridas.append(
                    Corrida(escenario.nombre, politica, replica, semilla, parametros.vehiculos, metricas)
                )
    return corridas


def barrido_vehiculos(
    planes: Mapping[str, Mapping[str, TiemposRuta]],
    escenarios: Sequence[Escenario],
    parametros: Parametros,
    flotas: Iterable[int],
) -> list[Corrida]:
    corridas = []
    for vehiculos in flotas:
        corridas += correr_pareado(planes, escenarios, replace(parametros, vehiculos=vehiculos))
    return corridas


def tabla_corridas(corridas: Iterable[Corrida]) -> list[dict]:
    filas = []
    for corrida in corridas:
        fila = {k: v for k, v in asdict(corrida).items() if k != "metricas"}
        filas.append(fila | asdict(corrida.metricas))
    return filas


def tabla_resumen(corridas: Iterable[Corrida]) -> list[dict]:
    """una fila por escenario, política y flota, con media e ic95 de cada indicador."""
    grupos: dict[tuple[str, str, int], list[Metricas]] = defaultdict(list)
    for corrida in corridas:
        grupos[(corrida.escenario, corrida.politica, corrida.vehiculos)].append(corrida.metricas)
    filas = []
    for (escenario, politica, vehiculos), metricas in grupos.items():
        fila = {"escenario": escenario, "politica": politica, "vehiculos": vehiculos, "replicas": len(metricas)}
        for campo, resumen in resumir(metricas).items():
            fila[f"{campo}_media"] = resumen.media
            fila[f"{campo}_ic95"] = resumen.ic95
        filas.append(fila)
    return filas

