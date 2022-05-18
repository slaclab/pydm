import functools
from p4p import Value
from p4p.client.thread import Context
from p4p.nt import NTScalar
from pydm.data_plugins.epics_plugins.p4p_plugin_component import Connection, P4PPlugin
from pydm.tests.conftest import ConnectionSignals
from pydm.widgets.channel import PyDMChannel
from pytest import MonkeyPatch


def test_send_new_value(monkeypatch: MonkeyPatch, signals: ConnectionSignals, qtbot):
    """ Ensure that all our signals are emitted as expected based on the structured data we received from p4p """

    # Set up a mock p4p client
    mock_channel = PyDMChannel()
    monkeypatch.setattr(P4PPlugin, 'context', Context('pva'))
    monkeypatch.setattr(P4PPlugin.context, 'monitor', lambda **args: None)  # Don't want to actually setup a monitor
    p4p_connection = Connection(mock_channel, 'pva://TEST:ADDRESS')

    received_values = {}
    signals_received = 0

    def receive_signal(value_name: str, value_received: object):
        """ A simple slot for receiving all our test signals and storing the values to ensure they are as expected """
        received_values[value_name] = value_received
        nonlocal signals_received
        signals_received += 1

    # Setup our initial testing value to send
    nt = NTScalar("i", display=True, control=True, valueAlarm=True)
    test_value = nt.wrap({'value': 5,
                          'valueAlarm': {'lowAlarmLimit': 2, 'lowWarningLimit': 3,
                                         'highAlarmLimit': 10, 'highWarningLimit': 8},
                          'alarm': {'severity': 0},
                          'display': {'units': 'mV'},
                          'control': {'limitLow': 1, 'limitHigh': 11}
                          })

    p4p_connection.new_value_signal[int].connect(functools.partial(receive_signal, 'value'))
    p4p_connection.lower_alarm_limit_signal.connect(functools.partial(receive_signal, 'low_alarm_limit'))
    p4p_connection.lower_warning_limit_signal.connect(functools.partial(receive_signal, 'low_warning_limit'))
    p4p_connection.upper_alarm_limit_signal.connect(functools.partial(receive_signal, 'high_alarm_limit'))
    p4p_connection.upper_warning_limit_signal.connect(functools.partial(receive_signal, 'high_warning_limit'))
    p4p_connection.new_severity_signal.connect(functools.partial(receive_signal, 'severity'))
    p4p_connection.unit_signal.connect(functools.partial(receive_signal, 'units'))
    p4p_connection.lower_ctrl_limit_signal.connect(functools.partial(receive_signal, 'lower_ctrl_limit'))
    p4p_connection.upper_ctrl_limit_signal.connect(functools.partial(receive_signal, 'upper_ctrl_limit'))

    # Send out the initial value for our test PV
    p4p_connection.send_new_value(test_value)

    # Confirm all the signals were fired off as expected, and that each value is what we specified
    assert received_values['value'] == 5
    assert received_values['low_alarm_limit'] == 2
    assert received_values['low_warning_limit'] == 3
    assert received_values['high_warning_limit'] == 8
    assert received_values['high_alarm_limit'] == 10
    assert received_values['severity'] == 0
    assert received_values['units'] == 'mV'
    assert received_values['lower_ctrl_limit'] == 1
    assert received_values['upper_ctrl_limit'] == 11
    assert signals_received == 9

    # Now make just a couple changes to our value, and send it again
    test_value.value = 9
    test_value.alarm.severity = 1
    p4p_connection.send_new_value(test_value)

    # Verify that the two values did update, and that the other 7 signals did not send
    assert received_values['value'] == 9
    assert received_values['severity'] == 1
    assert signals_received == 11
