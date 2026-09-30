from collections import defaultdict

import pytest

from algoritmos.min_cost_flow import FlowNetwork, min_cost_max_flow


def build(*arcs):
    network = FlowNetwork()
    for arc in arcs:
        network.add_arc(*arc)
    return network


def flows_by_pair(result):
    return {(arc.source, arc.target): flow for arc, flow in result.arc_flows}


def test_picks_cheaper_branch_when_flow_is_limited():
    # solo entran 5 unidades, y por A cuesta 2 c/u vs 10 por B
    network = build(
        ("S", "X", 5, 0),
        ("X", "A", 5, 1), ("A", "T", 5, 1),
        ("X", "B", 5, 5), ("B", "T", 5, 5),
    )

    result = min_cost_max_flow(network, "S", "T")

    assert result.total_flow == 5
    assert result.total_cost == 10
    assert flows_by_pair(result)[("X", "B")] == 0


def test_undoes_flow_through_residual_arcs():
    # el primer camino barato S-A-B-T hay que deshacerlo para meter 2 unidades
    network = build(
        ("S", "A", 1, 1), ("A", "B", 1, 1), ("B", "T", 1, 1),
        ("S", "B", 1, 5), ("A", "T", 1, 5),
    )

    result = min_cost_max_flow(network, "S", "T")

    assert result.total_flow == 2
    assert result.total_cost == 12
    assert flows_by_pair(result)[("A", "B")] == 0


def test_no_path_means_zero_flow():
    network = build(("S", "A", 3, 1), ("T", "B", 3, 1))

    result = min_cost_max_flow(network, "S", "T")

    assert result.total_flow == 0
    assert result.total_cost == 0


def test_respects_capacity_and_conservation():
    network = build(
        ("S", "A", 4, 2), ("S", "B", 2, 1), ("A", "B", 3, 1),
        ("A", "T", 2, 3), ("B", "T", 5, 1),
    )

    result = min_cost_max_flow(network, "S", "T")

    balance = defaultdict(int)
    for arc, flow in result.arc_flows:
        assert 0 <= flow <= arc.capacity
        balance[arc.source] -= flow
        balance[arc.target] += flow
    assert balance["A"] == balance["B"] == 0
    assert balance["T"] == -balance["S"] == result.total_flow == 6


@pytest.mark.parametrize(
    "arc, message",
    [
        (("A", "B", -1, 1), "capacity"),
        (("A", "B", 1, -1), "cost"),
        (("A", "B", True, 1), "capacity"),
        (("", "B", 1, 1), "no vacío"),
        (("A", "A", 1, 1), "mismo nodo"),
    ],
)
def test_rejects_invalid_arcs(arc, message):
    with pytest.raises(ValueError, match=message):
        FlowNetwork().add_arc(*arc)


def test_rejects_same_source_and_sink():
    with pytest.raises(ValueError, match="distintos"):
        min_cost_max_flow(build(("S", "T", 1, 1)), "S", "S")


def test_rejects_unknown_node():
    with pytest.raises(ValueError, match="Z"):
        min_cost_max_flow(build(("S", "T", 1, 1)), "S", "Z")
