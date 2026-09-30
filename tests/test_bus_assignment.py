import pytest

from aplicaciones.bus_assignment import (
    DESTINATION,
    ORIGIN,
    ROUTES,
    BusRoute,
    main,
    plan_passengers,
)


def passengers_on(result, source, target):
    return next(
        flow for arc, flow in result.arc_flows if (arc.source, arc.target) == (source, target)
    )


def test_matches_hand_calculation():
    # altiplano: el cuello es los encuentros -> cuatro caminos (240)
    #   200 directo a xela (34 c/u) + 40 por totonicapán (38 c/u) = 8320
    # costa: el cuello es mazatenango -> xela (135) a 36 c/u = 4860
    result = plan_passengers(ROUTES, ORIGIN, DESTINATION)

    assert result.total_flow == 375
    assert result.total_cost == 8320 + 4860
    assert passengers_on(result, "Cuatro Caminos", DESTINATION) == 200
    assert passengers_on(result, "Totonicapán", DESTINATION) == 40
    assert passengers_on(result, "Mazatenango", DESTINATION) == 135


def test_capacity_is_buses_times_seats():
    assert BusRoute("A", "B", 3, 45, 10).capacity == 135


@pytest.mark.parametrize("buses, seats", [(0, 40), (3, 0)])
def test_rejects_empty_routes(buses, seats):
    with pytest.raises(ValueError, match="debe ser mayor o igual a 1"):
        BusRoute("A", "B", buses, seats, 10)


def test_rejects_negative_fuel_cost():
    with pytest.raises(ValueError, match="cost"):
        plan_passengers([BusRoute("A", "B", 1, 40, -5)], "A", "B")


def test_main_prints_plan(capsys):
    main()

    output = capsys.readouterr().out
    assert "375" in output
    assert "Q13180" in output
