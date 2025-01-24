import functools
import numpy as np
import pytest
from p4p.nt import NTEnum, NTScalar
from pydm.data_plugins.epics_plugins.p4p_plugin_component import Connection, P4PPlugin
from pydm.tests.conftest import ConnectionSignals
from pydm.widgets.channel import PyDMChannel
from pytest import MonkeyPatch
from p4p.wrapper import Type, Value


class MockContext:
    """A do-nothing mock of a p4p context object"""

    def __init__(self):
        self.monitor = None


def generate_control_variables(value):
    """Generate some set values for control variables to test against"""
    return {
        "value": value,
        "valueAlarm": {"lowAlarmLimit": 2, "lowWarningLimit": 3, "highAlarmLimit": 10, "highWarningLimit": 8},
        "alarm": {"severity": 0},
        "display": {"units": "mV"},
        "control": {"limitLow": 1, "limitHigh": 11},
    }


@pytest.mark.parametrize(
    "value_to_send, has_ctrl_vars, expected_value_to_receive, expected_signal_count",
    [
        (NTScalar("i", display=True, control=True, valueAlarm=True).wrap(generate_control_variables(5)), True, 5, 9),
        (NTScalar("b", display=True, control=True, valueAlarm=True).wrap(generate_control_variables(1)), True, 1, 9),
        (NTScalar("h", display=True, control=True, valueAlarm=True).wrap(generate_control_variables(2)), True, 2, 9),
        (
            NTScalar("f", display=True, control=True, valueAlarm=True).wrap(generate_control_variables(7.0)),
            True,
            7.0,
            9,
        ),
        (NTScalar("s").wrap({"value": "PyDM:TEST"}), False, "PyDM:TEST", 1),
        (NTScalar("ai").wrap({"value": [1, 2, 4]}), False, [1, 2, 4], 1),
        (NTScalar("ab").wrap({"value": [6, 7, 8]}), False, [6, 7, 8], 1),
        (NTScalar("ah").wrap({"value": [10, 11, 12]}), False, [10, 11, 12], 1),
        (NTScalar("af").wrap({"value": [5.0, 6.0, 7.0, 8.0]}), False, [5.0, 6.0, 7.0, 8.0], 1),
        (
            NTScalar("as").wrap({"value": ["PyDM", "PVA", "Test", "Strings"]}),
            False,
            ["PyDM", "PVA", "Test", "Strings"],
            1,
        ),
        (NTEnum().wrap({"index": 0, "choices": ["YES", "NO", "MAYBE"]}), False, 0, 2),
    ],  # Add cases for testing NTTable containing np.integer and np float types arrays here
)
def test_send_new_value(
    monkeypatch: MonkeyPatch,
    signals: ConnectionSignals,
    value_to_send: Value,
    has_ctrl_vars: bool,
    expected_value_to_receive: object,
    expected_signal_count: int,
):
    """Ensure that all our signals are emitted as expected based on the structured data we received from p4p"""

    # Set up a mock p4p client
    mock_channel = PyDMChannel()
    monkeypatch.setattr(P4PPlugin, "context", MockContext())
    monkeypatch.setattr(P4PPlugin.context, "monitor", lambda **args: None)  # Don't want to actually setup a monitor
    p4p_connection = Connection(mock_channel, "pva://TEST:ADDRESS")

    received_values = {}
    signals_received = 0

    def receive_signal(value_name: str, value_received: object):
        """A simple slot for receiving all our test signals and storing the values to ensure they are as expected"""
        received_values[value_name] = value_received
        nonlocal signals_received
        signals_received += 1

    expected_value_type = type(value_to_send.value)
    if isinstance(value_to_send.value, list):
        expected_value_type = np.ndarray
    elif "NTEnum" in value_to_send.getID():
        expected_value_type = int

    p4p_connection.new_value_signal[expected_value_type].connect(functools.partial(receive_signal, "value"))
    p4p_connection.lower_alarm_limit_signal.connect(functools.partial(receive_signal, "low_alarm_limit"))
    p4p_connection.lower_warning_limit_signal.connect(functools.partial(receive_signal, "low_warning_limit"))
    p4p_connection.upper_alarm_limit_signal.connect(functools.partial(receive_signal, "high_alarm_limit"))
    p4p_connection.upper_warning_limit_signal.connect(functools.partial(receive_signal, "high_warning_limit"))
    p4p_connection.new_severity_signal.connect(functools.partial(receive_signal, "severity"))
    p4p_connection.unit_signal.connect(functools.partial(receive_signal, "units"))
    p4p_connection.lower_ctrl_limit_signal.connect(functools.partial(receive_signal, "lower_ctrl_limit"))
    p4p_connection.upper_ctrl_limit_signal.connect(functools.partial(receive_signal, "upper_ctrl_limit"))
    p4p_connection.enum_strings_signal.connect(functools.partial(receive_signal, "enum_strings"))

    # Send out the initial value for our test PV
    p4p_connection.send_new_value(value_to_send)

    # Confirm all the signals were fired off as expected, and that each value is what we specified
    assert np.array_equal(received_values["value"], expected_value_to_receive)
    if has_ctrl_vars:
        assert received_values["low_alarm_limit"] == 2
        assert received_values["low_warning_limit"] == 3
        assert received_values["high_warning_limit"] == 8
        assert received_values["high_alarm_limit"] == 10
        assert received_values["severity"] == 0
        assert received_values["units"] == "mV"
        assert received_values["lower_ctrl_limit"] == 1
        assert received_values["upper_ctrl_limit"] == 11
        assert signals_received == expected_signal_count
    else:
        assert signals_received == expected_signal_count

    # Now make just a couple changes to our value, and send it again
    if has_ctrl_vars:
        value_to_send.value = 9
        value_to_send.alarm.severity = 1
        p4p_connection.send_new_value(value_to_send)

        # Verify that the two values did update, and that the other 7 signals did not send
        assert received_values["value"] == 9
        assert received_values["severity"] == 1
        assert signals_received == 11


def test_set_value_by_keys():
    table = {"a": {"b": {"c": 1}}}
    Connection.set_value_by_keys(table, ["a", "b", "c"], 2)
    assert table["a"]["b"]["c"] == 2

    table = {"1": {"2": {"3": 4}}}
    Connection.set_value_by_keys(table, ["1", "2", "3"], 5)
    assert table["1"]["2"]["3"] == 5

    table = {"a": {"b": {"c": 1}}}
    with pytest.raises(KeyError):
        Connection.set_value_by_keys(table, ["a", "x", "y"], 2)


def test_convert_epics_nttable():
    my_type = Type(
        [
            ("secondsPastEpoch", "l"),
            ("nanoseconds", "i"),
            ("userTag", "i"),
        ]
    )

    epics_struct = Value(my_type, {"secondsPastEpoch": 0, "nanoseconds": 0, "userTag": 0})

    solution = {"secondsPastEpoch": 0, "nanoseconds": 0, "userTag": 0}

    result = Connection.convert_epics_nttable(epics_struct)
    assert result == solution


@pytest.mark.parametrize(
    "address, expected_function_name, expected_arg_names, expected_arg_values, expected_poll_rate",
    [
        ("pva://pv:call:add?a=4&b=7&pydm_pollrate=10", "pv:call:add", ["a", "b"], ["4", "7"], 10),
        ("pva://pv:call:add?a=4&b=7&", "pv:call:add", ["a", "b"], ["4", "7"], 5.0),
        (
            "pva://pv:call:add_three_ints_negate_option?a=2&b=7&negate=True&pydm_pollrate=10",
            "pv:call:add_three_ints_negate_option",
            ["a", "b", "negate"],
            ["2", "7", "True"],
            10,
        ),
        (
            "pva://pv:call:add_ints_floats?a=3&b=4&c=5&d=6&e=7.8&pydm_pollrate=1",
            "pv:call:add_ints_floats",
            ["a", "b", "c", "d", "e"],
            ["3", "4", "5", "6", "7.8"],
            1,
        ),
        (
            "pva://pv:call:take_return_string?a=Hello&",
            "pv:call:take_return_string",
            ["a"],
            ["Hello"],
            5.0,
        ),
        ("", "", [], [], 0.0),  # poll-rate 0 because only set to DEFAULT_RPC_TIMEOUT (5) when have realistic address
    ],
)
def test_parsing_rpc_channel(
    monkeypatch, address, expected_function_name, expected_arg_names, expected_arg_values, expected_poll_rate
):
    """
    Ensure we can tell when a pva channel is an RPC call or not,
    and when it is make sure we are extracting its data correctly.
    """
    mock_channel = PyDMChannel(address=address)
    monkeypatch.setattr(P4PPlugin, "context", MockContext())
    monkeypatch.setattr(P4PPlugin.context, "monitor", lambda **args: None)  # Don't want to actually setup a monitor
    p4p_connection = Connection(mock_channel, address)

    assert p4p_connection._rpc_function_name == expected_function_name
    assert p4p_connection._rpc_arg_names == expected_arg_names
    assert p4p_connection._rpc_arg_values == expected_arg_values
    assert p4p_connection._rpc_poll_rate == expected_poll_rate


@pytest.mark.parametrize(
    "address, is_valid_rpc",
    [
        # Valid RPC
        ("pva://pv:call:add?a=4&b=7&pydm_pollrate=10", True),
        ("pva://pv:call:add?a=4&b=7&pydm_pollrate=5.5", True),
        # When pollrate is not specified, the last argument must also end with '&' character
        ("pva://pv:call:add?a=4&b=7&", True),
        # Valid pva addresses but not RPC
        ("pva://PyDM:PVA:IntValue", False),
        # Totally invalid
        ("this is not valid!! pva://&&==!!", False),
        ("pva://", False),
        ("", False),
        (None, False),
    ],
)
def test_is_rpc_check(
    monkeypatch,
    address,
    is_valid_rpc,
):
    """Ensure that the regex is working for checking if a pva address is a RPC request or not"""
    mock_channel = PyDMChannel(address=address)
    monkeypatch.setattr(P4PPlugin, "context", MockContext())
    monkeypatch.setattr(P4PPlugin.context, "monitor", lambda **args: None)  # Don't want to actually setup a monitor
    p4p_connection = Connection(mock_channel, address)

    assert p4p_connection.is_rpc_address(address) == is_valid_rpc


@pytest.mark.parametrize(
    "address, expected_query",
    [
        (
            "pva://pv:call:add?a=4&b=7&pydm_pollrate=10",
            {
                "a": 4,
                "b": 7,
            },
        ),
        # Check that not specifying pollrate doesn't effect Value obj creation
        (
            "pva://pv:call:add?a=4&b=7&",
            {
                "a": 4,
                "b": 7,
            },
        ),
        # Make sure args of mixed datatypes work correctly
        (
            "pva://pv:call:add?a=4&b=7.5&pydm_pollrate=10",
            {
                "a": 4,
                "b": 7.5,
            },
        ),
        # Try with more args
        (
            "pva://pv:call:add?a=1&b=2&c=3&d=4&e=5&pydm_pollrate=10",
            {
                "a": 1,
                "b": 2,
                "c": 3,
                "d": 4,
                "e": 5,
            },
        ),
        # Check using no args
        (
            "pva://pv:call:no_args&",
            {},
        ),
    ],
)
def test_create_rpc_value_obj(
    monkeypatch,
    address,
    expected_query,
):
    """
    To make a successful RPC call, we first need to create ("wrap") a request object to pass in.
    """
    mock_channel = PyDMChannel(address=address)
    monkeypatch.setattr(P4PPlugin, "context", MockContext())
    monkeypatch.setattr(P4PPlugin.context, "monitor", lambda **args: None)  # Don't want to actually setup a monitor
    p4p_connection = Connection(mock_channel, address)
    request = p4p_connection.create_request(
        p4p_connection._rpc_function_name, p4p_connection._rpc_arg_names, p4p_connection._rpc_arg_values
    )

    result_query = request.query

    assert len(result_query.items()) == len(expected_query.items())

    for item1, item2 in zip(result_query.items(), expected_query.items()):
        assert item1 == item2
