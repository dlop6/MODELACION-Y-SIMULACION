import pytest

from algoritmos.hill_climbing import hill_climbing


class LineProblem:
    """enteros de 0 a len(values)-1, cada uno con su valor; vecinos = x-1 y x+1."""

    def __init__(self, values):
        self._values = values

    def neighbors(self, state):
        return [x for x in (state - 1, state + 1) if 0 <= x < len(self._values)]

    def score(self, state):
        return self._values[state]


PARABOLA = [-((x - 7) ** 2) for x in range(11)]  # máximo global en x=7
TWO_PEAKS = [0, 1, 2, 1, 0, 1, 5, 3]  # local en x=2, global en x=6


def test_climbs_to_global_maximum():
    result = hill_climbing(LineProblem(PARABOLA), initial=0)

    assert result.state == 7
    assert result.score == 0
    assert result.iterations == 7


def test_gets_stuck_on_local_maximum():
    # es la limitación clásica del método
    result = hill_climbing(LineProblem(TWO_PEAKS), initial=0)

    assert result.state == 2
    assert result.score == 2


def test_other_start_reaches_global_peak():
    result = hill_climbing(LineProblem(TWO_PEAKS), initial=5)

    assert result.state == 6


def test_stops_at_max_iterations():
    result = hill_climbing(LineProblem(PARABOLA), initial=0, max_iterations=3)

    assert result.state == 3
    assert result.iterations == 3


def test_rejects_invalid_max_iterations():
    with pytest.raises(ValueError, match="max_iterations"):
        hill_climbing(LineProblem(PARABOLA), initial=0, max_iterations=0)
