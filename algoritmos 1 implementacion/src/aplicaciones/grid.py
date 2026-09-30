"""cuadrícula de texto que comparten el robot de bodega y el wifi."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass

Cell = tuple[int, int]  # (fila, columna)

MAX_CELLS = 10_000  # tope para que un mapa gigante no se coma la memoria
_STEPS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def manhattan(a: Cell, b: Cell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


@dataclass(frozen=True)
class Grid:
    rows: tuple[str, ...]

    @classmethod
    def parse(cls, rows: Sequence[str], allowed: str) -> Grid:
        if isinstance(rows, str) or not isinstance(rows, Sequence) or not rows:
            raise ValueError("el mapa debe ser una lista de filas no vacía")
        if not all(isinstance(row, str) for row in rows):
            raise ValueError("cada fila del mapa debe ser texto")
        width = len(rows[0])
        if width == 0 or any(len(row) != width for row in rows):
            raise ValueError("todas las filas deben tener el mismo largo y no estar vacías")
        if width * len(rows) > MAX_CELLS:
            raise ValueError(f"el mapa no puede pasar de {MAX_CELLS} casillas")
        invalid = set("".join(rows)) - set(allowed)
        if invalid:
            raise ValueError(f"caracteres no permitidos en el mapa: {''.join(sorted(invalid))}")
        return cls(tuple(rows))

    def at(self, cell: Cell) -> str:
        return self.rows[cell[0]][cell[1]]

    def cells_with(self, symbol: str) -> list[Cell]:
        return [
            (r, c)
            for r, row in enumerate(self.rows)
            for c, char in enumerate(row)
            if char == symbol
        ]

    def neighbors(self, cell: Cell) -> Iterator[Cell]:
        height, width = len(self.rows), len(self.rows[0])
        for dr, dc in _STEPS:
            r, c = cell[0] + dr, cell[1] + dc
            if 0 <= r < height and 0 <= c < width:
                yield (r, c)

    def render(self, cells: Iterable[Cell], symbol: str) -> str:
        canvas = [list(row) for row in self.rows]
        for r, c in cells:
            canvas[r][c] = symbol
        return "\n".join("".join(row) for row in canvas)
