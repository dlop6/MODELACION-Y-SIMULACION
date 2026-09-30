"""a* genérico: sirve para cualquier problema que cumpla SearchProblem."""

from __future__ import annotations

import heapq
from collections.abc import Hashable, Iterable
from dataclasses import dataclass
from itertools import count
from math import inf
from typing import Generic, Protocol, TypeVar

S = TypeVar("S", bound=Hashable)


class SearchProblem(Protocol[S]):
    def start(self) -> S: ...

    def is_goal(self, state: S) -> bool: ...

    def neighbors(self, state: S) -> Iterable[tuple[S, float]]: ...

    def heuristic(self, state: S) -> float: ...


@dataclass(frozen=True)
class SearchResult(Generic[S]):
    path: tuple[S, ...]
    cost: float


def a_star(problem: SearchProblem[S]) -> SearchResult[S] | None:
    start = problem.start()
    tie = count()  # desempate para que heapq nunca compare estados
    frontier = [(problem.heuristic(start), next(tie), 0, start)]
    best_cost: dict[S, float] = {start: 0}
    parent: dict[S, S] = {}

    while frontier:
        _, _, cost, state = heapq.heappop(frontier)
        if cost > best_cost[state]:
            continue  # entrada vieja, ya hubo un camino más barato
        if problem.is_goal(state):
            return SearchResult(_rebuild_path(parent, state), cost)
        for neighbor, step in problem.neighbors(state):
            if step < 0:
                raise ValueError("a* no acepta costos negativos")
            new_cost = cost + step
            if new_cost < best_cost.get(neighbor, inf):
                best_cost[neighbor] = new_cost
                parent[neighbor] = state
                priority = new_cost + problem.heuristic(neighbor)
                heapq.heappush(frontier, (priority, next(tie), new_cost, neighbor))
    return None


def _rebuild_path(parent: dict[S, S], goal: S) -> tuple[S, ...]:
    path = [goal]
    while path[-1] in parent:
        path.append(parent[path[-1]])
    return tuple(reversed(path))
