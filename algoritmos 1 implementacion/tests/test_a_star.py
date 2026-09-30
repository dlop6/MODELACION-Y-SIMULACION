import pytest

from algoritmos.a_star import a_star


class GraphProblem:
    """grafo a mano para probar a* sin depender de ninguna app."""

    def __init__(self, edges, heuristic, start="S", goal="G"):
        self._edges = edges
        self._heuristic = heuristic
        self._start = start
        self._goal = goal

    def start(self):
        return self._start

    def is_goal(self, state):
        return state == self._goal

    def neighbors(self, state):
        return self._edges.get(state, [])

    def heuristic(self, state):
        return self._heuristic[state]


def test_finds_optimal_path_even_if_first_step_looks_better():
    # A parece más cerca de G, pero pasar por B sale más barato
    edges = {"S": [("A", 1), ("B", 4), ("G", 20)], "A": [("G", 10)], "B": [("G", 1)]}
    heuristic = {"S": 5, "A": 1, "B": 1, "G": 0}

    result = a_star(GraphProblem(edges, heuristic))

    assert result.path == ("S", "B", "G")
    assert result.cost == 5


def test_returns_none_when_goal_is_unreachable():
    edges = {"S": [("A", 1)]}
    heuristic = {"S": 0, "A": 0, "G": 0}

    assert a_star(GraphProblem(edges, heuristic)) is None


def test_start_equal_goal_costs_nothing():
    result = a_star(GraphProblem({}, {"S": 0}, goal="S"))

    assert result.path == ("S",)
    assert result.cost == 0


def test_rejects_negative_costs():
    edges = {"S": [("G", -1)]}
    heuristic = {"S": 0, "G": 0}

    with pytest.raises(ValueError, match="negativos"):
        a_star(GraphProblem(edges, heuristic))
