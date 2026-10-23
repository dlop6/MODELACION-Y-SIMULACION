"""búsqueda de rutas: dijkstra para la óptima y yen para las k mejores."""

from __future__ import annotations

import heapq
from collections.abc import Set
from dataclasses import dataclass

from logistica.red import Red, RedInvalida


@dataclass(frozen=True)
class Ruta:
    nodos: tuple[str, ...]
    tiempo: float


def dijkstra(red: Red, origen: str, destino: str) -> Ruta | None:
    """ruta de menor tiempo; None si el destino no es alcanzable."""
    _exigir_nodos(red, origen, destino)
    return _dijkstra(red, origen, destino, frozenset(), frozenset())


def yen(red: Red, origen: str, destino: str, k: int) -> list[Ruta]:
    """hasta k rutas simples distintas, ordenadas por tiempo."""
    if k < 1:
        raise ValueError("k debe ser al menos 1")
    primera = dijkstra(red, origen, destino)
    if primera is None:
        return []
    rutas = [primera]
    candidatos: list[tuple[float, tuple[str, ...]]] = []
    vistas = {primera.nodos}
    while len(rutas) < k:
        previa = rutas[-1].nodos
        for i in range(len(previa) - 1):
            raiz = previa[: i + 1]
            # se cortan los tramos que ya usaron las rutas con la misma raíz
            arcos_fuera = {
                (r.nodos[i], r.nodos[i + 1])
                for r in rutas
                if len(r.nodos) > i + 1 and r.nodos[: i + 1] == raiz
            }
            desvio = _dijkstra(red, raiz[-1], destino, frozenset(raiz[:-1]), frozenset(arcos_fuera))
            if desvio is None:
                continue
            nodos = raiz[:-1] + desvio.nodos
            if nodos not in vistas:
                vistas.add(nodos)
                heapq.heappush(candidatos, (red.costo(nodos), nodos))
        if not candidatos:
            break
        tiempo, nodos = heapq.heappop(candidatos)
        rutas.append(Ruta(nodos, tiempo))
    return rutas


def _exigir_nodos(red: Red, *nodos: str) -> None:
    faltantes = [n for n in nodos if n not in red.arcos]
    if faltantes:
        raise RedInvalida(f"nodos que no están en la red: {faltantes}")


def _dijkstra(
    red: Red,
    origen: str,
    destino: str,
    nodos_fuera: Set[str],
    arcos_fuera: Set[tuple[str, str]],
) -> Ruta | None:
    distancia = {origen: 0.0}
    previo: dict[str, str] = {}
    pendientes = [(0.0, origen)]
    while pendientes:
        actual_dist, actual = heapq.heappop(pendientes)
        if actual == destino:
            break
        if actual_dist > distancia[actual]:
            continue
        for vecino, tiempo in red.arcos[actual].items():
            if vecino in nodos_fuera or (actual, vecino) in arcos_fuera:
                continue
            nueva = actual_dist + tiempo
            if nueva < distancia.get(vecino, float("inf")):
                distancia[vecino] = nueva
                previo[vecino] = actual
                heapq.heappush(pendientes, (nueva, vecino))
    if destino not in distancia:
        return None
    camino = [destino]
    while camino[-1] != origen:
        camino.append(previo[camino[-1]])
    return Ruta(tuple(reversed(camino)), distancia[destino])
