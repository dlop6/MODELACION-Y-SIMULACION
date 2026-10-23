"""simulación de eventos discretos de la flota: cola fifo y vehículos de un pedido."""

from __future__ import annotations

import heapq
from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from logistica.pedidos import Pedido
from logistica.politicas import TiemposRuta

VEHICULOS_MAXIMOS = 100
DESCARGA_MAXIMA = 120.0

# a igual instante primero vuelve el vehículo y luego entra el pedido
_REGRESO, _LLEGADA = 0, 1


@dataclass(frozen=True)
class ConfigSim:
    vehiculos: int = 8
    descarga: float = 0.0

    def __post_init__(self) -> None:
        if isinstance(self.vehiculos, bool) or not isinstance(self.vehiculos, int):
            raise ValueError("vehiculos debe ser entero")
        if not 1 <= self.vehiculos <= VEHICULOS_MAXIMOS:
            raise ValueError(f"vehiculos fuera de [1, {VEHICULOS_MAXIMOS}]")
        if not 0 <= self.descarga <= DESCARGA_MAXIMA:
            raise ValueError(f"descarga fuera de [0, {DESCARGA_MAXIMA}]")


@dataclass(frozen=True)
class Registro:
    pedido: Pedido
    vehiculo: int
    inicio: float
    entrega: float
    regreso: float

    @property
    def espera(self) -> float:
        return self.inicio - self.pedido.llegada

    @property
    def solicitud_entrega(self) -> float:
        return self.entrega - self.pedido.llegada


@dataclass(frozen=True)
class ResultadoSim:
    registros: tuple[Registro, ...]
    vehiculos: int


def simular(
    pedidos: Sequence[Pedido], tiempos: Mapping[str, TiemposRuta], config: ConfigSim
) -> ResultadoSim:
    """corre hasta despachar todos los pedidos, aunque se pase de la recepción."""
    sin_ruta = {p.destino for p in pedidos} - set(tiempos)
    if sin_ruta:
        raise ValueError(f"destinos sin ruta en la política: {sorted(sin_ruta)}")

    eventos: list[tuple[float, int, int, object]] = []
    for secuencia, pedido in enumerate(pedidos):
        heapq.heappush(eventos, (pedido.llegada, _LLEGADA, secuencia, pedido))
    secuencia = len(pedidos)
    libres = list(range(config.vehiculos))
    cola: deque[Pedido] = deque()
    registros = []

    while eventos:
        instante, tipo, _, dato = heapq.heappop(eventos)
        if tipo == _REGRESO:
            heapq.heappush(libres, dato)
        else:
            cola.append(dato)
        while cola and libres:
            vehiculo = heapq.heappop(libres)
            pedido = cola.popleft()
            ruta = tiempos[pedido.destino]
            entrega = instante + ruta.ida + config.descarga
            regreso = entrega + ruta.regreso
            registros.append(Registro(pedido, vehiculo, instante, entrega, regreso))
            heapq.heappush(eventos, (regreso, _REGRESO, secuencia, vehiculo))
            secuencia += 1

    registros.sort(key=lambda r: r.pedido.id)
    return ResultadoSim(tuple(registros), config.vehiculos)
