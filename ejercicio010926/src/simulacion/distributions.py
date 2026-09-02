"""Distribuciones admitidas por los simuladores.

El módulo centraliza la creación y validación para evitar que cada modelo
interprete la configuración de una manera distinta.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Any, Protocol


class Distribution(Protocol):
    def sample(self, rng: Random) -> float:
        """Devuelve una observación."""


@dataclass(frozen=True)
class Constant:
    value: float

    def sample(self, rng: Random) -> float:
        del rng
        return self.value


@dataclass(frozen=True)
class Uniform:
    minimum: float
    maximum: float

    def sample(self, rng: Random) -> float:
        return rng.uniform(self.minimum, self.maximum)


@dataclass(frozen=True)
class DiscreteUniform:
    minimum: int
    maximum: int

    def sample(self, rng: Random) -> float:
        return float(rng.randint(self.minimum, self.maximum))


@dataclass(frozen=True)
class Exponential:
    mean: float

    def sample(self, rng: Random) -> float:
        return rng.expovariate(1.0 / self.mean)


@dataclass(frozen=True)
class Triangular:
    minimum: float
    mode: float
    maximum: float

    def sample(self, rng: Random) -> float:
        return rng.triangular(self.minimum, self.maximum, self.mode)


def _number(data: dict[str, Any], key: str) -> float:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"'{key}' debe ser numérico")
    return float(value)


def _integer(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"'{key}' debe ser un entero")
    return value


def distribution_from_dict(
    data: Any,
    field_name: str,
    *,
    require_positive: bool = False,
    require_integer: bool = False,
) -> Distribution:
    if not isinstance(data, dict):
        raise ValueError(f"'{field_name}' debe ser un objeto de distribución")
    kind = data.get("type")

    if kind == "constant":
        distribution: Distribution = Constant(_number(data, "value"))
    elif kind == "uniform":
        minimum, maximum = _number(data, "min"), _number(data, "max")
        if minimum > maximum:
            raise ValueError(f"'{field_name}': min no puede superar max")
        distribution = Uniform(minimum, maximum)
    elif kind == "discrete_uniform":
        minimum, maximum = _integer(data, "min"), _integer(data, "max")
        if minimum > maximum:
            raise ValueError(f"'{field_name}': min no puede superar max")
        distribution = DiscreteUniform(minimum, maximum)
    elif kind == "exponential":
        mean = _number(data, "mean")
        if mean <= 0:
            raise ValueError(f"'{field_name}': mean debe ser mayor que cero")
        distribution = Exponential(mean)
    elif kind == "triangular":
        minimum = _number(data, "min")
        mode = _number(data, "mode")
        maximum = _number(data, "max")
        if not minimum <= mode <= maximum:
            raise ValueError(f"'{field_name}': se requiere min <= mode <= max")
        distribution = Triangular(minimum, mode, maximum)
    else:
        allowed = "constant, uniform, discrete_uniform, exponential, triangular"
        raise ValueError(f"'{field_name}': tipo desconocido {kind!r}; use {allowed}")

    if require_positive:
        lower_bound = {
            Constant: distribution.value if isinstance(distribution, Constant) else None,
            Uniform: distribution.minimum if isinstance(distribution, Uniform) else None,
            DiscreteUniform: (
                float(distribution.minimum) if isinstance(distribution, DiscreteUniform) else None
            ),
            Exponential: 1.0,
            Triangular: distribution.minimum if isinstance(distribution, Triangular) else None,
        }[type(distribution)]
        if lower_bound is not None and lower_bound <= 0:
            raise ValueError(f"'{field_name}' debe producir solamente valores > 0")
    if require_integer:
        is_integer_distribution = isinstance(distribution, DiscreteUniform) or (
            isinstance(distribution, Constant) and distribution.value.is_integer()
        )
        if not is_integer_distribution:
            raise ValueError(f"'{field_name}' debe producir solamente enteros")
    return distribution


def positive_sample(distribution: Distribution, rng: Random, field_name: str) -> float:
    value = distribution.sample(rng)
    if value <= 0:
        raise ValueError(f"'{field_name}' produjo {value}; debe producir valores > 0")
    return value


def positive_integer_sample(
    distribution: Distribution, rng: Random, field_name: str
) -> int:
    value = positive_sample(distribution, rng, field_name)
    if not value.is_integer():
        raise ValueError(f"'{field_name}' produjo {value}; debe producir enteros")
    return int(value)
