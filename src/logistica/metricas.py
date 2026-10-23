"""indicadores de una corrida y resumen estadístico de varias réplicas."""

from __future__ import annotations

import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass, fields

from logistica.comparacion import LIMITE_PUNTUAL_MIN
from logistica.simulacion import ResultadoSim

_Z_95 = 1.96
ETIQUETAS = {
    "pedidos": "pedidos recibidos",
    "puntuales": "entregas puntuales",
    "porcentaje_puntual": "entregas puntuales (%)",
    "espera_promedio": "espera promedio (min)",
    "solicitud_entrega_promedio": "solicitud a entrega promedio (min)",
    "utilizacion": "utilización de vehículos",
    "tiempo_extra": "tiempo extra tras la recepción (min)",
    "fin": "fin de la operación (min)",
}
INDICADORES_CLAVE = (
    "porcentaje_puntual",
    "espera_promedio",
    "solicitud_entrega_promedio",
    "utilizacion",
    "tiempo_extra",
)


@dataclass(frozen=True)
class Metricas:
    pedidos: int
    puntuales: int
    porcentaje_puntual: float
    espera_promedio: float
    solicitud_entrega_promedio: float
    utilizacion: float
    tiempo_extra: float
    fin: float


@dataclass(frozen=True)
class Resumen:
    media: float
    desviacion: float
    ic95: float


def calcular_metricas(
    resultado: ResultadoSim, recepcion_min: float, limite_puntual: float = LIMITE_PUNTUAL_MIN
) -> Metricas:
    registros = resultado.registros
    if not registros:
        return Metricas(0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    total = len(registros)
    puntuales = sum(r.solicitud_entrega <= limite_puntual for r in registros)
    fin = max(r.regreso for r in registros)
    ocupado = sum(r.regreso - r.inicio for r in registros)
    return Metricas(
        pedidos=total,
        puntuales=puntuales,
        porcentaje_puntual=100 * puntuales / total,
        espera_promedio=statistics.fmean(r.espera for r in registros),
        solicitud_entrega_promedio=statistics.fmean(r.solicitud_entrega for r in registros),
        utilizacion=ocupado / (resultado.vehiculos * fin),
        tiempo_extra=max(0.0, fin - recepcion_min),
        fin=fin,
    )


def resumir(corridas: Sequence[Metricas]) -> dict[str, Resumen]:
    """media, desviación muestral e ic95 con aproximación normal, por indicador."""
    if not corridas:
        raise ValueError("no hay corridas que resumir")
    resumen = {}
    for campo in fields(Metricas):
        valores = [float(getattr(m, campo.name)) for m in corridas]
        desviacion = statistics.stdev(valores) if len(valores) > 1 else 0.0
        resumen[campo.name] = Resumen(
            statistics.fmean(valores), desviacion, _Z_95 * desviacion / math.sqrt(len(valores))
        )
    return resumen
