import pytest
import numpy as np
from pydm.PyQt.QtGui import QWidget

from ...widgets.display_format import  DisplayFormat, parse_value_for_display


# --------------------
# POSITIVE TEST CASES
#---------------------

# Test the correctness of the displayed value according to the specified value
# type
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
    assert parse_value_for_display(
        value, precision, display_format_type=display_format) == expected


# Test the correctness of the displayed value according to the specified value
# precision
@pytest.mark.parametrize("value, precision, display_format, widget, expected", [
    (123.45, 1, DisplayFormat.Default, QWidget, 123.45),
    (123.45, 1, DisplayFormat.Decimal, QWidget, 123.45),
    (3.000e-02, 2, DisplayFormat.Exponential, QWidget, "3.00e-02"),
    (3.000e-02, 3, DisplayFormat.Exponential, QWidget, "3.000e-02"),
    (1.234, 3, DisplayFormat.Hex, QWidget, "0x1"),
    (-1.234, 3, DisplayFormat.Hex, QWidget, "-0x1"),
    (1.234, 3, DisplayFormat.Binary, QWidget, "0b1"),
    (-1.234, 3, DisplayFormat.Binary, QWidget, "-0b1")

])
def test_parse_value_for_display_precision(value, precision, display_format, widget, expected):
    assert parse_value_for_display(
        value, precision, display_format_type=display_format, widget=widget) == expected


# --------------------
# NEGATIVE TEST CASES
#---------------------

# Test for exceptions thrown for mismatching display formats and corresponding
# values
@pytest.mark.parametrize("value, precision, display_format, widget, expected", [
    (np.ndarray([65, 66, 67, 68]), 1, DisplayFormat.String, QWidget, "Could not decode"),
    #(123.45, 1, DisplayFormat.Decimal, QWidget, 123.45),
    #(3.000e-02, 2, DisplayFormat.Exponential, QWidget, "3.00e-02"),
    #(3.000e-02, 3, DisplayFormat.Exponential, QWidget, "3.000e-02"),
    #(1.234, 3, DisplayFormat.Hex, QWidget, "0x1"),
    #(1.234, 3, DisplayFormat.Binary, QWidget, "0b1")

])
def test_parse_value_for_display_precision_incorrect_display_format(
        capfd, value, precision, display_format, widget, expected):
    parse_value_for_display(
        value, precision, display_format_type=display_format, widget=widget)

    out, err = capfd.readouterr()
    assert expected in err



# Test for exceptions thrown for precisions inapplicable to corresponding values


# Test for null widgets being provided in correct display formats

# Test for null widgets being provided in incorrect display formats

"""
@pytest.mark.parametrize("value, precision, display_format, widget, expected", [
    (np.ndarray([80, 121, 68, 77, 32, 82, 111, 99, 107, 115, 33]),
     0, DisplayFormat.String, QWidget,
     np.ndarray([80, 121, 68, 77, 32, 82, 111, 99, 107, 115, 33])),
])
def test_parse_value_for_display_negative(value, precision, display_format, widget, expected):
    pass
"""
