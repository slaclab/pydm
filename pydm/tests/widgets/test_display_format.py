import pytest
import numpy as np
from pydm.PyQt.QtGui import QWidget

from pydm.widgets.display_format import  DisplayFormat, parse_value_for_display


# --------------------
# POSITIVE TEST CASES
# --------------------

@pytest.mark.parametrize("value, precision, display_format, widget, expected", [
    ("abc", 0, DisplayFormat.Default, QWidget, "abc"),
    (123, 0, DisplayFormat.Default, QWidget, 123),
    (123.45, 0, DisplayFormat.Default, QWidget, 123.45),
    ("abc", 0, DisplayFormat.String, QWidget, "abc"),
    (123.45, 0, DisplayFormat.Decimal, QWidget, 123.45),
    (3.000e-02, 0, DisplayFormat.Exponential, QWidget, "3e-02"),
    (0x07FF, 0, DisplayFormat.Hex, QWidget, "0x7ff"),
    (0b1101, 0, DisplayFormat.Binary, QWidget, "0b1101"),
])
def test_parse_value_for_display_format(value, precision, display_format, widget, expected):
    """
    Test the correctness of the displayed value according to the specified value
    type.
    Invariance:
    1. For each value provided, the display format (the string representation of the value) must be as expected
    2. All supported formats must be tested
    :param value: The data to be formatted
    :type: int, float, hex, bin, or str
    :param precision: The numeric precision to consider during formatting
    :type: int
    :param display_format: The format type for the provided value
    :type: int
    :param widget: The widget that will display the formatted value. This object can be None
    :type: PyDMWidget
    :param expected: The expected formatted presentation of the provided value
    :type: str
    """
    assert parse_value_for_display(
        value, precision, display_format_type=display_format, widget=widget) == expected


@pytest.mark.parametrize("value, precision, display_format, widget, expected", [
    (123.45, 1, DisplayFormat.Default, QWidget, 123.45),
    (123.45, 1, DisplayFormat.Decimal, QWidget, 123.45),
    (3.000e-02, 2, DisplayFormat.Exponential, QWidget, "3.00e-02"),
    (3.000e-02, 3, DisplayFormat.Exponential, QWidget, "3.000e-02"),
    (1.234, 3, DisplayFormat.Hex, QWidget, "0x1"),
    (-1.234, 3, DisplayFormat.Hex, QWidget, "-0x2"),
    (1.234, 3, DisplayFormat.Binary, QWidget, "0b1"),
    (-1.234, 3, DisplayFormat.Binary, QWidget, "-0b10")
])
def test_parse_value_for_display_precision(value, precision, display_format, widget, expected):
    """
    Test the correctness of the displayed value according to the specified value precision.
    Invariance:
    The formatted presentation of the displayed value must present the numeric precision as requested, providing a
    precision consideration is applicable for the provided value, for all supported display formats.
    :param value: The data to be formatted
    :type: int, float, hex, bin, or str
    :param precision: The numeric precision to consider during formatting
    :type: int
    :param display_format: The format type for the provided value
    :type: int
    :param widget: The widget that will display the formatted value. This object can be None
    :type: PyDMWidget
    :param expected: The expected formatted presentation of the provided value
    :type: str
    """
    assert parse_value_for_display(
        value, precision, display_format_type=display_format, widget=widget) == expected


# --------------------
# NEGATIVE TEST CASES
# ---------------------

@pytest.mark.parametrize("value, precision, display_format, widget, expected", [
    (np.ndarray([65, 66, 67, 68]), 1, DisplayFormat.String, QWidget, "Could not decode"),
    ("aaa", 1, DisplayFormat.Exponential, QWidget, "Could not display in 'Exponential'"),
    ("zzz", 2, DisplayFormat.Hex, QWidget, "Could not display in 'Hex'"),
    ("zzz", 3, DisplayFormat.Binary, QWidget, "Could not display in 'Binary'"),
])
def test_parse_value_for_display_precision_incorrect_display_format(
        capfd, value, precision, display_format, widget, expected):
    """

    Parameters
    ----------
    capfd
    value
    precision
    display_format
    widget
    expected

    Returns
    -------

    """
    """
    Test that errors will be output into stderr.
    TODO: Provide logging for errors, and check the log for the appropriate error messages.
    :param capfd: stderr capturing fixture
    :type: fixture
    :param value: The data to be formatted
    :type: int, float, hex, bin, or str
    :param precision: The numeric precision to consider during formatting
    :type: int
    :param display_format: The format type for the provided value
    :type: int
    :param widget: The widget that will display the formatted value. This object can be None
    :type: PyDMWidget
    :param expected: The expected error message to be streamed to stderr
    :type: str
    """
    parsed_value = parse_value_for_display(
        value, precision, display_format_type=display_format, widget=widget)
    assert(value == parsed_value)

    out, err = capfd.readouterr()
    assert expected in err
