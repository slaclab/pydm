import pytest

from pydm.data_plugins.local_plugin import Connection


@pytest.mark.parametrize(
    "value, expected",
    [
        # Values Decimal renders with a decimal point, unchanged behavior.
        (3.14159, 5),
        (0.0001, 4),
        (12345.6, 1),
        (5.0, 1),
        (0.123456789, 8),
        # Values Decimal renders without one, which used to raise IndexError.
        (1e-9, 8),
        (1e-12, 8),
        (1e20, 0),
        (float("nan"), 0),
        (float("inf"), 0),
        (5, 0),
    ],
)
def test_precision_for_value(value, expected):
    assert Connection.precision_for_value(value) == expected


def test_precision_for_value_honors_max_precision():
    assert Connection.precision_for_value(1e-9, max_precision=3) == 3
