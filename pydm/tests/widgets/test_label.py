# coding: utf-8
# Unit Tests for the PyDMLabel Widget


import os
import pytest
from numpy import ndarray

from ...PyQt.QtCore import QObject, pyqtSignal
from ...utilities import is_pydm_app
from ...widgets.label import PyDMLabel
from ...widgets.base import PyDMWidget
from pydm.widgets.display_format import parse_value_for_display, DisplayFormat

current_dir = os.path.abspath(os.path.dirname(__file__))


# --------------------
# POSITIVE TEST CASES
# --------------------

def test_construct(qtbot):
    """
    Test the basic instantiation of the widget.
    Invariance:
    The widget was created with the following default settings:
    1. DisplayFormat is Default
    2. String encoding is the same as that specified in the PyDM App, or UTF-8
    :param qtbot: pytest-qt window for widget testing
    :type: qtbot
    """
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    display_format_type = pydm_label.displayFormat
    assert (display_format_type == pydm_label.DisplayFormat.Default)
    assert(pydm_label._string_encoding == pydm_label.app.get_string_encoding()
           if is_pydm_app() else "utf_8")


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
    Invariance:
    The following settings are in place after the value changed signal is emitted:
    1. The value displayed by the widget is the new value
    2. The value format maintained by the widget the correct format for the new value
    :param qtbot: pytest-qt window for widget testing
    :type: qtbot
    :param signals: The signals fixture, which provides access signals to be bound to the appropriate slots.
    :type: ConnectionSignals
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
    assert(displayed_value == expected_value)
    assert (pydm_label.displayFormat == display_format)


@pytest.mark.parametrize("value, selected_index, expected", [
    (("ON", "OFF"), 0, "ON"),
    (("ON", "OFF"), 1, "OFF"),
])
def test_enum_strings_changed(qtbot, signals, value, selected_index, expected):
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    signals.new_value_signal[type(selected_index)].connect(pydm_label.channelValueChanged)
    signals.new_value_signal[type(selected_index)].emit(selected_index)

    signals.enum_strings_signal.connect(pydm_label.enumStringsChanged)
    signals.enum_strings_signal.emit(value)
    pydm_label.displayFormat = DisplayFormat.String

    assert(pydm_label.value == selected_index)
    assert(pydm_label.text() == expected)
    assert (pydm_label.displayFormat == DisplayFormat.String)


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
def test_label_alarms(qtbot, signals, test_alarm_style_sheet_map, alarm_severity, alarm_sensitive_content,
                      alarm_sensitive_border):
    """
    Test the widget's appearance changes according to changes in alarm severity.
    Invariance:
    1. The widget receives the correct alarm severity
    2. The appearance changes to check for are the alarm content (alarm color), and the widget's border appearance, e.g.
       solid, transparent, etc.
    3. The alarm color and border appearance will change only if each corresponding Boolean flag is set to True

    We use the style dictionary above as the guidelines to check whether the alarm color and widget's border appearance
    are correct.

    :param qtbot: pytest-qt window for widget testing
    :type: qtbot
    :param signals: The signals fixture, which provides access signals to be bound to the appropriate slots.
    :type: ConnectionSignals
    :para test_alarm_style_sheet_map: The alarm style sheet map fixture, which provides a style sheet inventory to
        to compare against the widget's changing style
    :type: dict
    :param alarm_severity: The severity of an alarm (NONE, MINOR, MAJOR, INVALID, or DISCONNECTED)
    :type: int
    :param alarm_sensitive_content: Essentially an HTML-compliant hexadecimal color code
    :type: str
    :param alarm_sensitive_border: A CSS-style dictionary of the appearance settings of the widget's border
    :type: dict
    """
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    pydm_label.alarmSensitiveContent = alarm_sensitive_content
    pydm_label.alarmSensitiveBorder = alarm_sensitive_border
    alarm_flags = (PyDMWidget.ALARM_CONTENT * alarm_sensitive_content) | \
                  (PyDMWidget.ALARM_BORDER * alarm_sensitive_border)

    signals.new_severity_signal.connect(pydm_label.alarmSeverityChanged)
    signals.new_severity_signal.emit(alarm_severity)

    assert(pydm_label._alarm_state == alarm_severity)
    expected_style = dict(test_alarm_style_sheet_map[alarm_flags][alarm_severity])
    assert(pydm_label._style == expected_style)


@pytest.mark.parametrize("alarm_sensitive_content, alarm_sensitive_border", [
    (True, True),
    #(True, False),
    #(False, True),
    #(False, False),
])
def test_alarm_state_changes(qtbot, signals, test_alarm_style_sheet_map, alarm_sensitive_content,
                             alarm_sensitive_border):
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    pydm_label.alarmSensitiveContent = alarm_sensitive_content
    pydm_label.alarmSensitiveBorder = alarm_sensitive_border
    alarm_flags = (PyDMWidget.ALARM_CONTENT * alarm_sensitive_content) | \
                  (PyDMWidget.ALARM_BORDER * alarm_sensitive_border)

    # Set the channel, and set the alarm severity to normal (NONE)
    pydm_label.channel = "CA://MTEST"
    alarm_severity = PyDMWidget.ALARM_NONE
    signals.new_severity_signal.connect(pydm_label.alarmSeverityChanged)
    signals.new_severity_signal.emit(alarm_severity)

    # Set the connection as enabled (True)
    signals.connection_state_signal.connect(pydm_label.connectionStateChanged)
    signals.connection_state_signal.emit(True)

    # Confirm alarm severity, style, connection state, and tool tip
    assert (pydm_label._alarm_state == alarm_severity)
    expected_style = dict(test_alarm_style_sheet_map[alarm_flags][alarm_severity])
    assert (pydm_label._style == expected_style)
    assert(pydm_label._connected == True)

    # Next, disconnect the alarm, and check for the alarm severity, style, connection state, and tool tip
    alarm_severity = PyDMWidget.ALARM_DISCONNECTED

    signals.connection_state_signal.connect(pydm_label.connectionStateChanged)
    signals.connection_state_signal.emit(False)
    assert (pydm_label._alarm_state == alarm_severity)
    expected_style = dict(test_alarm_style_sheet_map[alarm_flags][alarm_severity])
    assert (pydm_label._style == expected_style)
    assert(pydm_label._connected == False)

    # Finally, reconnect the alarm, and check for the same attributes
    signals.connection_state_signal.connect(pydm_label.connectionStateChanged)
    signals.connection_state_signal.emit(True)

    # Confirm alarm severity, style, connection state, and tool tip
    assert (pydm_label._alarm_state == alarm_severity)
    expected_style = dict(test_alarm_style_sheet_map[alarm_flags][alarm_severity])
    assert (pydm_label._style == expected_style)
    assert (pydm_label._connected == True)


# --------------------
# NEGATIVE TEST CASES
# --------------------

@pytest.mark.parametrize("value, display_format, expected", [
    (ndarray([65, 66, 67, 68]), DisplayFormat.String, "Could not decode"),
    ("aaa", DisplayFormat.Exponential, "Could not display in 'Exponential'"),
    ("zzz", DisplayFormat.Hex, "Could not display in 'Hex'"),
    ("zzz", DisplayFormat.Binary, "Could not display in 'Binary'"),
])
def test_value_changed_incorrect_display_format(qtbot, signals, capfd, value, display_format, expected):
    """
    Test the widget's handling of incorrect provided values.
    Invariance:
    The following settings are in place after the value changed signal is emitted:
    1. The value displayed by the widget is the new value
    2. The value format maintained by the widget the correct format for the new value
    :param qtbot: pytest-qt window for widget testing
    :type: qtbot
    :param signals: The signals fixture, which provides access signals to be bound to the appropriate slots.
    :type: ConnectionSignals
    :param capfd: stderr capturing fixture
    :type: fixture
    :param value: The data to be formatted
    :type: int, float, hex, bin, or str
    :param display_format: The format type for the provided value
    :type: int
    :param expected: The expected error message to be streamed to stderr
    :type: str
    """
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    signals.new_value_signal[type(value)].connect(pydm_label.channelValueChanged)
    signals.new_value_signal[type(value)].emit(value)
    pydm_label.displayFormat = display_format

    out, err = capfd.readouterr()
    assert expected in err


@pytest.mark.parametrize("value, selected_index, expected", [
    (("ON", "OFF"), 3, "**INVALID**"),
])
def test_enum_strings_changed_incorrect_index(qtbot, signals, value, selected_index, expected):
    """
    Test the widget's handling of incorrect provided enum string index.
    :param qtbot: pytest-qt window for widget testing
    :type: qtbot
    :param signals: The signals fixture, which provides access signals to be bound to the appropriate slots.
    :type: ConnectionSignals
    :param value: The enum strings as available options for the widget to display to the user
    :type: tuple
    :param selected_index: The user-selected index for the enum string tuple
    :type: int
    :param expected: The expected selected enum string or error message to be displayed by the widget
    :type: str
    """
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    signals.new_value_signal[type(selected_index)].connect(pydm_label.channelValueChanged)
    signals.new_value_signal[type(selected_index)].emit(selected_index)

    signals.enum_strings_signal.connect(pydm_label.enumStringsChanged)
    signals.enum_strings_signal.emit(value)
    pydm_label.displayFormat = DisplayFormat.String

    assert(pydm_label.value == selected_index)
    assert(pydm_label.text() == expected)
    assert (pydm_label.displayFormat == DisplayFormat.String)
