import logging
import time
import weakref

from ...widgets.rules import RulesEngine, RulesDispatcher
from ...widgets.label import PyDMLabel


def test_rules_dispatcher(qapp, caplog):
    """
    Test the dispatcher to ensure that it is a singleton.

    Parameters
    ----------
    qapp : QApplication
        Reference to the QApplication
    caplog : fixture
        To capture the log messages
    """
    disp1 = RulesDispatcher()
    disp2 = RulesDispatcher()
    assert disp1 is disp2

    assert disp1.rules_engine.isRunning()

    payload = {"foo": "bar"}
    disp1.dispatch(payload)

    for record in caplog.records:
        assert record.levelno == logging.ERROR
    assert "Error at RulesDispatcher" in caplog.text


def test_unregister(qtbot):
    """
    Test the dispatcher for registering and unregistering of widgets.

    Parameters
    ----------
    qtbot : fixture
        Parent of all the widgets
    """
    widget = PyDMLabel()
    qtbot.addWidget(widget)

    rules = [{'name': 'Rule #1', 'property': 'Visible',
              'expression': 'ch[0] < 1',
              'channels': [{'channel': 'ca://MTEST:Float', 'trigger': True}]}]

    dispatcher = RulesDispatcher()
    dispatcher.register(widget, rules)
    assert weakref.ref(widget) in dispatcher.rules_engine.widget_map

    dispatcher.unregister(widget)
    assert weakref.ref(widget) not in dispatcher.rules_engine.widget_map


def test_rules_full(qtbot, caplog):
    """
    Test the rules mechanism.

    Parameters
    ----------
    qtbot : fixture
        Parent of all the widgets
    caplog : fixture
        To capture the log messages
    """
    widget = PyDMLabel()
    qtbot.addWidget(widget)
    widget.show()
    assert widget.isVisible()

    rules = [{'name': 'Rule #1', 'property': 'Visible',
                'expression': 'ch[0] < 1',
                'channels': [{'channel': 'ca://MTEST:Float', 'trigger': True}]}]

    dispatcher = RulesDispatcher()
    dispatcher.register(widget, rules)

    re = dispatcher.rules_engine
    assert weakref.ref(widget) in re.widget_map
    assert len(re.widget_map[weakref.ref(widget)]) == 1
    assert re.widget_map[weakref.ref(widget)][0]['rule'] == rules[0]

    re.callback_value(weakref.ref(widget), 0, 0, trigger=True, value=1)
    for record in caplog.records:
        assert record.levelno == logging.ERROR
    assert "Not all channels are connected" in caplog.text

    blocker = qtbot.waitSignal(re.rule_signal, timeout=1000)

    re.callback_conn(weakref.ref(widget), 0, 0, value=True)
    re.callback_value(weakref.ref(widget), 0, 0, trigger=True, value=5)
    assert re.widget_map[weakref.ref(widget)][0]['calculate'] is True

    time.sleep(0.1)
    assert re.widget_map[weakref.ref(widget)][0]['calculate'] is False

    blocker.wait()
    assert not widget.isVisible()

    caplog.clear()

    rules[0]['expression'] = 'foo'
    dispatcher.register(widget, rules)
    assert len(re.widget_map[weakref.ref(widget)]) == 1
    re.callback_conn(weakref.ref(widget), 0, 0, value=True)
    re.callback_value(weakref.ref(widget), 0, 0, trigger=True, value='a')
    time.sleep(0.1)
    for record in caplog.records:
        assert record.levelno == logging.ERROR
    assert "Error while evaluating Rule" in caplog.text

    dispatcher.unregister(widget)
    assert weakref.ref(widget) not in re.widget_map