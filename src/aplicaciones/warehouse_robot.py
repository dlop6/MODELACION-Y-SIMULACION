"""robot de bodega: va de su estación de carga al estante del pedido usando a*."""

from __future__ import annotations

from collections.abc import Iterator, Sequence

from algoritmos.a_star import a_star
from aplicaciones.grid import Cell, Grid, manhattan

FREE = "."
SHELF = "#"
ROBOT = "R"
PICKUP = "P"
PATH_MARK = "*"

# R = estación de carga, P = punto de recogida del pedido, # = estanterías
WAREHOUSE_LAYOUT = (
    "R....#.........",
    ".##..#.###.###.",
    ".##..#.###.###.",
    ".##....###.....",
    ".#####.###.###.",
    ".......###.#P#.",
    ".#####.....#.#.",
    "...............",
)


class WarehouseRouteProblem:
    def __init__(self, layout: Sequence[str]) -> None:
        self.grid = Grid.parse(layout, FREE + SHELF + ROBOT + PICKUP)
        self._start = _single_cell(self.grid, ROBOT, "robot")
        self._goal = _single_cell(self.grid, PICKUP, "punto de recogida")

    def start(self) -> Cell:
        return self._start

    def is_goal(self, state: Cell) -> bool:
        return state == self._goal

    def neighbors(self, state: Cell) -> Iterator[tuple[Cell, int]]:
        # cada paso cuesta 1, los estantes no se atraviesan
        for cell in self.grid.neighbors(state):
            if self.grid.at(cell) != SHELF:
                yield cell, 1

    def heuristic(self, state: Cell) -> int:
        return manhattan(state, self._goal)


def _single_cell(grid: Grid, symbol: str, name: str) -> Cell:
    cells = grid.cells_with(symbol)
    if len(cells) != 1:
        raise ValueError(f"el mapa debe tener exactamente un {name} ('{symbol}')")
    return cells[0]


def main() -> None:
    problem = WarehouseRouteProblem(WAREHOUSE_LAYOUT)
    result = a_star(problem)
    if result is None:
        print("el robot no tiene forma de llegar al pedido")
        return
    # se marcan solo las casillas intermedias para que R y P se sigan viendo
    print(problem.grid.render(result.path[1:-1], PATH_MARK))
    print(f"\npasos: {len(result.path) - 1} | costo: {result.cost}")


if __name__ == "__main__":
    main()
