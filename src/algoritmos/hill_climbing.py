"""hill-climbing de subida más empinada (steepest ascent), maximiza el score."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from algoritmos.validation import require_int

S = TypeVar("S")


class LocalSearchProblem(Protocol[S]):
    def neighbors(self, state: S) -> Iterable[S]: ...

    def score(self, state: S) -> float: ...


@dataclass(frozen=True)
class ClimbResult(Generic[S]):
    state: S
    score: float
    iterations: int  # cuántas veces se movió a un vecino mejor


def hill_climbing(
    problem: LocalSearchProblem[S], initial: S, max_iterations: int = 1_000
) -> ClimbResult[S]:
    require_int(max_iterations, "max_iterations", minimum=1)
    current, current_score = initial, problem.score(initial)

    for iteration in range(max_iterations):
        best, best_score = None, current_score
        for neighbor in problem.neighbors(current):
            score = problem.score(neighbor)
            if score > best_score:
                best, best_score = neighbor, score
        if best is None:
            # ningún vecino mejora, llegamos a un máximo (local o global)
            return ClimbResult(current, current_score, iteration)
        current, current_score = best, best_score

    return ClimbResult(current, current_score, max_iterations)
