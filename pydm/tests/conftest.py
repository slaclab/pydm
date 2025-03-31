# coding: utf-8
# Fixtures for PyDM Unit Tests

import numpy as np
import pytest
import tempfile
import logging

from qtpy.QtCore import QObject, Signal, Slot
from pydm.application import PyDMApplication
from pydm.main_window import PyDMMainWindow
from pydm.data_plugins import PyDMPlugin, add_plugin

logger = logging.getLogger(__name__)
_, file_path = tempfile.mkstemp(suffix=".log")
handler = logging.FileHandler(file_path)
logger.addHandler(handler)


def mock_method(*args, **kwargs):
    pass


PyDMMainWindow.closeEvent = mock_method


class ConnectionSignals(QObject):
    """
    An assortment of signals, to which a unit test can choose from and bind an appropriate slot
    """

    new_value_signal = Signal((float,), (int,), (str,), (np.ndarray,))
    connection_state_signal = Signal(bool)
    new_severity_signal = Signal(int)
    write_access_signal = Signal(bool)
    enum_strings_signal = Signal(tuple)
    internal_slider_moved = Signal(int)
    internal_slider_clicked = Signal()
    send_value_signal = Signal((int,), (float,), (str,), (bool,), (np.ndarray,))
    unit_signal = Signal(str)
    prec_signal = Signal(int)
    upper_ctrl_limit_signal = Signal((float,))
    lower_ctrl_limit_signal = Signal((float,))
    upper_alarm_limit_signal = Signal((float,))
    lower_alarm_limit_signal = Signal((float,))
    upper_warning_limit_signal = Signal((float,))
    lower_warning_limit_signal = Signal((float,))

    def __init__(self):
        super().__init__()
        self._value = None
        self._received_values = {}

    def reset(self):
        self._value = None
        self._received_values.clear()

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

    @Slot(object)
    def receive_value(self, name: str, value: object) -> None:
        """
        Slot for receiving a value from a signal.

        Parameters
        ----------
        name : str
            Name to associate with the value received
        value : object
            The value that was sent by the signal
        """
        self._received_values[name] = value

    def __getitem__(self, name):
        return self._received_values[name]


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


@pytest.fixture(scope="session")
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
    # Don't pass along the default app name we get from pytest-qt otherwise PyDM will misinterpret it as a ui file name
    if "pytest-qt-qapp" == qapp_args[0]:
        qapp_args.remove("pytest-qt-qapp")

    yield PyDMApplication(use_main_window=False, *qapp_args)


@pytest.fixture(scope="session")
def test_plugin():
    # Create test PyDMPlugin with mock protocol
    test_plug = PyDMPlugin
    test_plug.protocol = "tst"
    add_plugin(test_plug)
    return test_plug
