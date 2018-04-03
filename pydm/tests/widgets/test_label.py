# coding: utf-8

import os
import pytest

from ...PyQt.QtCore import QObject, pyqtSignal
from ...utilities import is_pydm_app
from ...widgets.label import PyDMLabel
from ...widgets.base import PyDMWidget
from pydm.widgets.display_format import parse_value_for_display, DisplayFormat

current_dir = os.path.abspath(os.path.dirname(__file__))


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


class SignalTrigger(QObject):
    change_signal = pyqtSignal([int], [str])

    def __init__(self, signal_handler):
        super().__init__()
        self.change_signal[str].connect(signal_handler)

    def emit(self, value):
        self.change_signal.emit(value)


@pytest.mark.parametrize("value, display_format", [
    ("abc", DisplayFormat.Default),
    # (123, DisplayFormat.Default),
    # (0b100, DisplayFormat.Default),
    # (0x1FF, DisplayFormat.Default),
    #
    # ("abc", DisplayFormat.String),
    # ("123", DisplayFormat.String),
    # ("0b100", DisplayFormat.String),
    # ("0x1FF", DisplayFormat.String),
    #
    # (123, DisplayFormat.Decimal),
    # (123.45, DisplayFormat.Decimal),
    # (0b100, DisplayFormat.Decimal),
    # (0x1FF, DisplayFormat.Decimal),
    #
    # (123, DisplayFormat.Exponential),
    # (3.000e-02, DisplayFormat.Exponential),
    # (0b100, DisplayFormat.Exponential),
    # (0x1FF, DisplayFormat.Exponential),
    #
    # (123, DisplayFormat.Hex),
    # (3.000e-02, DisplayFormat.Hex),
    # (0b100, DisplayFormat.Hex),
    # (0x1FF, DisplayFormat.Hex),
    #
    # (123, DisplayFormat.Binary),
    # (3.000e-02, DisplayFormat.Binary),
    # (0b100, DisplayFormat.Binary),
    # (0x1FF, DisplayFormat.Binary),
])
def test_value_changed(qtbot, value, display_format):
    """
    Test the widget's handling of the value changed event.
    Invariance:
    The following settings are in place after the value changed signal is emitted:
    1. The value displayed by the widget is the new value
    2. The value format maintained by the widget the correct format for the new value
    :param qtbot: pytest-qt window for widget testing
    :type: qtbot
    """
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    trigger = SignalTrigger(pydm_label.channelValueChanged)
    v = str()
    v = value
    trigger.emit(v)
    pydm_label.displayFormat = display_format

    displayed_value = parse_value_for_display(value=pydm_label.value, precision=1,
                                              display_format_type=pydm_label.displayFormat, widget=pydm_label)
    expected_value = parse_value_for_display(value=value, precision=1,
                                             display_format_type=display_format, widget=pydm_label)
    assert(displayed_value == expected_value)
    assert (pydm_label.displayFormat == display_format)


test_alarm_style_sheet_map = {
    PyDMWidget.NO_ALARM: {
        PyDMWidget.ALARM_NONE: {},
        PyDMWidget.ALARM_MINOR: {},
        PyDMWidget.ALARM_MAJOR: {},
        PyDMWidget.ALARM_INVALID: {},
        PyDMWidget.ALARM_DISCONNECTED: {}
    },
    PyDMWidget.ALARM_CONTENT: {
        PyDMWidget.ALARM_NONE: {"color": "black"},
        PyDMWidget.ALARM_MINOR: {"color": PyDMWidget.YELLOW_ALARM},
        PyDMWidget.ALARM_MAJOR: {"color": PyDMWidget.RED_ALARM},
        PyDMWidget.ALARM_INVALID: {"color": PyDMWidget.MAGENTA_ALARM},
        PyDMWidget.ALARM_DISCONNECTED: {"color": PyDMWidget.WHITE_ALARM}
    },
    PyDMWidget.ALARM_INDICATOR: {
        PyDMWidget.ALARM_NONE: {"color": PyDMWidget.GREEN_ALARM},
        PyDMWidget.ALARM_MINOR: {"color": PyDMWidget.YELLOW_ALARM},
        PyDMWidget.ALARM_MAJOR: {"color": PyDMWidget.RED_ALARM},
        PyDMWidget.ALARM_INVALID: {"color": PyDMWidget.MAGENTA_ALARM},
        PyDMWidget.ALARM_DISCONNECTED: {"color": PyDMWidget.WHITE_ALARM}
    },
    PyDMWidget.ALARM_BORDER: {
        PyDMWidget.ALARM_NONE: {"border": "2px solid transparent"},
        PyDMWidget.ALARM_MINOR: {"border": "2px solid " + PyDMWidget.YELLOW_ALARM},
        PyDMWidget.ALARM_MAJOR: {"border": "2px solid " + PyDMWidget.RED_ALARM},
        PyDMWidget.ALARM_INVALID: {"border": "2px solid " + PyDMWidget.MAGENTA_ALARM},
        PyDMWidget.ALARM_DISCONNECTED: {"border": "2px solid " + PyDMWidget.WHITE_ALARM}
    },
    PyDMWidget.ALARM_CONTENT | PyDMWidget.ALARM_BORDER: {
        PyDMWidget.ALARM_NONE: {"color": "black", "border": "2px solid transparent"},
        PyDMWidget.ALARM_MINOR: {"color": PyDMWidget.YELLOW_ALARM, "border": "2px solid " + PyDMWidget.YELLOW_ALARM},
        PyDMWidget.ALARM_MAJOR: {"color": PyDMWidget.RED_ALARM, "border": "2px solid " + PyDMWidget.RED_ALARM},
        PyDMWidget.ALARM_INVALID: {
            "color": PyDMWidget.MAGENTA_ALARM, "border": "2px solid " + PyDMWidget.MAGENTA_ALARM},
        PyDMWidget.ALARM_DISCONNECTED: {
            "color": PyDMWidget.WHITE_ALARM, "border": "2px solid " + PyDMWidget.WHITE_ALARM}
    }
}


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
def test_label_alarms(qtbot, alarm_severity, alarm_sensitive_content, alarm_sensitive_border):
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    pydm_label.alarmSensitiveContent = alarm_sensitive_content
    pydm_label.alarmSensitiveBorder = alarm_sensitive_border
    alarm_flags = (PyDMWidget.ALARM_CONTENT * alarm_sensitive_content) | \
                  (PyDMWidget.ALARM_BORDER * alarm_sensitive_border)

    trigger = SignalTrigger(pydm_label.alarmSeverityChanged)
    trigger.emit(alarm_severity)

    assert(pydm_label._alarm_state == alarm_severity)
    expected_style = dict(test_alarm_style_sheet_map[alarm_flags][alarm_severity])
    assert(pydm_label._style == expected_style)
