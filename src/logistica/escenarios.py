"""escenarios de demanda que pide la gerencia."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Escenario:
    nombre: str
    pedidos_por_hora: float


ESCENARIOS = (
    Escenario("normal", 4.0),
    Escenario("semana santa", 6.0),
    Escenario("navidad", 10.0),
)
