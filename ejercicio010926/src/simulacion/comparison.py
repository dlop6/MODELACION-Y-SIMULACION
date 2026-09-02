"""Comparación numérica entre simulación y observaciones reales."""

from __future__ import annotations

from typing import Any


def compare_metrics(
    simulated: dict[str, Any], actual: dict[str, Any]
) -> dict[str, dict[str, float | None]]:
    if not isinstance(actual, dict):
        raise ValueError("los valores reales de cada modelo deben ser un objeto")
    comparison: dict[str, dict[str, float | None]] = {}
    for metric, actual_value in actual.items():
        if metric not in simulated:
            raise ValueError(f"la métrica real {metric!r} no existe en la simulación")
        simulated_value = simulated[metric]
        if isinstance(actual_value, bool) or not isinstance(actual_value, (int, float)):
            raise ValueError(f"el valor real de {metric!r} debe ser numérico")
        if isinstance(simulated_value, bool) or not isinstance(simulated_value, (int, float)):
            raise ValueError(f"la métrica simulada {metric!r} no es numérica")
        absolute_error = abs(float(simulated_value) - float(actual_value))
        relative_error = None if actual_value == 0 else absolute_error / abs(float(actual_value))
        comparison[metric] = {
            "simulated": float(simulated_value),
            "actual": float(actual_value),
            "absolute_error": absolute_error,
            "relative_error": relative_error,
        }
    return comparison

