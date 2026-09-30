"""flujo máximo con costo mínimo usando caminos más baratos sucesivos (bellman-ford)."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import inf

from algoritmos.validation import require_int

MAX_ARCS = 10_000  # tope para no dejar que una red enorme se coma la cpu


@dataclass(frozen=True)
class Arc:
    source: str
    target: str
    capacity: int
    cost: int


@dataclass(frozen=True)
class FlowResult:
    total_flow: int
    total_cost: int
    arc_flows: tuple[tuple[Arc, int], ...]  # mismo orden en que se agregaron los arcos


class FlowNetwork:
    def __init__(self) -> None:
        self._arcs: list[Arc] = []

    @property
    def arcs(self) -> tuple[Arc, ...]:
        return tuple(self._arcs)

    @property
    def nodes(self) -> frozenset[str]:
        return frozenset(n for arc in self._arcs for n in (arc.source, arc.target))

    def add_arc(self, source: str, target: str, capacity: int, cost: int) -> None:
        if len(self._arcs) >= MAX_ARCS:
            raise ValueError(f"la red no puede pasar de {MAX_ARCS} arcos")
        for node in (source, target):
            if not isinstance(node, str) or not node.strip():
                raise ValueError("los nodos deben ser texto no vacío")
        if source == target:
            raise ValueError("un arco no puede salir y llegar al mismo nodo")
        require_int(capacity, "capacity", minimum=0)
        require_int(cost, "cost", minimum=0)
        self._arcs.append(Arc(source, target, capacity, cost))


@dataclass(eq=False)
class _ResidualEdge:
    source: str
    target: str
    capacity: int
    cost: int
    reverse: _ResidualEdge | None = field(default=None, repr=False)


def min_cost_max_flow(network: FlowNetwork, source: str, sink: str) -> FlowResult:
    if source == sink:
        raise ValueError("el origen y el destino deben ser distintos")
    missing = {source, sink} - network.nodes
    if missing:
        raise ValueError(f"nodos que no están en la red: {', '.join(sorted(missing))}")

    graph, forward_edges = _build_residual(network)
    total_flow = total_cost = 0

    while (path := _cheapest_path(graph, source, sink)) is not None:
        push = min(edge.capacity for edge in path)
        for edge in path:
            edge.capacity -= push
            edge.reverse.capacity += push
        total_flow += push
        total_cost += push * sum(edge.cost for edge in path)

    # lo que quedó en el arco de regreso es justo el flujo que pasó
    arc_flows = tuple((arc, edge.reverse.capacity) for arc, edge in forward_edges)
    return FlowResult(total_flow, total_cost, arc_flows)


def _build_residual(
    network: FlowNetwork,
) -> tuple[dict[str, list[_ResidualEdge]], list[tuple[Arc, _ResidualEdge]]]:
    graph: dict[str, list[_ResidualEdge]] = {node: [] for node in network.nodes}
    forward_edges = []
    for arc in network.arcs:
        forward = _ResidualEdge(arc.source, arc.target, arc.capacity, arc.cost)
        backward = _ResidualEdge(arc.target, arc.source, 0, -arc.cost)
        forward.reverse, backward.reverse = backward, forward
        graph[arc.source].append(forward)
        graph[arc.target].append(backward)
        forward_edges.append((arc, forward))
    return graph, forward_edges


def _cheapest_path(
    graph: dict[str, list[_ResidualEdge]], source: str, sink: str
) -> list[_ResidualEdge] | None:
    # bellman-ford porque el residual tiene costos negativos
    distance = dict.fromkeys(graph, inf)
    distance[source] = 0
    arrived_by: dict[str, _ResidualEdge] = {}

    for _ in range(len(graph) - 1):
        changed = False
        for edges in graph.values():
            for edge in edges:
                if edge.capacity > 0 and distance[edge.source] + edge.cost < distance[edge.target]:
                    distance[edge.target] = distance[edge.source] + edge.cost
                    arrived_by[edge.target] = edge
                    changed = True
        if not changed:
            break

    if distance[sink] == inf:
        return None
    path = []
    node = sink
    while node != source:
        edge = arrived_by[node]
        path.append(edge)
        node = edge.source
    return path[::-1]
