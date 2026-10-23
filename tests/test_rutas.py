from itertools import islice

import networkx as nx
import pytest

from logistica.red import Red, RedInvalida
from logistica.rutas import Ruta, dijkstra, yen

OPTIMOS = {"N08": (51, 59), "N19": (18, 24), "N34": (24, 34), "N40": (47, 61)}


@pytest.fixture
def red_chica() -> Red:
    return Red(
        ("N01", "N02", "N03", "N04", "N05"),
        {
            "N01": {"N02": 1, "N03": 2, "N04": 5},
            "N02": {"N04": 1},
            "N03": {"N04": 1},
        },
    )


def _a_networkx(red: Red) -> nx.DiGraph:
    grafo = nx.DiGraph()
    grafo.add_weighted_edges_from(red.lista_arcos())
    return grafo


@pytest.mark.parametrize("destino", OPTIMOS)
def test_optimos_ida_y_regreso(red, destino):
    ida, regreso = OPTIMOS[destino]
    assert dijkstra(red, "N01", destino).tiempo == ida
    assert dijkstra(red, destino, "N01").tiempo == regreso


def test_dijkstra_coincide_con_networkx_en_todos_los_pares(red):
    distancias = dict(nx.all_pairs_dijkstra_path_length(_a_networkx(red)))
    for origen in red.nodos:
        for destino in red.nodos:
            if origen == destino:
                continue
            ruta = dijkstra(red, origen, destino)
            assert ruta.tiempo == pytest.approx(distancias[origen][destino])
            assert red.costo(ruta.nodos) == pytest.approx(ruta.tiempo)


def test_grafo_chico_a_mano(red_chica):
    rutas = yen(red_chica, "N01", "N04", 10)
    assert rutas == [
        Ruta(("N01", "N02", "N04"), 2),
        Ruta(("N01", "N03", "N04"), 3),
        Ruta(("N01", "N04"), 5),
    ]


def test_sin_camino(red_chica):
    assert dijkstra(red_chica, "N04", "N01") is None
    assert dijkstra(red_chica, "N01", "N05") is None
    assert yen(red_chica, "N04", "N01", 3) == []


def test_mismo_origen_y_destino(red_chica):
    assert dijkstra(red_chica, "N01", "N01") == Ruta(("N01",), 0)


def test_nodo_desconocido(red_chica):
    with pytest.raises(RedInvalida):
        dijkstra(red_chica, "N01", "N99")


def test_k_invalido(red_chica):
    with pytest.raises(ValueError):
        yen(red_chica, "N01", "N04", 0)


@pytest.mark.parametrize("destino", OPTIMOS)
@pytest.mark.parametrize("sentido", ["ida", "regreso"])
def test_yen_propiedades_y_networkx(red, destino, sentido):
    origen, fin = ("N01", destino) if sentido == "ida" else (destino, "N01")
    k = 6
    rutas = yen(red, origen, fin, k)
    assert len(rutas) == k
    assert rutas[0] == dijkstra(red, origen, fin)
    assert len({r.nodos for r in rutas}) == k
    tiempos = [r.tiempo for r in rutas]
    assert tiempos == sorted(tiempos)
    for ruta in rutas:
        assert len(set(ruta.nodos)) == len(ruta.nodos)
        assert ruta.nodos[0] == origen and ruta.nodos[-1] == fin
        assert red.costo(ruta.nodos) == ruta.tiempo
    referencia = islice(nx.shortest_simple_paths(_a_networkx(red), origen, fin, weight="weight"), k)
    assert tiempos == [red.costo(c) for c in referencia]
