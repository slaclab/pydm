# Unit Tests for the PyDMLineEdit Widget

import pytest

import numpy as np
from logging import ERROR

from qtpy.QtWidgets import QMenu
from ...widgets.line_edit import PyDMLineEdit
from ...utilities import is_pydm_app, find_unit_options
from ...widgets.display_format import DisplayFormat, parse_value_for_display


# --------------------
# POSITIVE TEST CASES
# --------------------

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
    assert pydm_lineedit.isEnabled() == False
    assert pydm_lineedit.showUnits == False
    assert isinstance(pydm_lineedit.unitMenu, QMenu) and pydm_lineedit.unitMenu.title() == "Convert Units"
    assert pydm_lineedit.displayFormat == pydm_lineedit.DisplayFormat.Default
    assert (pydm_lineedit._string_encoding == pydm_lineedit.app.get_string_encoding()
            if is_pydm_app() else "utf_8")

    assert find_action_from_menu(pydm_lineedit.unitMenu, "No Unit Conversions found")


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
def test_value_change(qtbot, signals, value, display_format, precision, scale, unit, show_unit, expected_display):
    """
    Test changing the value to be displayed by the widget, given the value's display format, precision, scale, and unit.

    Expectations:
    The widget displays the new value properly, taken into account the value's display format, precision, scale, and
    unit.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
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
    pydm_lineedit._prec = precision
    pydm_lineedit._scale = scale
    pydm_lineedit.channeltype = type(value)
    pydm_lineedit._unit = unit
    pydm_lineedit.showUnits = show_unit

    signals.new_value_signal[type(value)].connect(pydm_lineedit.channelValueChanged)
    signals.new_value_signal[type(value)].emit(value)

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
def test_send_value(qtbot, signals, init_value, user_typed_value, display_format, precision, scale, unit,
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
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
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

    pydm_lineedit.value = init_value
    pydm_lineedit.channeltype = type(init_value)
    pydm_lineedit.displayFormat = display_format
    pydm_lineedit._prec = precision
    pydm_lineedit._scale = scale
    pydm_lineedit._unit = unit
    pydm_lineedit.showUnits = show_units

    signals.new_value_signal[type(user_typed_value)].connect(pydm_lineedit.channelValueChanged)
    signals.new_value_signal[type(user_typed_value)].emit(user_typed_value)

    # Besides receiving the new channel value, simulate the update of the new value to the widget by connecting the
    # channelValueChanged slot to the same signal
    signal_type = type(user_typed_value)
    if signal_type == np.ndarray:
        signal_type = str
    pydm_lineedit.send_value_signal[signal_type].connect(signals.receiveValue)
    pydm_lineedit.send_value_signal[signal_type].connect(pydm_lineedit.channelValueChanged)
    pydm_lineedit.send_value()

    # Python 2.7 produces the strings without the spaces, but Python 3.x does not. So, remove all the spaces, and
    # compare just the characters (in the right order)
    assert pydm_lineedit.displayText().replace(" ", "") == expected_display_value.replace(" ", "")

    if all(x in (int, float) for x in (type(expected_received_value), type(signals.value))) :
        # Testing the actual value sent to the data channel and the expected value using a tolerance due to floating
        # point arithmetic
        assert abs(signals.value - expected_received_value) < 0.00001


@pytest.mark.parametrize("new_write_access, is_channel_connected, tooltip, is_app_read_only", [
    (True, True, "Write Access and Connected Channel", False),
    (False, True, "Only Connected Channel", False),
    (True, False, "Only Write Access", False),
    (False, False, "No Write Access and No Connected Channel", False),

    (True, True, "Write Access and Connected Channel", True),
    (False, True, "Only Connected Channel", True),
    (True, False, "Only Write Access", True),
    (False, False, "No Write Access and No Connected Channel", True),

    (True, True, "", False),
    (True, True, "", True),
])
def test_write_access_changed(qtbot, signals, new_write_access, is_channel_connected, tooltip, is_app_read_only):
    """
    Test the widget's write access status and tooltip, which depends on the connection status of the data channel and
    the app's read-only status.

    Expectations:

    1. If the write access is set to False, the widget is read-only.
    2. If the data channel is disconnected, the widget's tooltip will  "PV is disconnected"
    3. If the data channel is connected, but it has no write access:
        a. If the app is read-only, the tooltip will read  "Running PyDM on Read-Only mode."
        b. If the app is not read-only, the tooltip will read "Access denied by Channel Access Security."

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    new_write_access : bool
        True if the widget has write access; False otherwise
    is_channel_connected : bool
        True if the data channel is connected; False otherwise
    tooltip : str
        The widget's tooltip
    is_app_read_only : bool
        True if the app is read-only; False otherwise
    """
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit.channel = "CA://MTEST"
    pydm_lineedit._conneted = is_channel_connected
    pydm_lineedit.setToolTip(tooltip)
    pydm_lineedit.app.__read_only = is_app_read_only

    signals.write_access_signal.connect(pydm_lineedit.writeAccessChanged)
    signals.write_access_signal.emit(new_write_access)

    # The widget is expected to be always enabled
    assert pydm_lineedit.isEnabled()
    assert pydm_lineedit.isReadOnly() == (not new_write_access)

    actual_tooltip = pydm_lineedit.toolTip()
    if not pydm_lineedit._connected:
        assert "PV is disconnected." in actual_tooltip
    elif not new_write_access:
        if is_pydm_app() and is_app_read_only:
            assert "Running PyDM on Read-Only mode." in actual_tooltip
        else:
            assert "Access denied by Channel Access Security." in actual_tooltip


@pytest.mark.parametrize("is_precision_from_pv, pv_precision, non_pv_precision", [
    (True, 1, 3),
    (False, 5, 3),
    (True, 6, 0),
    (True, 3, None),
    (False, 3, None),
])
def test_precision_change(qtbot, signals, is_precision_from_pv, pv_precision, non_pv_precision):
    """
    Test setting the precision for the widget's value.

    Expectations:

    1. If the precision comes from the PV, emit a prec_signal to change the widget's precision.
    2. If this is a non-PV precision, set the widget's precision directly.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    is_precision_from_pv : bool
        True if the precision value comes from the PV; False otherwise
    pv_precision : int
        The PV precision value to set to the widget
    non_pv_precision : int
        The non-PV precision value to set to the widget
    """
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit.precisionFromPV = is_precision_from_pv
    pydm_lineedit.precision = non_pv_precision

    if is_precision_from_pv:
        signals.prec_signal[type(pv_precision)].connect(pydm_lineedit.precisionChanged)
        signals.prec_signal.emit(pv_precision)

        assert pydm_lineedit._prec == pv_precision
    else:
        assert pydm_lineedit._prec == non_pv_precision if non_pv_precision else pydm_lineedit._prec == 0


@pytest.mark.parametrize("new_unit", [
    "s",
    "light years",
    "",
])
def test_unit_change(qtbot, signals, new_unit):
    """
    Test setting the widget's unit.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    new_unit : str
        The new unit to set to the widget
    """
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    signals.unit_signal[str].connect(pydm_lineedit.unitChanged)
    signals.unit_signal.emit(new_unit)

    assert pydm_lineedit._unit == new_unit


def find_action_from_menu(menu, action_name):
    """
    Verify if an action (a conversion unit) is available in a context menu.

    Parameters
    ----------
    menu : QMenu
        The context menu of a widget
    action_name : str
        A menu text item

    Returns
    -------
    True if the action name is found in the menu; False otherwise
    """
    for action in menu.actions():
        if action.menu():
            # The action will always contain a menu, so the status will be created
            status = find_action_from_menu(action.menu(), action_name)
        if not action.isSeparator():
            if action_name == action.text():
                return True
    return status


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
def test_send_value_neg(qtbot, caplog, signals, init_value, user_typed_value, display_format, precision, scale, unit,
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
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
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

    signal_type = type(user_typed_value)
    if signal_type == np.ndarray:
        signal_type = str
    pydm_lineedit.send_value_signal[signal_type].connect(signals.receiveValue)
    pydm_lineedit.send_value_signal[signal_type].connect(pydm_lineedit.channelValueChanged)
    pydm_lineedit.send_value()

    for record in caplog.records:
        assert record.levelno == ERROR
    assert all(x in caplog.text for x in expected_errors)
