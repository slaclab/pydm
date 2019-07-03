import pytest

from ...widgets.byte import PyDMByteIndicator


@pytest.mark.parametrize("shift, value, expected", [
    (0, 0, (False, False, False)),
    (0, 5, (True, False, True)),
    (0, -5, (False, False, False)),

    (1, 0, (False, False, False)),
    (1, 4, (False, True, False)),
    (1, -5, (False, False, False)),

    (-1, 0, (False, False, False)),
    (-1, 1, (False, True, False)),
    (-1, -5, (False, False, False)),
])
def test_value_shift(qtbot, shift, value, expected):
    """
    Test the widget's handling of the value changed event affected by predefined shift.

    Expectations:
    1. Value coming from the control system is correctly shifted by the predefined value
    2. Resulting value should be non-negative

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    value : int
        The value to be displayed by the widget
    shift : int
        The value's bit shift
    expected : int
        Expected resulting value
    """
    num_bits = len(expected)
    pydm_byte = PyDMByteIndicator()
    qtbot.addWidget(pydm_byte)
    pydm_byte.numBits = num_bits
    pydm_byte.shift = shift
    pydm_byte._connected = True

    pydm_byte.value_changed(value)

    for i, bit, indicator in zip(range(num_bits), expected, pydm_byte._indicators):
        expected_color = pydm_byte.onColor if bit else pydm_byte.offColor
        assert indicator._brush.color().name() == expected_color.name(), "Failed to match bit#{}".format(i)
