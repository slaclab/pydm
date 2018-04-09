# coding: utf-8
# Fixtures for PyDM Unit Tests

import pytest
from pytestqt.qt_compat import qt_api

from numpy import ndarray
import tempfile
import logging

from ..PyQt.QtCore import QObject, pyqtSignal, pyqtSlot

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
        super(ConnectionSignals, self).__init__()
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
    @pyqtSlot(ndarray)
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
        _qapp_instance = PyDMApplication(*qapp_args)
        yield _qapp_instance
    else:
        yield app  # pragma: no cover
