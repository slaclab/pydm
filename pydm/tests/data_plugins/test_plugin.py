from unittest.mock import MagicMock

from pydm.data_plugins import PyDMPlugin
from pydm.widgets.channel import PyDMChannel


def test_connections():
    """Test that adding and removing connections in the base plugin class works as expected"""
    pydm_plugin = PyDMPlugin()

    # First add a couple of channels, confirm they were added correctly along with their associated channels
    test_channel_one = PyDMChannel("ca://TEST:CHANNEL:ONE")
    test_channel_two = PyDMChannel("ca://TEST:CHANNEL:TWO")
    pydm_plugin.add_connection(test_channel_one)
    pydm_plugin.add_connection(test_channel_two)
    assert test_channel_one, test_channel_two in pydm_plugin.channels
    assert pydm_plugin.connections["TEST:CHANNEL:ONE"].address == "TEST:CHANNEL:ONE"
    assert pydm_plugin.connections["TEST:CHANNEL:TWO"].address == "TEST:CHANNEL:TWO"

    # Then remove the channels and confirm that both the channels and connections are deleted correctly
    pydm_plugin.remove_connection(test_channel_one)
    assert test_channel_one not in pydm_plugin.channels
    assert len(pydm_plugin.connections) == 1
    assert pydm_plugin.connections["TEST:CHANNEL:TWO"].address == "TEST:CHANNEL:TWO"

    pydm_plugin.remove_connection(test_channel_two)
    assert test_channel_two not in pydm_plugin.channels
    assert len(pydm_plugin.connections) == 0


def test_signal_slot_disconnect():
    """When a listener is removed from a channel, verify all signals/slots for that listener are disconnected"""
    pydm_plugin = PyDMPlugin()

    signal_one = MagicMock()
    signal_two = MagicMock()

    # First create a couple of channels, both pointing to the same address and giving the values signals to write to
    test_channel_one = create_channel("ca://TEST:CHANNEL", signal_one)
    test_channel_two = create_channel("ca://TEST:CHANNEL", signal_two)

    pydm_plugin.add_connection(test_channel_one)
    pydm_plugin.add_connection(test_channel_two)

    # There should only be one connection object since both channels pointed to the same address
    connection = pydm_plugin.connections["TEST:CHANNEL"]
    connection.add_listener(test_channel_one)
    connection.put_value = lambda: None  # Mock that the test will be writing a value

    # There should be two listeners to every signal for this connection since we created two distinct channels for it
    assert_all_signal_receivers(connection, 2)

    pydm_plugin.remove_connection(test_channel_one)
    # The connection should still exist even if one listener goes away, with one slot still present for each signal
    assert_all_signal_receivers(connection, 1)
    signal_one[str].disconnect.assert_called()
    signal_two[str].disconnect.assert_not_called()

    signal_one[str].reset_mock()
    signal_two[str].reset_mock()
    pydm_plugin.remove_connection(test_channel_two)

    # Now that no more listeners are remaining, the connection should be closed
    assert connection.listener_count == 0
    signal_one[str].disconnect.assert_not_called()
    signal_two[str].disconnect.assert_called()


def assert_all_signal_receivers(connection, expected_receivers):
    signals = [
        "new_value_signal",
        "connection_state_signal",
        "new_severity_signal",
        "write_access_signal",
        "enum_strings_signal",
        "unit_signal",
        "prec_signal",
        "upper_ctrl_limit_signal",
        "lower_ctrl_limit_signal",
        "upper_alarm_limit_signal",
        "lower_alarm_limit_signal",
        "upper_warning_limit_signal",
        "lower_warning_limit_signal",
        "timestamp_signal",
    ]

    for signal_name in signals:
        signal = getattr(connection, signal_name)
        assert connection.receivers(signal) == expected_receivers


def create_channel(address, value_signal):
    return PyDMChannel(
        address,
        connection_slot=lambda: None,
        value_slot=lambda: None,
        severity_slot=lambda: None,
        write_access_slot=lambda: None,
        enum_strings_slot=lambda: None,
        unit_slot=lambda: None,
        prec_slot=lambda: None,
        upper_ctrl_limit_slot=lambda: None,
        lower_ctrl_limit_slot=lambda: None,
        upper_alarm_limit_slot=lambda: None,
        lower_alarm_limit_slot=lambda: None,
        upper_warning_limit_slot=lambda: None,
        lower_warning_limit_slot=lambda: None,
        value_signal=value_signal,
        timestamp_slot=lambda: None,
    )
