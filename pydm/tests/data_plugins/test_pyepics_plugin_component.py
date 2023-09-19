from pydm.data_plugins.epics_plugins.pyepics_plugin_component import Connection
from pydm.tests.conftest import ConnectionSignals
from pydm.widgets.channel import PyDMChannel


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
