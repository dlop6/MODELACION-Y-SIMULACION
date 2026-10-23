from collections import Counter
from statistics import fmean

import pytest

from logistica.pedidos import generar_pedidos
from logistica.politicas import DESTINOS


def test_misma_semilla_misma_lista():
    assert generar_pedidos(4, 8, DESTINOS, 7) == generar_pedidos(4, 8, DESTINOS, 7)
    assert generar_pedidos(4, 8, DESTINOS, 7) != generar_pedidos(4, 8, DESTINOS, 8)


def test_llegadas_crecientes_dentro_de_la_recepcion():
    pedidos = generar_pedidos(10, 8, DESTINOS, 3)
    llegadas = [p.llegada for p in pedidos]
    assert llegadas == sorted(llegadas)
    assert all(0 < t < 480 for t in llegadas)
    assert [p.id for p in pedidos] == list(range(len(pedidos)))


def test_media_y_proporcion_por_destino():
    corridas = [generar_pedidos(4, 8, DESTINOS, s) for s in range(1000)]
    assert fmean(len(c) for c in corridas) == pytest.approx(32, rel=0.05)
    conteo = Counter(p.destino for c in corridas for p in c)
    total = sum(conteo.values())
    for destino in DESTINOS:
        assert conteo[destino] / total == pytest.approx(0.25, abs=0.03)


@pytest.mark.parametrize(
    "tasa, duracion, destinos, semilla",
    [
        (0, 8, DESTINOS, 1),
        (61, 8, DESTINOS, 1),
        (4, 0.4, DESTINOS, 1),
        (4, 25, DESTINOS, 1),
        (4, 8, (), 1),
        (4, 8, DESTINOS, -1),
        (4, 8, DESTINOS, 1.5),
        (4, 8, DESTINOS, True),
    ],
)
def test_parametros_invalidos(tasa, duracion, destinos, semilla):
    with pytest.raises(ValueError):
        generar_pedidos(tasa, duracion, destinos, semilla)
