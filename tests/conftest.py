import pytest

from logistica.red import Red, cargar_red


@pytest.fixture(scope="session")
def red() -> Red:
    return cargar_red()
