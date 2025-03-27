import time
import functools
import pydm.data_plugins.epics_plugins.psp_plugin_component
from pydm.data_plugins.epics_plugins.psp_plugin_component import Connection
from pydm.tests.conftest import ConnectionSignals
from pydm.widgets.channel import PyDMChannel
from pytest import MonkeyPatch


# Note: This test cannot be run on any Windows OS as a build of PyCA is not available there


class MockPV:
    """A simple mock of the psp Pv object"""

    def __init__(self):
        self.data = {}

    @staticmethod
    def severity(self):
        return None

    def timestamp(self):
        secs = time.time()
        nanos = time.time_ns()
        return secs, nanos


def test_update_ctrl_vars(monkeypatch: MonkeyPatch, signals: ConnectionSignals):
    """Invoke our callback for updating the control values for a PV as if we had a monitor on it. Verify
    that the signals sent are received as expected.
    """
    # Initialize a mock channel and connection for testing
    mock_channel = PyDMChannel()
    mock_pv = MockPV()
    monkeypatch.setattr(
        pydm.data_plugins.epics_plugins.psp_plugin_component, "setup_pv", lambda *args, **kwargs: mock_pv
    )
    monkeypatch.setattr(Connection, "add_listener", lambda *args, **kwargs: None)
    psp_connection = Connection(mock_channel, "Test:PV:1")
    psp_connection.count = 1

    # Create some control values for our PV as if we had received them using psp
    mock_pv.data["precision"] = 3
    mock_pv.data["units"] = "mV"
    mock_pv.data["ctrl_llim"] = 5.5
    mock_pv.data["ctrl_hlim"] = 30.5
    mock_pv.data["alarm_hlim"] = 28
    mock_pv.data["alarm_llim"] = 8
    mock_pv.data["warn_hlim"] = 22.5
    mock_pv.data["warn_llim"] = 10.25

    # Connect the signals to a slot that allows us to inspect the value received
    psp_connection.new_value_signal[float].connect(lambda: None)  # Only testing control variables here
    psp_connection.prec_signal.connect(functools.partial(signals.receive_value, "precision"))
    psp_connection.unit_signal.connect(functools.partial(signals.receive_value, "units"))
    psp_connection.lower_ctrl_limit_signal.connect(functools.partial(signals.receive_value, "ctrl_llim"))
    psp_connection.upper_ctrl_limit_signal.connect(functools.partial(signals.receive_value, "ctrl_hlim"))
    psp_connection.upper_alarm_limit_signal.connect(functools.partial(signals.receive_value, "alarm_hlim"))
    psp_connection.lower_alarm_limit_signal.connect(functools.partial(signals.receive_value, "alarm_llim"))
    psp_connection.upper_warning_limit_signal.connect(functools.partial(signals.receive_value, "warn_hlim"))
    psp_connection.lower_warning_limit_signal.connect(functools.partial(signals.receive_value, "warn_llim"))

    psp_connection.python_type = float
    psp_connection.send_new_value(10.0)

    # Verify all the signals were emitted as expected
    assert signals["precision"] == 3
    assert signals["units"] == "mV"
    assert signals["ctrl_llim"] == 5.5
    assert signals["ctrl_hlim"] == 30.5
    assert signals["alarm_hlim"] == 28
    assert signals["alarm_llim"] == 8
    assert signals["warn_hlim"] == 22.5
    assert signals["warn_llim"] == 10.25
