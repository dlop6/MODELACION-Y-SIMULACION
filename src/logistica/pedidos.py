"""generación de pedidos: llegadas de poisson y destino uniforme."""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass

TASA_MAXIMA = 60.0
DURACION_MINIMA_H = 0.5
DURACION_MAXIMA_H = 24.0


@dataclass(frozen=True)
class Pedido:
    id: int
    llegada: float
    destino: str


def generar_pedidos(
    pedidos_por_hora: float, duracion_h: float, destinos: Sequence[str], semilla: int
) -> tuple[Pedido, ...]:
    """tiempos entre llegadas exponenciales (en minutos) mientras dure la recepción."""
    if not 0 < pedidos_por_hora <= TASA_MAXIMA:
        raise ValueError(f"pedidos por hora fuera de (0, {TASA_MAXIMA}]")
    if not DURACION_MINIMA_H <= duracion_h <= DURACION_MAXIMA_H:
        raise ValueError(f"duración fuera de [{DURACION_MINIMA_H}, {DURACION_MAXIMA_H}] h")
    if not destinos:
        raise ValueError("se necesita al menos un destino")
    if isinstance(semilla, bool) or not isinstance(semilla, int) or semilla < 0:
        raise ValueError("la semilla debe ser un entero >= 0")

    # random normal está bien acá: es simulación, no criptografía
    azar = random.Random(semilla)
    tasa_min = pedidos_por_hora / 60
    fin = duracion_h * 60
    pedidos = []
    instante = azar.expovariate(tasa_min)
    while instante < fin:
        pedidos.append(Pedido(len(pedidos), instante, azar.choice(destinos)))
        instante += azar.expovariate(tasa_min)
    return tuple(pedidos)
