"""validaciones chiquitas que se repiten en varios módulos."""

from __future__ import annotations


def require_int(value: object, name: str, minimum: int) -> int:
    # bool hereda de int, así que hay que sacarlo aparte
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} debe ser un entero")
    if value < minimum:
        raise ValueError(f"{name} debe ser mayor o igual a {minimum}")
    return value
