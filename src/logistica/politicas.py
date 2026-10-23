"""políticas de rutas: las que usan hoy los conductores y las óptimas."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from logistica.red import Red, RutaInvalida
from logistica.rutas import Ruta, dijkstra

BODEGA = "N01"
RUTAS_ACTUALES = MappingProxyType(
    {
        "N08": ("N01", "N02", "N03", "N04", "N05", "N06", "N07", "N08"),
        "N19": ("N01", "N02", "N03", "N11", "N19"),
        "N34": ("N01", "N09", "N17", "N25", "N33", "N34"),
        "N40": ("N01", "N02", "N03", "N04", "N05", "N06", "N07", "N08", "N16", "N24", "N32", "N40"),
    }
)
DESTINOS = tuple(RUTAS_ACTUALES)


class PlanInvalido(ValueError):
    """alguna ruta del plan no se puede recorrer en la red actual."""

    def __init__(self, destino: str, sentido: str, tramo: tuple[str, str] | None) -> None:
        detalle = f"tramo {tramo[0]}->{tramo[1]} no disponible" if tramo else "sin camino"
        super().__init__(f"{destino} ({sentido}): {detalle}")
        self.destino = destino
        self.sentido = sentido
        self.tramo = tramo


@dataclass(frozen=True)
class TiemposRuta:
    ida: float
    regreso: float

    @property
    def ciclo(self) -> float:
        return self.ida + self.regreso


@dataclass(frozen=True)
class RutasDestino:
    ida: Ruta
    regreso: Ruta

    @property
    def tiempos(self) -> TiemposRuta:
        return TiemposRuta(self.ida.tiempo, self.regreso.tiempo)


PlanRutas = dict[str, RutasDestino]


def ruta_declarada(red: Red, nodos: tuple[str, ...], destino: str, sentido: str) -> Ruta:
    try:
        return Ruta(nodos, red.costo(nodos))
    except RutaInvalida as error:
        raise PlanInvalido(destino, sentido, error.tramo) from error


def plan_actual(red: Red) -> PlanRutas:
    """la hoja de despacho: ida declarada y regreso por el mismo camino al revés."""
    return {
        destino: RutasDestino(
            ruta_declarada(red, nodos, destino, "ida"),
            ruta_declarada(red, nodos[::-1], destino, "regreso"),
        )
        for destino, nodos in RUTAS_ACTUALES.items()
    }


def plan_optimo(red: Red) -> PlanRutas:
    """dijkstra por separado en cada sentido, porque la red es asimétrica."""
    plan = {}
    for destino in DESTINOS:
        ida = dijkstra(red, BODEGA, destino)
        if ida is None:
            raise PlanInvalido(destino, "ida", None)
        regreso = dijkstra(red, destino, BODEGA)
        if regreso is None:
            raise PlanInvalido(destino, "regreso", None)
        plan[destino] = RutasDestino(ida, regreso)
    return plan


def tiempos(plan: PlanRutas) -> dict[str, TiemposRuta]:
    return {destino: rutas.tiempos for destino, rutas in plan.items()}
