
import pytest

from clickpilot.clicker import Clicker


@pytest.mark.parametrize(
    ("value", "unit", "expected"),
    [
        (1, "ms", 1),
        (100, "ms", 100),
        (1, "s", 1000),
        (1.5, "s", 1500),
        (1, "min", 60000),
        (0.001, "s", 1),
    ],
)
def test_to_milliseconds(value, unit, expected):
    assert Clicker.to_milliseconds(value, unit) == expected


@pytest.mark.parametrize(
    ("value", "unit"),
    [
        (0, "ms"),
        (-1, "s"),
        (0.0001, "s"),
        (1441, "min"),
        (1, "hours"),
        (float("inf"), "s"),
        (float("nan"), "s"),
    ],
)
def test_to_milliseconds_rejects_invalid_values(value, unit):
    with pytest.raises(ValueError):
        Clicker.to_milliseconds(value, unit)
