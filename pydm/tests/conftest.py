# coding: utf-8
# Fixtures for PyDM Unit Tests

import pytest
from pytestqt.qt_compat import qt_api

import numpy as np
import tempfile
import logging

from qtpy.QtCore import QObject, Signal, Slot
from pydm.application import PyDMApplication
from pydm.data_plugins import PyDMPlugin, add_plugin

logger = logging.getLogger(__name__)
_, file_path = tempfile.mkstemp(suffix=".log")
handler = logging.FileHandler(file_path)
logger.addHandler(handler)


class ConnectionSignals(QObject):
    """
    An assortment of signals, to which a unit test can choose from and bind an appropriate slot
    """
    new_value_signal = Signal([float], [int], [str], [np.ndarray])
    connection_state_signal = Signal(bool)
    new_severity_signal = Signal(int)
    write_access_signal = Signal(bool)
    enum_strings_signal = Signal(tuple)
    internal_slider_moved = Signal(int)
    internal_slider_clicked = Signal()
    send_value_signal = Signal([int], [float], [str], [bool], [np.ndarray])
    unit_signal = Signal(str)
    prec_signal = Signal(int)
    upper_ctrl_limit_signal = Signal([float])
    lower_ctrl_limit_signal = Signal([float])

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

    @Slot(int)
    @Slot(float)
    @Slot(str)
    @Slot(np.ndarray)
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


@pytest.fixture(scope='session')
def test_plugin():
    # Create test PyDMPlugin with mock protocol
    test_plug = PyDMPlugin
    test_plug.protocol = 'tst'
    add_plugin(test_plug)
    return test_plug
