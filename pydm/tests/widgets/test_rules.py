import pytest
import logging

from ...widgets.rules import RulesEngine

def test_rules_constructor(qapp):
    """
    Test the rules constructor.

    Parameters
    ----------
    qapp : fixture
        Reference to the QApplication
    """

    with pytest.raises(ValueError):
        rule_map = None
        invalid = RulesEngine(rule_map)

    with pytest.raises(ValueError):
        rule_map = "foo"
        invalid = RulesEngine(rule_map)

    rule_map = {'name': 'Rule #1', 'property': 'Enable',
              'expression': 'ch[0] > 1',
              'channels': [{'channel': 'ca://MTEST:Float', 'trigger': True}]}
    r_eng = RulesEngine(rule_map)

    assert r_eng.should_calculate is False
    assert r_eng.rule_map == rule_map
    assert r_eng.name == "Rule #1"
    assert r_eng.channels_connection == [False]
    assert r_eng.channels_value == [None]

    assert len(r_eng.channels) == 1
    assert r_eng.channels[0].address == "ca://MTEST:Float"


def test_rules_full(qapp, signals, caplog):
    """
    Test the rules mechanism.

    Parameters
    ----------
    qapp : fixture
        Reference to the QApplication
    signals : fixture
        The signals fixture, which provides access signals to be bound to the
        appropriate slots
    caplog : fixture
        To capture the log messages
    """
    rule_map = {'name': 'Rule #1', 'property': 'Enable',
                'expression': 'ch[0] > 1',
                'channels': [{'channel': 'ca://MTEST:Float', 'trigger': True}]}
    r_eng = RulesEngine(rule_map)
    r_eng.rule_signal.connect(signals.receiveValue)

    assert signals.value is None
    assert r_eng.should_calculate is False
    assert len(r_eng.channels) == 1
    assert r_eng.channels_connection == [False]
    assert r_eng.channels_value == [None]

    # Channel is not connected, will log an error.
    r_eng.channel_value_callback(0, 'channel_name', trigger=True, value=1)

    for record in caplog.records:
        assert record.levelno == logging.ERROR
    assert "Not all channels are connected" in caplog.text

    # Force the connection state and resend the value
    r_eng.channel_conn_callback(0, 'channel_name', trigger=True, value=True)
    r_eng.channel_value_callback(0, 'channel_name', trigger=True, value=5)
    assert r_eng.should_calculate is True
    r_eng.calculate_expression()
    assert r_eng.should_calculate is False
    assert signals.value['value'] is True

    # Test for Invalid Expression
    signals.reset()
    r_eng.expression = 'foo'
    r_eng.channel_value_callback(0, 'channel_name', trigger=True, value='a')
    r_eng.calculate_expression()
    for record in caplog.records:
        assert record.levelno == logging.ERROR
    assert "Error while evaluating Rule" in caplog.text
    assert signals.value is None


