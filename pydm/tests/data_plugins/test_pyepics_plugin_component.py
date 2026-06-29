import pytest
from concurrent.futures import ThreadPoolExecutor

from pydm.data_plugins.epics_plugins.pyepics_plugin_component import Connection, PyEPICSPlugin
from pydm.tests.conftest import ConnectionSignals
from pydm.widgets.channel import PyDMChannel


@pytest.fixture(autouse=True)
def ensure_thread_pool():
    # Connection.__init__ submits work to the class-level PyEPICSPlugin.thread_pool, which is
    # normally created when the plugin itself is instantiated. These tests build a Connection
    # directly, so initialize the pool here to keep them independent of test ordering.
    created_here = PyEPICSPlugin.thread_pool is None
    if created_here:
        PyEPICSPlugin.thread_pool = ThreadPoolExecutor()
    try:
        yield
    finally:
        # Only tear down a pool this fixture created, so we don't leak worker threads or
        # class-level state into other tests.
        if created_here:
            PyEPICSPlugin.thread_pool.shutdown(wait=False, cancel_futures=True)
            PyEPICSPlugin.thread_pool = None


def test_update_ctrl_vars(signals: ConnectionSignals):
    """Invoke our callback for updating the control values for a PV as if we had a monitor on it. Verify
    that the signals sent are received as expected.
    """
    values_received = []
    mock_channel = PyDMChannel()
    mock_pyepics_connection = Connection(mock_channel, "Test:PV:1")
    mock_pyepics_connection.upper_alarm_limit_signal.connect(lambda x: values_received.append(x))
    mock_pyepics_connection.lower_alarm_limit_signal.connect(lambda x: values_received.append(x))
    mock_pyepics_connection.lower_warning_limit_signal.connect(lambda x: values_received.append(x))
    mock_pyepics_connection.upper_warning_limit_signal.connect(lambda x: values_received.append(x))
    mock_pyepics_connection.upper_ctrl_limit_signal.connect(lambda x: values_received.append(x))
    mock_pyepics_connection.lower_ctrl_limit_signal.connect(lambda x: values_received.append(x))

    mock_pyepics_connection.update_ctrl_vars(
        upper_ctrl_limit=70,
        lower_ctrl_limit=20,
        upper_alarm_limit=100,
        lower_alarm_limit=2,
        upper_warning_limit=90,
        lower_warning_limit=10,
    )

    expected_values = [70, 20, 100, 2, 90, 10]
    assert values_received == expected_values
