# coding: utf-8
# Fixtures for PyDM Unit Tests

import pytest
from pytestqt.qt_compat import qt_api

import numpy as np
import tempfile
import logging

from ..PyQt.QtCore import QObject, pyqtSignal, pyqtSlot
from ..PyQt.QtGui import QColor

from ..application import PyDMApplication
from ..widgets.base import PyDMWidget


pytest_plugins = 'pytester'


logger = logging.getLogger(__name__)
_, file_path = tempfile.mkstemp(suffix=".log")
handler = logging.FileHandler(file_path)
logger.addHandler(handler)


"""
PyDMWidget Style Sheet

This serves as the invariance for the widget's appearance, depending on the alarm type, and the content and border
appearances.

In case of style assertion failures, check if the widget styles in the main PyDM code have changed, and whether those
changes are as intended. If they are, update the reference style sheet below accordingly.
"""
NO_ALARM = 0x0 #Stylesheet for widgets which don't react to alarm status
ALARM_CONTENT = 0x1 #Stylesheet for the 'content' of widgets (text, usually).
ALARM_BORDER = 0x2 #Stylesheet for the border of widgets.
ALARM_INDICATOR = 0x4 #Stylesheet for 'indicator' ornaments, where you want the "OK" status to actually have a color.

ALARM_NONE = 0
ALARM_MINOR = 1
ALARM_MAJOR = 2
ALARM_INVALID = 3
ALARM_DISCONNECTED = 4

GREEN_ALARM = "#00EB00"
YELLOW_ALARM = "#EBEB00"
RED_ALARM = "#EB0000"
MAGENTA_ALARM = "#EB00EB"
WHITE_ALARM = "#EBEBEB"

# We put all this in a big dictionary to try to avoid constantly
# allocating and deallocating new stylesheet strings.
alarm_style_sheet_map = {
    NO_ALARM: {
        ALARM_NONE: {},
        ALARM_MINOR: {},
        ALARM_MAJOR: {},
        ALARM_INVALID: {},
        ALARM_DISCONNECTED: {}
    },
    ALARM_CONTENT: {
        ALARM_NONE: {"color": "black"},
        ALARM_MINOR: {"color": YELLOW_ALARM},
        ALARM_MAJOR: {"color": RED_ALARM},
        ALARM_INVALID: {"color": MAGENTA_ALARM},
        ALARM_DISCONNECTED: {"color": WHITE_ALARM}
    },
    ALARM_INDICATOR: {
        ALARM_NONE: {"color": GREEN_ALARM},
        ALARM_MINOR: {"color": YELLOW_ALARM},
        ALARM_MAJOR: {"color": RED_ALARM},
        ALARM_INVALID: {"color": MAGENTA_ALARM},
        ALARM_DISCONNECTED: {"color": WHITE_ALARM}
    },
    ALARM_BORDER: {
        ALARM_NONE: {"border": "2px solid transparent"},
        ALARM_MINOR: {"border": "2px solid " + YELLOW_ALARM},
        ALARM_MAJOR: {"border": "2px solid " + RED_ALARM},
        ALARM_INVALID: {"border": "2px solid " + MAGENTA_ALARM},
        ALARM_DISCONNECTED: {"border": "2px solid " + WHITE_ALARM}
    },
    ALARM_CONTENT | ALARM_BORDER: {
        ALARM_NONE: {"color": "black", "border": "2px solid transparent"},
        ALARM_MINOR: {"color": YELLOW_ALARM, "border": "2px solid " + YELLOW_ALARM},
        ALARM_MAJOR: {"color": RED_ALARM, "border": "2px solid " + RED_ALARM},
        ALARM_INVALID: {"color": MAGENTA_ALARM, "border": "2px solid " + MAGENTA_ALARM},
        ALARM_DISCONNECTED: {"color": WHITE_ALARM, "border": "2px solid " + WHITE_ALARM}
    }
}


local_connection_status_color_map = {
        False: QColor(0, 0, 0),
        True: QColor(0, 0, 0,)
    }

@pytest.fixture(scope="session")
def test_alarm_style_sheet_map():
    return alarm_style_sheet_map


@pytest.fixture(scope="session")
def test_local_connection_status_color_map():
    return local_connection_status_color_map


class ConnectionSignals(QObject):
    """
    An assortment of signals, to which a unit test can choose from and bind an appropriate slot
    """
    new_value_signal = pyqtSignal([float], [int], [str], [np.ndarray])
    connection_state_signal = pyqtSignal(bool)
    new_severity_signal = pyqtSignal(int)
    write_access_signal = pyqtSignal(bool)
    enum_strings_signal = pyqtSignal(tuple)
    internal_slider_moved = pyqtSignal(int)
    internal_slider_clicked = pyqtSignal()
    send_value_signal = pyqtSignal([int], [float], [str], [bool], [np.ndarray])
    unit_signal = pyqtSignal(str)
    prec_signal = pyqtSignal(int)
    upper_ctrl_limit_signal = pyqtSignal([float])
    lower_ctrl_limit_signal = pyqtSignal([float])


    def __init__(self):
        super(ConnectionSignals, self).__init__()
        self._value = None

    def reset(self):
        self._value = None

    @property
    def value(self):
        """
        The property to retrieve the value received from a PyDM widget.

        Returns
        -------
        The value received from a PyDM widget.
        """
        return self._value

    @pyqtSlot(int)
    @pyqtSlot(float)
    @pyqtSlot(str)
    @pyqtSlot(np.ndarray)
    def receiveValue(self, val):
        """
        The slot to receive the value from a PyDM widget.

        Parameters
        ----------
        val : int, float, str, ndarray
            The value received from a PyDM widget
        """
        self._value = val


@pytest.fixture(scope="function")
def signals():
    """
    Wraparound signal collection to work as a fixture for all unit tests.
    This fixture has a function scope to ensure we have a fresh fixture, i.e. a new set of signals, for every unit
    test run.

    Returns
    -------
    A collection of signals to bind to slots.
    """
    return ConnectionSignals()


@pytest.yield_fixture(scope='session')
def qapp(qapp_args):
    """
    Fixture for a PyDMApplication app instance.

    Parameters
    ----------
    qapp_args: Arguments for the QApp.

    Returns
    -------
    An instance of PyDMApplication.
    """
    app = qt_api.QApplication.instance()
    if app is None or not isinstance(app, PyDMApplication):
        global _qapp_instance
        _qapp_instance = PyDMApplication(use_main_window=False, *qapp_args)
        yield _qapp_instance
    else:
        yield app  # pragma: no cover
