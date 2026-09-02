import pytest

from simulacion.inventory import InventoryConfig, InventorySimulator


def deterministic_config(**overrides):
    data = {
        "horizon": 5,
        "initial_units": 4,
        "product_limit": 10,
        "shortage_threshold": 1,
        "reorder_point": 1,
        "order_quantity": 5,
        "max_open_orders": 1,
        "shortage_policy": "lost_sales",
        "demand_interarrival": {"type": "constant", "value": 1},
        "demand_size": {"type": "constant", "value": 1},
        "order_lead_time": {"type": "constant", "value": 2},
        "unit_order_cost": 2,
        "fixed_order_cost": 1,
        "holding_cost_per_unit_time": 1,
        "sale_price": 5,
    }
    data.update(overrides)
    return InventoryConfig.from_dict(data)


def test_deterministic_inventory_accounting():
    result = InventorySimulator(deterministic_config()).run(seed=7)

    assert result["ending_units_now"] == 4
    assert result["ending_units_ordered"] == 0
    assert result["units_demanded"] == 5
    assert result["units_sold"] == 5
    assert result["shortage_notifications"] == 1
    assert result["C_ordering_cost"] == 11
    assert result["H_holding_cost"] == 10
    assert result["R_sales_revenue"] == 25
    assert result["net_result"] == 4


def test_rejects_initial_inventory_above_limit():
    with pytest.raises(ValueError, match="initial_units"):
        deterministic_config(initial_units=11)


def test_demand_quantity_must_be_integer():
    with pytest.raises(ValueError, match="debe producir solamente enteros"):
        deterministic_config(demand_size={"type": "constant", "value": 1.5})
