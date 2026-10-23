"""conversión de tablas a csv, compartida por la cli y la app."""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence

_PELIGROSOS = ("=", "+", "-", "@", "\t", "\r")


def celda_segura(valor):
    # evita que excel interprete texto como fórmula (csv injection)
    if isinstance(valor, str) and valor.startswith(_PELIGROSOS):
        return "'" + valor
    return valor


def filas_a_csv(filas: Sequence[dict]) -> str:
    if not filas:
        return ""
    texto = io.StringIO()
    escritor = csv.DictWriter(texto, fieldnames=list(filas[0]), lineterminator="\n")
    escritor.writeheader()
    escritor.writerows({k: celda_segura(v) for k, v in fila.items()} for fila in filas)
    return texto.getvalue()
