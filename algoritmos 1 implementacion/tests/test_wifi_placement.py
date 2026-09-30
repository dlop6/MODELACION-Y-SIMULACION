from random import Random

import pytest

from algoritmos.hill_climbing import hill_climbing
from aplicaciones.wifi_placement import FLOOR_LAYOUT, WifiPlacementProblem, main

SMALL_FLOOR = (
    "OO.OO",
    ".....",
    "OO.OO",
)


@pytest.mark.parametrize(
    "routers, radius, expected",
    [
        ({(1, 2)}, 1, 0),  # en el centro no toca ninguna oficina
        ({(1, 0)}, 1, 2),  # (0,0) y (2,0)
        ({(1, 1)}, 2, 4),  # (0,0), (0,1), (2,0), (2,1)
        ({(1, 1), (1, 3)}, 2, 8),  # cubre todo
    ],
)
def test_score_matches_hand_calculation(routers, radius, expected):
    problem = WifiPlacementProblem(SMALL_FLOOR, radius)

    assert problem.score(frozenset(routers)) == expected


def test_neighbors_only_move_to_free_hallways():
    problem = WifiPlacementProblem(SMALL_FLOOR, radius=1)
    state = frozenset({(1, 0), (1, 1)})

    neighbors = list(problem.neighbors(state))

    # (1,0) solo puede ir a oficinas o a (1,1) ocupado; (1,1) puede ir a (1,2)
    assert neighbors == [frozenset({(1, 0), (1, 2)})]


def test_climb_never_ends_worse_than_start():
    problem = WifiPlacementProblem(FLOOR_LAYOUT, radius=3)
    initial = problem.random_placement(3, Random(1))

    result = hill_climbing(problem, initial)

    assert result.score >= problem.score(initial)
    assert len(result.state) == 3


def test_same_seed_gives_same_result():
    problem = WifiPlacementProblem(FLOOR_LAYOUT, radius=3)

    first = hill_climbing(problem, problem.random_placement(3, Random(42)))
    second = hill_climbing(problem, problem.random_placement(3, Random(42)))

    assert first == second


def test_rejects_negative_radius():
    with pytest.raises(ValueError, match="radius"):
        WifiPlacementProblem(SMALL_FLOOR, radius=-1)


def test_rejects_more_routers_than_hallways():
    problem = WifiPlacementProblem(SMALL_FLOOR, radius=1)

    with pytest.raises(ValueError, match="pasillo"):
        problem.random_placement(8, Random(0))


def test_rejects_invalid_floor_symbols():
    with pytest.raises(ValueError, match="no permitidos"):
        WifiPlacementProblem(("O#.",), radius=1)


def test_main_prints_coverage(capsys):
    main()

    output = capsys.readouterr().out
    assert "inicial:" in output
    assert "final:" in output
    assert "W" in output
