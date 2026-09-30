import pytest

from algoritmos.validation import require_int


def test_accepts_int_at_minimum():
    assert require_int(3, "x", minimum=3) == 3


@pytest.mark.parametrize("value", [True, 2.5, "4", None])
def test_rejects_non_int(value):
    with pytest.raises(ValueError, match="entero"):
        require_int(value, "x", minimum=0)


def test_rejects_below_minimum():
    with pytest.raises(ValueError, match="mayor o igual a 1"):
        require_int(0, "x", minimum=1)
