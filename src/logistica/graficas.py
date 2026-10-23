"""figuras de matplotlib compartidas por la cli y la app."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import networkx as nx
from matplotlib.figure import Figure

from logistica.metricas import ETIQUETAS
from logistica.politicas import BODEGA, DESTINOS
from logistica.red import Red

_COLUMNAS_GRILLA = 8
_CURVA = "arc3,rad=0.12"
_COLOR_DOBLE = "#9aa0a6"
_COLOR_UN_SENTIDO = "#e37400"
_COLORES_RUTA = ("#1a73e8", "#d93025", "#188038", "#9334e6")
_COLORES_POLITICA = {"actual": "#9aa0a6", "algoritmo": "#1a73e8"}


def posiciones(red: Red) -> dict[str, tuple[float, float]]:
    """grilla de 8 columnas según el número del nodo; es solo visual, la matriz no trae coordenadas."""
    pos = {}
    for nodo in red.nodos:
        indice = int(nodo[1:]) - 1
        pos[nodo] = (indice % _COLUMNAS_GRILLA, -(indice // _COLUMNAS_GRILLA))
    return pos


def fig_red(red: Red, resaltar: Mapping[str, Sequence[str]] | None = None, titulo: str = "") -> Figure:
    """dibuja la red dirigida; resaltar = {etiqueta: nodos de la ruta}."""
    grafo = nx.DiGraph()
    grafo.add_nodes_from(red.nodos)
    grafo.add_weighted_edges_from(red.lista_arcos())
    pos = posiciones(red)
    figura = Figure(figsize=(16, 10), layout="constrained")
    ax = figura.add_subplot()

    un_sentido = [(o, d) for o, d in grafo.edges if not grafo.has_edge(d, o)]
    doble = [(o, d) for o, d in grafo.edges if grafo.has_edge(d, o)]
    for arcos, color, etiqueta in ((doble, _COLOR_DOBLE, "doble sentido"), (un_sentido, _COLOR_UN_SENTIDO, "un solo sentido")):
        coleccion = nx.draw_networkx_edges(
            grafo, pos, edgelist=arcos, ax=ax, edge_color=color, arrowsize=12,
            connectionstyle=_CURVA, node_size=600, width=1.2,
        )
        if coleccion:
            coleccion[0].set_label(etiqueta)

    for i, (etiqueta, nodos) in enumerate((resaltar or {}).items()):
        tramos = list(zip(nodos, nodos[1:]))
        coleccion = nx.draw_networkx_edges(
            grafo, pos, edgelist=tramos, ax=ax, edge_color=_COLORES_RUTA[i % len(_COLORES_RUTA)],
            arrowsize=16, connectionstyle=_CURVA, node_size=600, width=3.5,
        )
        if coleccion:
            coleccion[0].set_label(etiqueta)

    colores_nodo = [
        "#fbbc04" if n == BODEGA else "#34a853" if n in DESTINOS else "#e8eaed" for n in red.nodos
    ]
    nx.draw_networkx_nodes(grafo, pos, ax=ax, node_color=colores_nodo, node_size=600, edgecolors="#3c4043")
    nx.draw_networkx_labels(grafo, pos, ax=ax, font_size=8)
    nx.draw_networkx_edge_labels(
        grafo, pos, ax=ax, edge_labels={(o, d): f"{t:g}" for o, d, t in red.lista_arcos()},
        connectionstyle=_CURVA, font_size=6, label_pos=0.3, bbox={"alpha": 0},
    )
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1), fontsize=9)
    ax.set_title(titulo or "red de logística del valle (minutos por tramo)")
    ax.set_axis_off()
    return figura


def fig_metricas(resumen: Sequence[dict], indicador: str) -> Figure:
    """barras por escenario y política con su ic95."""
    escenarios = list(dict.fromkeys(f["escenario"] for f in resumen))
    politicas = list(dict.fromkeys(f["politica"] for f in resumen))
    figura = Figure(figsize=(8, 4.5), layout="constrained")
    ax = figura.add_subplot()
    ancho = 0.8 / max(len(politicas), 1)
    for i, politica in enumerate(politicas):
        filas = {f["escenario"]: f for f in resumen if f["politica"] == politica}
        xs = [j + i * ancho for j in range(len(escenarios))]
        ax.bar(
            xs,
            [filas[e][f"{indicador}_media"] for e in escenarios],
            ancho,
            yerr=[filas[e][f"{indicador}_ic95"] for e in escenarios],
            capsize=4,
            label=politica,
            color=_COLORES_POLITICA.get(politica),
        )
    ax.set_xticks([j + ancho * (len(politicas) - 1) / 2 for j in range(len(escenarios))], escenarios)
    ax.set_ylabel(ETIQUETAS[indicador])
    ax.set_title(f"{ETIQUETAS[indicador]} por escenario (media ± ic95)")
    ax.legend()
    return figura


def fig_barrido(resumen: Sequence[dict], indicador: str) -> Figure:
    """indicador contra el tamaño de la flota, un panel por escenario."""
    escenarios = list(dict.fromkeys(f["escenario"] for f in resumen))
    figura = Figure(figsize=(5 * len(escenarios), 4), layout="constrained")
    ejes = figura.subplots(1, len(escenarios), squeeze=False)[0]
    for ax, escenario in zip(ejes, escenarios):
        for politica in dict.fromkeys(f["politica"] for f in resumen):
            filas = sorted(
                (f for f in resumen if f["escenario"] == escenario and f["politica"] == politica),
                key=lambda f: f["vehiculos"],
            )
            xs = [f["vehiculos"] for f in filas]
            medias = [f[f"{indicador}_media"] for f in filas]
            ic = [f[f"{indicador}_ic95"] for f in filas]
            color = _COLORES_POLITICA.get(politica)
            ax.plot(xs, medias, marker="o", label=politica, color=color)
            ax.fill_between(xs, [m - c for m, c in zip(medias, ic)], [m + c for m, c in zip(medias, ic)], alpha=0.2, color=color)
        ax.set_title(escenario)
        ax.set_xlabel("vehículos")
        ax.set_ylabel(ETIQUETAS[indicador])
        ax.legend()
    return figura
