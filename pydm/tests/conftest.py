# coding: utf-8
# Fixtures for PyDM Unit Tests

import pytest
from numpy import ndarray

from ..PyQt.QtCore import QObject, pyqtSignal, pyqtSlot
from ..widgets.base import PyDMWidget

pytest_plugins = 'pytester'


"""
PyDMLabel Style Sheet

This serves as the invariance for the label widget's appearance, depending on the alarm type, and the content and border
appearances.

In case of style assertion failures, check if the widget styles in the main PyDM code have changed, and whether those
changes are as intended. If they are, update the reference style sheet below accordingly.
"""
alarm_style_sheet_map = {
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


@pytest.fixture(scope="session")
def test_alarm_style_sheet_map():
    return alarm_style_sheet_map


class ConnectionSignals(QObject):
    """
    An assortment of signals, to which a unit test can choose from and bind an appropriate slot
    """
    new_value_signal = pyqtSignal([float], [int], [str], [ndarray])
    connection_state_signal = pyqtSignal(bool)
    new_severity_signal = pyqtSignal(int)
    write_access_signal = pyqtSignal(bool)
    enum_strings_signal = pyqtSignal(tuple)
    unit_signal = pyqtSignal(str)
    prec_signal = pyqtSignal(int)
    upper_ctrl_limit_signal = pyqtSignal([float], [int])
    lower_ctrl_limit_signal = pyqtSignal([float], [int])

    def __init__(self):
        super().__init__()
        self._value = None

    @property
    def value(self):
        return self._value

    @pyqtSlot(int)
    @pyqtSlot(float)
    @pyqtSlot(str)
    @pyqtSlot(ndarray)
    def receiveValue(self, val):
        """
        Slot to receive the value from a PyDM widget
        :param val: The value from a PyDM widget
        """
        self._value = val


@pytest.fixture(scope="function")
def signals():
    """Wraparound signal collection to work as a fixture for all unit tests.
       This fixture has a function scope to ensure we have a fresh fixture, i.e. a new set of signals, for every
       unit test run.
       :return: A collection of signals to bind to slots.
       :rtype: ConnectionSignals
    """
    return ConnectionSignals()
