import pytest

from simulacion.repairs import RepairConfig, RepairSystemSimulator


def deterministic_config(**overrides):
    data = {
        "horizon": 7,
        "working_machines": 2,
        "available_spares": 1,
        "machine_lifetime": {"type": "constant", "value": 3},
        "repair_time": {"type": "constant", "value": 2},
    }
    data.update(overrides)
    return RepairConfig.from_dict(data)


def test_one_mechanic_and_cold_spare_accounting():
    result = RepairSystemSimulator(deterministic_config()).run(seed=10)

    assert result["failures"] == 3
    assert result["repairs_completed"] == 2
    assert result["replacements"] == 1
    assert result["ending_working_machines"] == 2
    assert result["ending_available_spares"] == 0
    assert result["ending_broken_machines"] == 1
    assert result["mechanic_busy_at_end"] == 1
    assert result["time_to_first_total_stoppage"] is None
    assert 0 <= result["machine_availability"] <= 1
    assert 0 <= result["mechanic_utilization"] <= 1


def test_rejects_zero_working_machines():
    with pytest.raises(ValueError, match="working_machines"):
        deterministic_config(working_machines=0)
