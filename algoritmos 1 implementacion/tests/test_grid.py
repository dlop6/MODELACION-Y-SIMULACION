import pytest

from aplicaciones.grid import MAX_CELLS, Grid, manhattan


def test_manhattan():
    assert manhattan((0, 0), (2, 3)) == 5


def test_cells_with_and_at():
    grid = Grid.parse(["a.", ".a"], "a.")

    assert grid.cells_with("a") == [(0, 0), (1, 1)]
    assert grid.at((1, 0)) == "."


def test_neighbors_stay_inside():
    grid = Grid.parse(["...", "..."], ".")

    assert sorted(grid.neighbors((0, 0))) == [(0, 1), (1, 0)]
    assert sorted(grid.neighbors((1, 1))) == [(0, 1), (1, 0), (1, 2)]


def test_render_marks_cells_without_touching_original():
    grid = Grid.parse(["...", "..."], ".")

    assert grid.render([(0, 1), (1, 2)], "*") == ".*.\n..*"
    assert grid.rows == ("...", "...")


@pytest.mark.parametrize(
    "rows, message",
    [
        ([], "no vacía"),
        ("...", "no vacía"),
        (None, "no vacía"),
        ([".", 3], "texto"),
        ([".", ".."], "mismo largo"),
        ([""], "mismo largo"),
        (["x"], "no permitidos"),
    ],
)
def test_rejects_invalid_maps(rows, message):
    with pytest.raises(ValueError, match=message):
        Grid.parse(rows, ".")


def test_rejects_huge_map():
    with pytest.raises(ValueError, match="casillas"):
        Grid.parse(["." * (MAX_CELLS + 1)], ".")
