"""ubicar routers wifi en los pasillos de un piso para cubrir la mayor cantidad de oficinas."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from random import Random

from algoritmos.hill_climbing import hill_climbing
from algoritmos.validation import require_int
from aplicaciones.grid import Cell, Grid, manhattan

OFFICE = "O"
HALLWAY = "."
ROUTER_MARK = "W"

Placement = frozenset[Cell]

# piso de oficinas, los routers solo se pueden poner en pasillo
FLOOR_LAYOUT = (
    "OOOO.OOOO.OOOO",
    "OOOO.OOOO.OOOO",
    "..............",
    "OOOO.OOOO.OOOO",
    "OOOO.OOOO.OOOO",
    "..............",
    "OOOO.OOOO.OOOO",
)
ROUTERS = 3
RADIUS = 3
SEED = 7  # semilla fija para que la corrida sea reproducible


class WifiPlacementProblem:
    def __init__(self, layout: Sequence[str], radius: int) -> None:
        self.grid = Grid.parse(layout, OFFICE + HALLWAY)
        self._radius = require_int(radius, "radius", minimum=0)
        self._offices = tuple(self.grid.cells_with(OFFICE))
        self._hallways = frozenset(self.grid.cells_with(HALLWAY))

    @property
    def office_count(self) -> int:
        return len(self._offices)

    def score(self, state: Placement) -> int:
        return sum(
            1
            for office in self._offices
            if any(manhattan(office, router) <= self._radius for router in state)
        )

    def neighbors(self, state: Placement) -> Iterator[Placement]:
        # vecino = mover un router una casilla a un pasillo libre; se ordena para ser determinista
        for router in sorted(state):
            for cell in self.grid.neighbors(router):
                if cell in self._hallways and cell not in state:
                    yield (state - {router}) | {cell}

    def random_placement(self, routers: int, rng: Random) -> Placement:
        require_int(routers, "routers", minimum=1)
        if routers > len(self._hallways):
            raise ValueError("hay más routers que casillas de pasillo")
        return frozenset(rng.sample(sorted(self._hallways), routers))


def main() -> None:
    problem = WifiPlacementProblem(FLOOR_LAYOUT, RADIUS)
    initial = problem.random_placement(ROUTERS, Random(SEED))
    result = hill_climbing(problem, initial)

    total = problem.office_count
    print(f"inicial: {problem.score(initial)}/{total} oficinas cubiertas")
    print(problem.grid.render(initial, ROUTER_MARK))
    print(f"\nfinal: {result.score}/{total} oficinas cubiertas en {result.iterations} movimientos")
    print(problem.grid.render(result.state, ROUTER_MARK))


if __name__ == "__main__":
    main()
