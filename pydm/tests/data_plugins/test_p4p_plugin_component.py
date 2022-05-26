import functools
import numpy as np
import pytest
from p4p.nt import NTScalar
from pydm.data_plugins.epics_plugins.p4p_plugin_component import Connection, P4PPlugin
from pydm.tests.conftest import ConnectionSignals
from pydm.widgets.channel import PyDMChannel
from pytest import MonkeyPatch


class MockContext:
    """ A do-nothing mock of a p4p context object """
    def __init__(self):
        self.monitor = None


def generate_control_variables(value):
    """ Generate some set values for control variables to test against """
    return {'value': value,
            'valueAlarm': {'lowAlarmLimit': 2, 'lowWarningLimit': 3, 'highAlarmLimit': 10, 'highWarningLimit': 8},
            'alarm': {'severity': 0},
            'display': {'units': 'mV'},
            'control': {'limitLow': 1, 'limitHigh': 11}
            }


@pytest.mark.parametrize('value_to_send, has_ctrl_vars, expected_value_to_receive', [
    (NTScalar("i", display=True, control=True, valueAlarm=True).wrap(generate_control_variables(5)), True, 5),
    (NTScalar("b", display=True, control=True, valueAlarm=True).wrap(generate_control_variables(1)), True, 1),
    (NTScalar("h", display=True, control=True, valueAlarm=True).wrap(generate_control_variables(2)), True, 2),
    (NTScalar("f", display=True, control=True, valueAlarm=True).wrap(generate_control_variables(7.0)), True, 7.0),
    (NTScalar("s").wrap({'value': 'PyDM:TEST'}), False, 'PyDM:TEST'),
    (NTScalar("ai").wrap({'value': [1, 2, 4]}), False, [1, 2, 4]),
    (NTScalar("ab").wrap({'value': [6, 7, 8]}), False, [6, 7, 8]),
    (NTScalar("ah").wrap({'value': [10, 11, 12]}), False, [10, 11, 12]),
    (NTScalar("af").wrap({'value': [5.0, 6.0, 7.0, 8.0]}), False, [5.0, 6.0, 7.0, 8.0]),
    (NTScalar("as").wrap({'value': ['PyDM', 'PVA', 'Test', 'Strings']}), False, ['PyDM', 'PVA', 'Test', 'Strings'])
])
def test_send_new_value(monkeypatch: MonkeyPatch, signals: ConnectionSignals,
                        value_to_send: object, has_ctrl_vars: bool, expected_value_to_receive: object):
    """ Ensure that all our signals are emitted as expected based on the structured data we received from p4p """

    # Set up a mock p4p client
    mock_channel = PyDMChannel()
    monkeypatch.setattr(P4PPlugin, 'context', MockContext())
    monkeypatch.setattr(P4PPlugin.context, 'monitor', lambda **args: None)  # Don't want to actually setup a monitor
    p4p_connection = Connection(mock_channel, 'pva://TEST:ADDRESS')

    received_values = {}
    signals_received = 0

    def receive_signal(value_name: str, value_received: object):
        """ A simple slot for receiving all our test signals and storing the values to ensure they are as expected """
        received_values[value_name] = value_received
        nonlocal signals_received
        signals_received += 1

    expected_value_type = type(value_to_send.value)
    if type(value_to_send.value) == list:
        expected_value_type = np.ndarray
    p4p_connection.new_value_signal[expected_value_type].connect(functools.partial(receive_signal, 'value'))
    p4p_connection.lower_alarm_limit_signal.connect(functools.partial(receive_signal, 'low_alarm_limit'))
    p4p_connection.lower_warning_limit_signal.connect(functools.partial(receive_signal, 'low_warning_limit'))
    p4p_connection.upper_alarm_limit_signal.connect(functools.partial(receive_signal, 'high_alarm_limit'))
    p4p_connection.upper_warning_limit_signal.connect(functools.partial(receive_signal, 'high_warning_limit'))
    p4p_connection.new_severity_signal.connect(functools.partial(receive_signal, 'severity'))
    p4p_connection.unit_signal.connect(functools.partial(receive_signal, 'units'))
    p4p_connection.lower_ctrl_limit_signal.connect(functools.partial(receive_signal, 'lower_ctrl_limit'))
    p4p_connection.upper_ctrl_limit_signal.connect(functools.partial(receive_signal, 'upper_ctrl_limit'))

    # Send out the initial value for our test PV
    p4p_connection.send_new_value(value_to_send)

    # Confirm all the signals were fired off as expected, and that each value is what we specified
    assert np.array_equal(received_values['value'], expected_value_to_receive)
    if has_ctrl_vars:
        assert received_values['low_alarm_limit'] == 2
        assert received_values['low_warning_limit'] == 3
        assert received_values['high_warning_limit'] == 8
        assert received_values['high_alarm_limit'] == 10
        assert received_values['severity'] == 0
        assert received_values['units'] == 'mV'
        assert received_values['lower_ctrl_limit'] == 1
        assert received_values['upper_ctrl_limit'] == 11
        assert signals_received == 9
    else:
        assert signals_received == 1

    # Now make just a couple changes to our value, and send it again
    if has_ctrl_vars:
        value_to_send.value = 9
        value_to_send.alarm.severity = 1
        p4p_connection.send_new_value(value_to_send)

        # Verify that the two values did update, and that the other 7 signals did not send
        assert received_values['value'] == 9
        assert received_values['severity'] == 1
        assert signals_received == 11
