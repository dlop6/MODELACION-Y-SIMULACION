import pytest

from simulacion.bank import BankConfig, BankSimulator


def deterministic_config(**overrides):
    data = {
        "horizon": 5,
        "tellers": 1,
        "customer_interarrival": {"type": "constant", "value": 1},
        "service_time": {"type": "constant", "value": 2},
    }
    data.update(overrides)
    return BankConfig.from_dict(data)


def test_fifo_bank_and_little_law():
    result = BankSimulator(deterministic_config()).run(seed=1)

    assert result["arrivals"] == 5
    assert result["customers_served"] == 2
    assert result["customers_in_queue_at_end"] == 2
    assert result["customers_in_system_at_end"] == 3
    assert result["average_customers_in_queue"] == pytest.approx(0.8)
    assert result["average_customers_in_system"] == pytest.approx(1.6)
    assert result["teller_utilization"] == pytest.approx(0.8)
    assert result["little_system_absolute_error"] == pytest.approx(0.0)
    assert result["little_queue_absolute_error"] == pytest.approx(0.0)


def test_rejects_zero_tellers():
    with pytest.raises(ValueError, match="tellers"):
        deterministic_config(tellers=0)
