import pytest

from algoritmos.a_star import a_star
from aplicaciones.grid import manhattan
from aplicaciones.warehouse_robot import SHELF, WarehouseRouteProblem, main

# a mano: hay que pasar sí o sí por (2,3) y (0,5) -> 5 + 4 + 3 = 12 pasos
SMALL_LAYOUT = (
    "R..#...",
    ".#.#.#.",
    ".#...#P",
)


def test_shortest_route_matches_hand_calculation():
    problem = WarehouseRouteProblem(SMALL_LAYOUT)

    result = a_star(problem)

    assert result.cost == 12
    assert result.path[0] == (0, 0)
    assert result.path[-1] == (2, 6)


def test_route_is_valid_step_by_step():
    problem = WarehouseRouteProblem(SMALL_LAYOUT)

    result = a_star(problem)

    assert all(manhattan(a, b) == 1 for a, b in zip(result.path, result.path[1:]))
    assert all(problem.grid.at(cell) != SHELF for cell in result.path)


def test_blocked_robot_has_no_route():
    problem = WarehouseRouteProblem(("R#.", "##.", "..P"))

    assert a_star(problem) is None


@pytest.mark.parametrize(
    "layout, name",
    [
        (("...", "..P"), "robot"),
        (("R.R", "..P"), "robot"),
        (("R..", "..."), "punto de recogida"),
    ],
)
def test_requires_exactly_one_robot_and_pickup(layout, name):
    with pytest.raises(ValueError, match=name):
        WarehouseRouteProblem(layout)


def test_main_prints_route(capsys):
    main()

    output = capsys.readouterr().out
    assert "*" in output
    assert "pasos:" in output
