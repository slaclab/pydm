# Unit Tests for the PyDMLineEdit Widget

import pytest

import numpy as np
from logging import ERROR

from qtpy.QtWidgets import QMenu
from pydm.widgets.line_edit import PyDMLineEdit
from pydm.data_plugins import set_read_only
from pydm.utilities import is_pydm_app, find_unit_options
from pydm.widgets.display_format import DisplayFormat, parse_value_for_display
from pydm.tests.widgets.utils import find_action_from_menu


@pytest.mark.parametrize("init_channel", [
    "CA://MTEST",
    "",
    None,
])
def test_construct(qtbot, init_channel):
    """
    Test the widget construct.
    Expectations:
    All parameters have the correct default value.

    Parameters
    ----------
     qtbot : fixture
        Window for widget testing
    init_channel : str
        The data channel to be used by the widget

    """
    pydm_lineedit = PyDMLineEdit(init_channel=init_channel)
    qtbot.addWidget(pydm_lineedit)

    if init_channel:
        assert pydm_lineedit.channel == str(init_channel)
    else:
        assert pydm_lineedit.channel is None
    assert pydm_lineedit._display is None
    assert pydm_lineedit._scale == 1
    assert pydm_lineedit._prec == 0
    assert pydm_lineedit.showUnits == False
    assert isinstance(pydm_lineedit.unitMenu, QMenu) and pydm_lineedit.unitMenu.title() == "Convert Units"
    assert pydm_lineedit.displayFormat == pydm_lineedit.DisplayFormat.Default
    assert (pydm_lineedit._string_encoding == pydm_lineedit.app.get_string_encoding()
            if is_pydm_app() else "utf_8")

    assert find_action_from_menu(pydm_lineedit.unitMenu, "No Unit Conversions found")


def test_write_access_changed(qtbot):
    pydm_lineedit = PyDMLineEdit(init_channel="ca://foo")
    qtbot.addWidget(pydm_lineedit)
    assert pydm_lineedit.isEnabled() is False
    assert pydm_lineedit.isReadOnly() is False
    assert pydm_lineedit._write_access is False

    pydm_lineedit.connection_changed(True)

    pydm_lineedit.write_access_changed(True)
    assert pydm_lineedit.isEnabled() is True
    assert pydm_lineedit.isReadOnly() is False

    pydm_lineedit.write_access_changed(False)
    assert pydm_lineedit.isEnabled() is False
    assert pydm_lineedit.isReadOnly() is True


@pytest.mark.parametrize("display_format", [
    (DisplayFormat.Default),
    (DisplayFormat.Exponential),
    (DisplayFormat.String),
    (DisplayFormat.Binary),
    (DisplayFormat.Decimal),
    (DisplayFormat.Hex),
])
def test_change_display_format_type(qtbot, display_format):
    """
    Test the widget's DisplayFormat property and setter.

    Expectations:
    The widget can set the DisplayFormat property, and retrieve it correctly.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    display_format : DisplayFormat
        The new DisplayFormat value to set
    """
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit.displayFormat = display_format
    assert pydm_lineedit.displayFormat == display_format


@pytest.mark.parametrize("value, display_format, precision, scale, unit, show_unit, expected_display", [
    (123, DisplayFormat.Default, 3, 1, "s", True, "123.000 s"),
    (123.47, DisplayFormat.Decimal, 3, 2, "seconds", False, "246.94"),
    (1e2, DisplayFormat.Exponential, 2, 2, "light years", True, "2.00e+02 light years"),
    (0x1FF, DisplayFormat.Hex, 0, 1, "Me", True, "0x1ff Me"),
    (0b100, DisplayFormat.Binary, 0, 1, "KB", True, "0b100 KB"),
    (np.array([123, 456]), DisplayFormat.Default, 3, 2, "light years", True, "[123 456] light years"),
])
def test_value_change(qtbot, value, display_format, precision, scale, unit, show_unit, expected_display):
    """
    Test changing the value to be displayed by the widget, given the value's display format, precision, scale, and unit.

    Expectations:
    The widget displays the new value properly, taken into account the value's display format, precision, scale, and
    unit.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    value : int, float, bin, hex, numpy.array
        The value to be displayed by the widget
    display_format : DisplayFormat
        The value's display format (Default, Decimal, Exponential, Hex, Binary)
    precision : int
        The number of decimal places in the displayed value
    scale : int
        The factor to reduce or magnify the given value
    unit : str
        The value unit to be displayed
    show_unit : bool
        True if the value unit is to be displayed. False otherwise
    expected_display : str
        The expected display contents to be compared to the actual widget's displayed content
    """
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit.displayFormat = display_format
    pydm_lineedit.precision_changed(precision)
    pydm_lineedit.channeltype = type(value)
    pydm_lineedit.unit_changed(unit)
    pydm_lineedit.showUnits = show_unit
    pydm_lineedit._scale = scale
    pydm_lineedit.value_changed(value)

    assert pydm_lineedit._display == expected_display


@pytest.mark.parametrize("init_value, user_typed_value, display_format, precision, scale, unit,"
                         "show_units, expected_received_value, expected_display_value", [
    ("abc", "cdf", DisplayFormat.Default, 3, 5, "s", True, "abc", "cdf s"),
    ("abc", "cdf", DisplayFormat.String, 3, 5, "s", False, "abc", "cdf"),
    (np.array([65, 66]), "[C D]", DisplayFormat.Default, 0, 10, "light years", True, "[C D]",
    "[C D] light years"),
    (np.array(["A", "B"]), "[C D]", DisplayFormat.String, 0, 10, "ms", True, "[C D]", "[C D] ms"),
    (np.array(["A", "B"]), np.array(["C", "D"]), DisplayFormat.String, 0, 10, "ms", True, "C   D    ", "C   D    ms"),
    (np.array(["A", "B"]), np.array(["C", "D"]), DisplayFormat.Default, 0, 10, "ms", True, "['C' 'D']", "['C' 'D'] ms"),
])
def test_send_value(qtbot, init_value, user_typed_value, display_format, precision, scale, unit,
                    show_units, expected_received_value, expected_display_value):
    """
    Test sending the value to the channel, and the displayed value by the widget.

    Expectations:

    1. The value sent to the channel will be affected by the precision only
    2. The value displayed by the widget will be affected by the scale, and show unit Boolean flag

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    init_value : int, float, hex, bin, str, numpy.array
        The initial value currently assigned to the widget
    user_typed_value : str
        The new value as provided (typed in) by the user
    display_format : DisplayFormat
        The display format of the current value, only str allowed
    precision : int
        The number of decimal places to consider for the new value
    scale : int
        The factor to reduce or magnify the new value
    unit : str
        The unit of the new value
    show_units : bool
        True if the value unit is to be displayed. False otherwise
    expected_received_value : int, float, hex, bin, str, numpy.array
        The expected new value to send to the channel
    expected_display_value : str
        The expected new content to be displayed by the widget
    """
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    def foo(val):
        pydm_lineedit.test_write = val

    pydm_lineedit.write_to_channel = foo

    pydm_lineedit.value = init_value
    pydm_lineedit.channeltype = type(init_value)
    pydm_lineedit.displayFormat = display_format
    pydm_lineedit._prec = precision
    pydm_lineedit._scale = scale
    pydm_lineedit._unit = unit
    pydm_lineedit.showUnits = show_units

    pydm_lineedit.value_changed(user_typed_value)
    pydm_lineedit.send_value()

    # Python 2.7 produces the strings without the spaces, but Python 3.x does not. So, remove all the spaces, and
    # compare just the characters (in the right order)
    assert pydm_lineedit.displayText().replace(" ", "") == expected_display_value.replace(" ", "")

    if all(x in (int, float) for x in (type(expected_received_value), type(pydm_lineedit.test_write))) :
        # Testing the actual value sent to the data channel and the expected value using a tolerance due to floating
        # point arithmetic
        assert abs(pydm_lineedit.test_write - expected_received_value) < 0.00001


@pytest.mark.parametrize("new_unit", [
    "s",
    "light years",
    "",
])
def test_unit_change(qtbot, new_unit):
    """
    Test setting the widget's unit.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    new_unit : str
        The new unit to set to the widget
    """
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit.unit_changed(new_unit)

    assert pydm_lineedit._unit == new_unit
    assert pydm_lineedit._scale == 1


@pytest.mark.parametrize("unit, show_units", [
    ("ms", True),
    ("s", False),
    ("MHz", True),
    ("V", True),
    ("in", True),
    ("mrad", True),
    ("MA", True),
])
def test_create_unit_options(qtbot, unit, show_units):
    """
    Test to ensure the context menu contains all applicable units that can be converted to from a given unit.

    Expectations:

    Given a unit and the show unit flag being set to True, the context menu must contain a unit conversion menu that
    has all the applicable units the original unit can be converted to.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    unit : str
        The original unit
    show_units : bool
        If True, the context menu must contain all the conversion units; False otherwise
    """
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit._unit = unit
    pydm_lineedit._show_units = show_units
    pydm_lineedit.create_unit_options()

    menu = pydm_lineedit.widget_ctx_menu()
    action_menu = menu.menuAction().menu()

    if unit and show_units:
        # Get all the units that can be converted to from the original unit
        units = find_unit_options(pydm_lineedit._unit)
        for unit in units:
            # For each of such unit, make sure it's in the context menu
            assert find_action_from_menu(action_menu, unit)
    else:
        # If no unit is provided, or the unit isn't required to be shown, the context menu should display
        # "No Unit Conversions found"
        assert find_action_from_menu(action_menu, "No Unit Conversions found")


@pytest.mark.parametrize("value, precision, unit, show_unit, expected_format_string", [
    (123, 0, "s", True, "{:.0f} s"),
    (123.456, 3, "mV", True, "{:.3f} mV"),
])
def test_apply_conversion(qtbot, value, precision, unit, show_unit, expected_format_string):
    """
    Test the unit conversion by examining the resulted format string.

    Expectations:

    Provided with the value, precision, unit, and the show unit Boolean flag by the user, this function must provide
    the correct format string to format the displayed value for the widget.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    value : int, float, bin, hex, numpy.array
        The value to be converted
    precision : int
        The
    unit : str
        The unit of the new value
    show_units : bool
        True if the value unit is to be displayed. False otherwise
    expected_format_string : str
        The expected format string that will produce the correct displayed value after the conversion
    """
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit.value = value
    pydm_lineedit._unit = unit
    pydm_lineedit._prec = precision
    pydm_lineedit.showUnits = show_unit

    pydm_lineedit.apply_conversion(unit)
    assert pydm_lineedit.format_string == expected_format_string


@pytest.mark.parametrize("value, has_focus, channel_type, display_format, precision, scale, unit, show_units", [
    (123, True, int, DisplayFormat.Default, 3, 1, "s", True),
    (123, False, int, DisplayFormat.Default, 3, 1, "s", True),
    (123, True, int, DisplayFormat.Default, 3, 1, "s", False),
    (123, False, int, DisplayFormat.Default, 3, 1, "s", False),
    (123.45, True, float, DisplayFormat.Decimal, 3, 2, "m", True),
    (1e3, True, int, DisplayFormat.Exponential, 2, 2, "GHz", True),
    (0x1FF, True, int, DisplayFormat.Hex, 0, 1, "Me", True),
    (0b100, True, int, DisplayFormat.Binary, 0, 1, "KB", True),
    (np.array([123, 456]), str, True, DisplayFormat.Default, 3, 2, "degree", True),
])
def test_set_display(qtbot, qapp, value, has_focus, channel_type, display_format, precision, scale, unit, show_units):
    """
    Test the widget's displayed value.

    Expectations:

    The widget displays the value according to the display format from parsing the value and from the data type.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    has_focus : Boolean
        True if the widget has the focus; False otherwise
    channel_type : type
        The type of the input value
    display_format : DisplayFormat
        The format to display the value
    precision : int
        The number of decimal places to consider for the new value
    scale : int
        The factor to reduce or magnify the new value
    unit : str
        The unit of the new value
    show_units : bool
        True if the value unit is to be displayed. False otherwise
    """
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)
    with qtbot.waitExposed(pydm_lineedit):
        pydm_lineedit.show()

    pydm_lineedit.value = value
    pydm_lineedit._unit = unit
    pydm_lineedit.displayFormat = display_format
    pydm_lineedit._scale = scale
    pydm_lineedit.channeltype = channel_type
    pydm_lineedit.showUnits = show_units
    pydm_lineedit._prec = precision
    pydm_lineedit._display = "Empty"
    pydm_lineedit._connected = True
    pydm_lineedit._write_access = True
    pydm_lineedit.check_enable_state()

    if has_focus:
        pydm_lineedit.setFocus()
        def wait_focus():
            return pydm_lineedit.hasFocus()

        qtbot.waitUntil(wait_focus, timeout=5000)

        pydm_lineedit.set_display()

        # If there's no focus on the widget, its display will not be updated
        assert pydm_lineedit._display == "Empty"
    else:
        pydm_lineedit.clearFocus()
        def wait_nofocus():
            return not pydm_lineedit.hasFocus()

        qtbot.waitUntil(wait_nofocus, timeout=5000)
        pydm_lineedit.set_display()

        new_value = value
        if not isinstance(value, (str, np.ndarray)):
            new_value *= pydm_lineedit.channeltype(pydm_lineedit._scale)

        new_value = parse_value_for_display(value=new_value, precision=precision, display_format_type=display_format,
                                            widget=pydm_lineedit)

        expected_display = str(new_value)
        if display_format == DisplayFormat.Default and not isinstance(value, np.ndarray):
            if isinstance(value, (int, float)):
                expected_display = str(pydm_lineedit.format_string.format(value))
        elif pydm_lineedit.showUnits:
            expected_display += " {}".format(unit)

        assert pydm_lineedit._display == expected_display


@pytest.mark.parametrize("display_value", [
    "123",
    "123.456",
    "",
])
def test_focus_out_event(qtbot, qapp, display_value):
    """
    Test the widget's value revert capability if the user doesn't commit the value change.

    Expectations:

    If the user types in some value to the widget, but then does not commit the change, but simply leaves the widget,
    i.e. generating a focusOut event, the widget's value will revert to the original one.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    qapp : fixture
        The current pytest-qt app
    display_value : str
        The new value entered by the user before leaving the widget without committing this value
    """
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)
    with qtbot.waitExposed(pydm_lineedit):
        pydm_lineedit.show()

    pydm_lineedit._connected = True
    pydm_lineedit._write_access = True
    pydm_lineedit.check_enable_state()

    pydm_lineedit._display = display_value
    pydm_lineedit.setFocus()
    qapp.processEvents()
    def wait_focus():
        qapp.processEvents()
        return pydm_lineedit.hasFocus()

    qtbot.waitUntil(wait_focus, timeout=5000)

    pydm_lineedit.setText("Canceled after the focusOut event")
    pydm_lineedit.clearFocus()

    def wait_nofocus():
        qapp.processEvents()
        return not pydm_lineedit.hasFocus()

    qtbot.waitUntil(wait_nofocus, timeout=5000)

    # Make sure the widget still retains the previously set value after the focusOut event
    assert pydm_lineedit.text() == display_value

# --------------------
# NEGATIVE TEST CASES
# --------------------

@pytest.mark.parametrize("value, precision, initial_unit, unit, show_unit, expected", [
    (123, 0, None, int, True,
     ("Warning: Attempting to convert PyDMLineEdit unit, but no initial units supplied",)),
    (123.456, 3, float, int, True,
     ("Warning: Attempting to convert PyDMLineEdit unit, but ", "'float'>' can not be converted to ", "'int'>'.")),
    (123.456, 3, float, "foo", True,
     ("Warning: Attempting to convert PyDMLineEdit unit, but ", "'float'>' can not be converted to 'foo'.")),
    ("123.456", 3, "light years", "light years", False,
     ("Warning: Attempting to convert PyDMLineEdit unit, but 'light years' can not be converted to 'light years'.",)),
])
def test_apply_conversion_wrong_unit(qtbot, caplog, value, precision, initial_unit, unit, show_unit, expected):
    """
    Test the unit conversion error logging.

    Expectations:

    Errors result from unit conversion problems must be logged correctly.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    caplog : fixture
        To capture the log messages
    value : int, float, bin, hex, numpy.array
        The signals fixture, which provides access signals to be bound to the appropriate slots
    precision : int
        The
    unit : str
        The unit of the new value
    show_units : bool
        True if the value unit is to be displayed. False otherwise
    expected : str
        The expected logged error statement
    """
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit.value = value
    pydm_lineedit._unit = initial_unit
    pydm_lineedit._prec = precision
    pydm_lineedit.showUnits = show_unit

    pydm_lineedit.apply_conversion(unit)
    assert all(x in caplog.text for x in expected)


@pytest.mark.parametrize("init_value, user_typed_value, display_format, precision, scale, unit,"
                         "show_units, expected_errors", [
    (123, 345.678, DisplayFormat.Default, 0, 1, "s", True, ("Error trying to set data ", "with type ", "int'>")),
])
def test_send_value_neg(qtbot, caplog, init_value, user_typed_value, display_format, precision, scale, unit,
                        show_units, expected_errors):
    """
    Test sending the value to the channel error logging.

    Expectations:

    Errors result from data sending problems must be logged correctly.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    caplog : fixture
        To capture the log messages
    init_value : int, float, hex, bin, str, numpy.array
        The initial value currently assigned to the widget
    user_typed_value : int, float, hex, bin, str, numpy.array
        The new value as provided (typed in) by the user
    display_format : DisplayFormat
        The display format of the current value
    precision : int
        The number of decimal places to consider for the new value
    scale : int
        The factor to reduce or magnify the new value
    unit : str
        The unit of the new value
    show_units : bool
        True if the value unit is to be displayed. False otherwise
    expected_errors : str
        The expected logged error statement
    """
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit.value = init_value
    pydm_lineedit.channeltype = type(init_value)
    pydm_lineedit.displayFormat = display_format
    pydm_lineedit._prec = precision
    pydm_lineedit._scale = scale
    pydm_lineedit._unit = unit
    pydm_lineedit.showUnits = show_units

    pydm_lineedit.send_value()

    for record in caplog.records:
        assert record.levelno == ERROR
    assert all(x in caplog.text for x in expected_errors)
