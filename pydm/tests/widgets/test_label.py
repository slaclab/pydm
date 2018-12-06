# Unit Tests for the PyDMLabel Widget


import pytest
import numpy as np
import logging

from ...utilities import is_pydm_app
from ...widgets.label import PyDMLabel
from ...widgets.base import PyDMWidget
from ...widgets.display_format import parse_value_for_display, DisplayFormat

from qtpy.QtWidgets import QApplication, QStyleOption

# --------------------
# POSITIVE TEST CASES
# --------------------

def test_construct(qtbot):
    """
    Test the basic instantiation of the widget.

    Expectations:
    The widget was created with the following default settings:
    1. DisplayFormat is Default
    2. String encoding is the same as that specified in the PyDM App, or UTF-8

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    display_format_type = pydm_label.displayFormat
    assert display_format_type == pydm_label.DisplayFormat.Default
    assert pydm_label._string_encoding == pydm_label.app.get_string_encoding() if is_pydm_app() else "utf_8"


@pytest.mark.parametrize("value, display_format", [
    ("abc", DisplayFormat.Default),
    (123, DisplayFormat.Default),
    (0b100, DisplayFormat.Default),
    (0x1FF, DisplayFormat.Default),

    ("abc", DisplayFormat.String),
    (123, DisplayFormat.String),
    (0b100, DisplayFormat.String),
    (0x1FF, DisplayFormat.String),

    ("abc", DisplayFormat.Decimal), # This setting is acceptable. The displayed value will be "abc"
    (123, DisplayFormat.Decimal),
    (123.45, DisplayFormat.Decimal),
    (0b100, DisplayFormat.Decimal),
    (0x1FF, DisplayFormat.Decimal),

    (123, DisplayFormat.Exponential),
    (3.000e-02, DisplayFormat.Exponential),
    (0b100, DisplayFormat.Exponential),
    (0x1FF, DisplayFormat.Exponential),

    (123, DisplayFormat.Hex),
    (3.000e-02, DisplayFormat.Hex),
    (0b100, DisplayFormat.Hex),
    (0x1FF, DisplayFormat.Hex),

    (123, DisplayFormat.Binary),
    (3.000e-02, DisplayFormat.Binary),
    (0b100, DisplayFormat.Binary),
    (0x1FF, DisplayFormat.Binary),
])
def test_value_changed(qtbot, signals, value, display_format):
    """
    Test the widget's handling of the value changed event.

    Expectations:
    The following settings are in place after the value changed signal is emitted:
    1. The value displayed by the widget is the new value
    2. The value format maintained by the widget the correct format for the new value

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    value : int, float, bin, hex, str
        The value to be displayed by the widget
    display_format : int
        The format of the widget's displayed value
    """
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    signals.new_value_signal[type(value)].connect(pydm_label.channelValueChanged)
    signals.new_value_signal[type(value)].emit(value)
    pydm_label.displayFormat = display_format

    displayed_value = parse_value_for_display(value=pydm_label.value, precision=1,
                                              display_format_type=pydm_label.displayFormat, widget=pydm_label)
    expected_value = parse_value_for_display(value=value, precision=1,
                                             display_format_type=display_format, widget=pydm_label)
    assert displayed_value == expected_value
    assert pydm_label.displayFormat == display_format


@pytest.mark.parametrize("values, selected_index, expected", [
    (("ON", "OFF"), 0, "ON"),
    (("ON", "OFF"), 1, "OFF"),
])
def test_enum_strings_changed(qtbot, signals, values, selected_index, expected):
    """
    Test the widget's handling of enum strings, which are choices presented to the user, and the widget's ability to
    update the selected enum string when the user provides a choice index.

    Expectations:
    The widget displays the correct enum string whose index from the enum string tuple is selected by the user.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    values : tuple
        A set of enum strings for the user to choose from
    selected_index : int
        The index from the enum string tuple chosen by the user
    expected : str
        The expected enum string displayed by the widget after receiving the user's choice index
    """
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    signals.enum_strings_signal.connect(pydm_label.enumStringsChanged)
    signals.enum_strings_signal.emit(values)
    pydm_label.displayFormat = DisplayFormat.String

    signals.new_value_signal[type(selected_index)].connect(pydm_label.channelValueChanged)
    signals.new_value_signal[type(selected_index)].emit(selected_index)

    assert pydm_label.value == selected_index
    assert pydm_label.text() == expected
    assert pydm_label.displayFormat == DisplayFormat.String


@pytest.mark.parametrize("value, display_format, unit_name, expected", [
    ("abc", DisplayFormat.Default, "", "abc"),
    (123, DisplayFormat.Default, "", "123"),
    (0b100, DisplayFormat.Default, "", "4"),
    (0x1FF, DisplayFormat.Default, "", "511"),

    ("abc", DisplayFormat.String, "s", "abc"),
    (123, DisplayFormat.String, "s", "123 s"),
    (0b100, DisplayFormat.String, "s", "4 s"),
    (0x1FF, DisplayFormat.String, "s", "511 s"),

    ("abc", DisplayFormat.Decimal, "light years", "abc"), # This setting is acceptable. The displayed value will be "abc"
    (123, DisplayFormat.Decimal, "light years", "123 light years"),
    (123.45, DisplayFormat.Decimal, "light years", "123 light years"), # Using default precision of 0
    (0b100, DisplayFormat.Decimal, "light years", "4 light years"),
    (0x1FF, DisplayFormat.Decimal, "light years", "511 light years"),

    # TODO: When parse_value_for_display returns a string, it should still contain the unit.
    # Right now, value_changed just returns a string as-is, without appending the unit to it.
    (123, DisplayFormat.Exponential, "ms", "1e+02"),
    (3.000e-02, DisplayFormat.Exponential, "ms", "3e-02"),
    (0b100, DisplayFormat.Exponential, "ms", "4e+00"),
    (0x1FF, DisplayFormat.Exponential, "ms", "5e+02"),

    (123, DisplayFormat.Hex, "ns", "0x7b"),
    (3.000e-02, DisplayFormat.Hex, "ns", "0x0"),
    (0b100, DisplayFormat.Hex, "ns", "0x4"),
    (0x1FF, DisplayFormat.Hex, "ns", "0x1ff"),

    (123, DisplayFormat.Binary, "light years", "0b1111011"),
    (3.000e-02, DisplayFormat.Binary, "light years", "0b0"),
    (0b100, DisplayFormat.Binary, "light years", "0b100"),
    (0x1FF, DisplayFormat.Binary, "light years", "0b111111111"),
])
def test_show_units(qtbot, signals, value, display_format, unit_name, expected):
    """
    Test the widget's capability to display a unit following a value if the user enables unit displaying.

    Expectations:
    1. The unit will be displayed following a space after the value
    2. The unit displayed can be toggled, depending on the user's value for the "show unit" flag to True, i.e.
       display the unit, or False, i.e. do not display the unit
    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    value : int, float, bin, hex, str
        The value to be displayed by the widget
    display_format : int
        The format of the widget's displayed value
    unit_name : str
        The name of the unit to be displayed by the widget, next to the value, separated with a space
    expected : str
        The expected string to be displayed by the widget
    """
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    signals.new_value_signal[type(value)].connect(pydm_label.channelValueChanged)
    signals.new_value_signal[type(value)].emit(value)
    pydm_label.displayFormat = display_format
    pydm_label.showUnits = False
    assert pydm_label.value == value

    # showUnits must be set first for the unit change to take effect
    pydm_label.showUnits = True
    signals.unit_signal[str].connect(pydm_label.unitChanged)
    signals.unit_signal[str].emit(unit_name)
    signals.new_value_signal[type(value)].emit(value)

    assert pydm_label.value == value
    assert pydm_label.text() == expected
    assert pydm_label.displayFormat == display_format

    # Now, turn off showUnits
    pydm_label.showUnits = False
    signals.new_value_signal[type(value)].emit(value)
    assert pydm_label.value == value
    if " " in expected:
        # We expect no unit to be displayed now, so the expected result must be adjusted to contain just the value
        expected = expected[0 : expected.find(" ")]
    assert pydm_label.text() == expected
    assert pydm_label.displayFormat == display_format


@pytest.mark.parametrize("alarm_severity, alarm_sensitive_content, alarm_sensitive_border", [
    (PyDMWidget.ALARM_NONE, True, True),
    (PyDMWidget.ALARM_NONE, True, False),
    (PyDMWidget.ALARM_NONE, False, True),
    (PyDMWidget.ALARM_NONE, False, False),

    (PyDMWidget.ALARM_MINOR, True, True),
    (PyDMWidget.ALARM_MINOR, True, False),
    (PyDMWidget.ALARM_MINOR, False, True),
    (PyDMWidget.ALARM_MINOR, False, False),

    (PyDMWidget.ALARM_MAJOR, True, True),
    (PyDMWidget.ALARM_MAJOR, True, False),
    (PyDMWidget.ALARM_MAJOR, False, True),
    (PyDMWidget.ALARM_MAJOR, False, False),

    (PyDMWidget.ALARM_INVALID, True, True),
    (PyDMWidget.ALARM_INVALID, True, False),
    (PyDMWidget.ALARM_INVALID, False, True),
    (PyDMWidget.ALARM_INVALID, False, False),

    (PyDMWidget.ALARM_DISCONNECTED, True, True),
    (PyDMWidget.ALARM_DISCONNECTED, True, False),
    (PyDMWidget.ALARM_DISCONNECTED, False, True),
    (PyDMWidget.ALARM_DISCONNECTED, False, False),
])
def test_label_alarms(qtbot, signals, alarm_severity, alarm_sensitive_content, alarm_sensitive_border):
    """
    Test the widget's appearance changes according to changes in alarm severity.

    Expectations:
    1. The widget receives the correct alarm severity
    2. The appearance changes to check for are the alarm content (alarm color), and the widget's border appearance, e.g.
       solid, transparent, etc.
    3. The alarm color and border appearance will change only if each corresponding Boolean flag is set to True

    NOTE: This test depends on the default stylesheet having different values for 'color' for different alarm states of PyDMLabel.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    alarm_severity : int
        The severity of an alarm (NONE, MINOR, MAJOR, INVALID, or DISCONNECTED)
    alarm_sensitive_content : bool
        True if the widget will change color accordingly to the alarm's severity; False if not
    alarm_sensitive_border : bool
        True if the widget's border will change color and thickness accordingly to the alarm's severity; False if not
    """
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    qtbot.addWidget(main_window)
    pydm_label = PyDMLabel(parent=main_window, init_channel="ca://FOOO")
    qtbot.addWidget(pydm_label)

    pydm_label.alarmSensitiveContent = alarm_sensitive_content
    pydm_label.alarmSensitiveBorder = alarm_sensitive_border

    signals.new_severity_signal.connect(pydm_label.alarmSeverityChanged)
    initial_severity = pydm_label._alarm_state
    option = QStyleOption()
    option.initFrom(pydm_label)
    before_color = option.palette.text().color().name()
    signals.new_severity_signal.emit(alarm_severity)

    assert pydm_label._alarm_state == alarm_severity
    option = QStyleOption()
    option.initFrom(pydm_label)
    after_color = option.palette.text().color().name()
    if alarm_sensitive_content and (alarm_severity != initial_severity):
        assert after_color != before_color
    else:
        assert after_color == before_color


TOOLTIP_TEXT = "Testing with Alarm State Changes, Channel Provided."
@pytest.mark.parametrize("alarm_sensitive_content, alarm_sensitive_border, tooltip", [
    (True, True, TOOLTIP_TEXT),
    (True, False, TOOLTIP_TEXT),
    (False, True, TOOLTIP_TEXT),
    (False, False, TOOLTIP_TEXT),

    (True, True, ""),
    (True, False, ""),
    (False, True, ""),
    (False, False, ""),
])
def test_label_channel_connection_changes_with_alarm(qtbot, signals, alarm_sensitive_content, alarm_sensitive_border,
                                               tooltip):
    """
    Test the widget's appearance and tooltip changes if a data channel is provided, and the is disconnected,
    and then is reconnected.

    Expectations:
    1. The widget receives the correct alarm severity when an alarm signal is emitted accordingly to the channel
       connection/disconnection
    2. The appearance changes to check for are the alarm content (alarm color), and the widget's border appearance, e.g.
       solid, transparent, etc.
    3. The alarm color and border appearance will change only if each corresponding Boolean flag is set to True
    4. The connection state is correctly set for the widget
    5. The tooltip will change when the channel is disconnected, having additional text, i.e. "PV is disconnected"
       appended to the existing text, to inform the user about the channel disconnection status. This tooltip will be
       reverted to the original content when the data channel is re-connected.
    6. The widget will be disabled during the disconnection, and become enabled again at the reconnection.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    alarm_sensitive_content : bool
        True if the widget will change color accordingly to the alarm's severity; False if not
    alarm_sensitive_border : bool
        True if the widget's border will change color and thickness accordingly to the alarm's severity; False if not
    tooltip : str
        The tooltip for the widget. This can be an empty string
    """
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    pydm_label.alarmSensitiveContent = alarm_sensitive_content
    pydm_label.alarmSensitiveBorder = alarm_sensitive_border

    pydm_label.setToolTip(tooltip)

    # Set the channel, and set the alarm severity to normal (NONE)
    pydm_label.channel = "CA://MTEST"
    alarm_severity = PyDMWidget.ALARM_NONE
    signals.new_severity_signal.connect(pydm_label.alarmSeverityChanged)
    signals.new_severity_signal.emit(alarm_severity)

    # Set the connection as enabled (True)
    signals.connection_state_signal.connect(pydm_label.connectionStateChanged)
    signals.connection_state_signal.emit(True)

    # Confirm alarm severity, style, connection state, enabling state, and tooltip
    assert pydm_label._alarm_state == alarm_severity
    assert pydm_label._connected == True
    assert pydm_label.toolTip() == tooltip
    assert pydm_label.isEnabled() == True

    # Next, disconnect the alarm, and check for the alarm severity, style, connection state, enabling state, and
    # tooltip
    alarm_severity = PyDMWidget.ALARM_DISCONNECTED

    signals.connection_state_signal.emit(False)
    assert pydm_label._alarm_state == alarm_severity
    assert pydm_label._connected == False
    assert all(i in pydm_label.toolTip() for i in (tooltip, "PV is disconnected."))
    assert pydm_label.isEnabled() == False

    # Finally, reconnect the alarm, and check for the same attributes
    signals.connection_state_signal.emit(True)

    # Confirm alarm severity, style, connection state, enabling state, and tooltip
    # TODO Set alarm_severity back to NONE
    assert pydm_label._alarm_state == PyDMWidget.ALARM_NONE
    assert pydm_label._connected == True
    assert pydm_label.toolTip() == tooltip
    assert pydm_label.isEnabled() == True


@pytest.mark.parametrize("alarm_sensitive_content, alarm_sensitive_border, tooltip", [
    (True, True, TOOLTIP_TEXT),
    (True, False, TOOLTIP_TEXT),
    (False, True, TOOLTIP_TEXT),
    (False, False, TOOLTIP_TEXT),

    (True, True, ""),
    (True, False, ""),
    (False, True, ""),
    (False, False, ""),
])
def test_label_connection_changes_with_alarm_and_no_channel(qtbot, signals, alarm_sensitive_content, alarm_sensitive_border,
                                                      tooltip):
    """
    Test the widget's appearance and tooltip changes if a data channel is not provided, and the connection is not
    available, and available again.

    Expectations:
    1. The widget receives the correct alarm severity when an alarm signal is emitted accordingly to the channel
       connection/disconnection
    2. The appearance changes to check for are the alarm content (alarm color), and the widget's border appearance, e.g.
       solid, transparent, etc.
    3. The alarm color and border appearance will change only if each corresponding Boolean flag is set to True
    4. The connection state is correctly set for the widget
    5. The tooltip will not change throughout the sequence of the connection events.
    6. The widget will remain enabled throughout the sequence of the connection events.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    alarm_sensitive_content : bool
        True if the widget will change color accordingly to the alarm's severity; False if not
    alarm_sensitive_border : bool
        True if the widget's border will change color and thickness accordingly to the alarm's severity; False if not
    tooltip : str
        The tooltip for the widget. This can be an empty string
    """
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    pydm_label.alarmSensitiveContent = alarm_sensitive_content
    pydm_label.alarmSensitiveBorder = alarm_sensitive_border
    pydm_label.setToolTip(tooltip)

    # Do not the channel, but set the alarm severity to normal (NONE)
    pydm_label.channel = None
    signals.new_severity_signal.connect(pydm_label.alarmSeverityChanged)
    signals.new_severity_signal.emit(PyDMWidget.ALARM_NONE)

    # Set the connection as enabled (True)
    signals.connection_state_signal.connect(pydm_label.connectionStateChanged)

    blocker = qtbot.waitSignal(signals.connection_state_signal, timeout=1000)
    signals.connection_state_signal.emit(True)
    blocker.wait()

    # Confirm alarm severity, style, connection state, enabling state, and tooltip
    assert pydm_label._alarm_state == PyDMWidget.ALARM_NONE
    assert pydm_label._connected == True
    assert pydm_label.toolTip() == tooltip
    assert pydm_label.isEnabled() == True

    # Next, disconnect the alarm, and check for the alarm severity, style, connection state, enabling state, and
    # tooltip
    signals.connection_state_signal.emit(False)
    blocker.wait()
    assert pydm_label._alarm_state == PyDMWidget.ALARM_NONE

    assert pydm_label._connected == False
    assert pydm_label.toolTip() == tooltip
    assert pydm_label.isEnabled() == True

    # Finally, reconnect the alarm, and check for the same attributes
    signals.connection_state_signal.emit(True)
    blocker.wait()

    # Confirm alarm severity, style, connection state, enabling state, and tooltip
    assert pydm_label._alarm_state == PyDMWidget.ALARM_NONE
    assert pydm_label._connected == True
    assert pydm_label.toolTip() == tooltip
    assert pydm_label.isEnabled() == True


# --------------------
# NEGATIVE TEST CASES
# --------------------

@pytest.mark.parametrize("value, display_format, expected", [
    (np.array([-1, -2]), DisplayFormat.String, "Could not decode"),
    (np.array([0xfffe, 0xffff]), DisplayFormat.String, "Could not decode"),
    ("aaa", DisplayFormat.Exponential, "Could not display value 'aaa' using displayFormat 'Exponential'"),
    ("zzz", DisplayFormat.Hex, "Could not display value 'zzz' using displayFormat 'Hex'"),
    ("zzz", DisplayFormat.Binary, "Could not display value 'zzz' using displayFormat 'Binary'"),
])
def test_value_changed_incorrect_display_format(qtbot, signals, caplog, value, display_format, expected):
    """
    Test the widget's handling of incorrect provided values.

    Expectations:
    The correct error message is output in stderr.
    
    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    caplog : fixture
        The fixture to capture log outputs
    value : ndarray, str
        The value to be displayed by the widget
    display_format : int
        The incorrect format type for the provided value
    expected : str
        The expected error message in stderr
    """
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    signals.new_value_signal[type(value)].connect(pydm_label.channelValueChanged)
    signals.new_value_signal[type(value)].emit(value)
    pydm_label.displayFormat = display_format

    # Make sure logging capture the error, and have the correct error message
    for record in caplog.records:
        assert record.levelno == logging.ERROR
    assert expected in caplog.text


@pytest.mark.parametrize("value, selected_index, expected", [
    (("ON", "OFF"), 3, "**INVALID**"),
])
def test_enum_strings_changed_incorrect_index(qtbot, signals, value, selected_index, expected):
    """
    Test the widget's handling of incorrect provided enum string index.

    Expectations:
    The widget will display an error message to notify the user of the invalid index choice.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    value : tuple
        A set of enum strings for the user to choose from
    selected_index : int
        The incorrect (out-of-bound) index from the enum string tuple chosen by the user
    expected : int
        The expected text displayed by the widget to notify the user of the incorrect choice index
    """
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    signals.new_value_signal[type(selected_index)].connect(pydm_label.channelValueChanged)
    signals.new_value_signal[type(selected_index)].emit(selected_index)

    signals.enum_strings_signal.connect(pydm_label.enumStringsChanged)
    signals.enum_strings_signal.emit(value)
    pydm_label.displayFormat = DisplayFormat.String

    assert pydm_label.value == selected_index
    assert pydm_label.text() == expected
    assert pydm_label.displayFormat == DisplayFormat.String
