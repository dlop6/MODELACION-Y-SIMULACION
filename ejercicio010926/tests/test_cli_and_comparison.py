import pytest

from simulacion.comparison import compare_metrics
from simulacion.cli import run


def test_comparison_calculates_both_errors():
    result = compare_metrics({"availability": 8.0}, {"availability": 10.0})

    assert result["availability"]["absolute_error"] == 2.0
    assert result["availability"]["relative_error"] == pytest.approx(0.2)


def test_comparison_rejects_unknown_metric():
    with pytest.raises(ValueError, match="no existe"):
        compare_metrics({}, {"invented": 1})


def test_full_run_requires_an_explicit_seed():
    with pytest.raises(ValueError, match="seed"):
        run({})

