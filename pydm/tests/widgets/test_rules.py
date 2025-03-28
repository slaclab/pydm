import logging
import pytest
import weakref

from ...widgets.rules import RulesDispatcher
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

    rules = [
        {
            "name": "Rule #1",
            "property": "Visible",
            "expression": "ch[0] < 1",
            "channels": [{"channel": "ca://TESTRULES:Float", "trigger": True}],
        }
    ]

    dispatcher = RulesDispatcher()
    dispatcher.register(widget, rules)
    assert weakref.ref(widget) in dispatcher.rules_engine.widget_map

    dispatcher.unregister(widget)
    assert weakref.ref(widget) not in dispatcher.rules_engine.widget_map


def test_rules_not_connected(qtbot, caplog):
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

    rules = [
        {
            "name": "Rule #1",
            "property": "Visible",
            "expression": "ch[0] < 1",
            "channels": [{"channel": "ca://TESTRULES:Float", "trigger": True}],
        }
    ]

    dispatcher = RulesDispatcher()
    dispatcher.register(widget, rules)

    re = dispatcher.rules_engine
    assert weakref.ref(widget) in re.widget_map
    assert len(re.widget_map[weakref.ref(widget)]) == 1
    assert re.widget_map[weakref.ref(widget)][0]["rule"] == rules[0]

    with caplog.at_level(logging.DEBUG):
        re.callback_value(weakref.ref(widget), 0, 0, trigger=True, value=1)
        for record in caplog.records:
            assert record.levelno == logging.DEBUG
        assert "Not all channels are connected" in caplog.text


def test_rules_ok(qtbot, caplog):
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

    rules = [
        {
            "name": "Rule #1",
            "property": "Visible",
            "expression": "ch[0] < 1",
            "channels": [{"channel": "ca://TESTRULES:Float", "trigger": True}],
        }
    ]

    dispatcher = RulesDispatcher()
    dispatcher.register(widget, rules)

    re = dispatcher.rules_engine
    assert weakref.ref(widget) in re.widget_map
    assert len(re.widget_map[weakref.ref(widget)]) == 1
    assert re.widget_map[weakref.ref(widget)][0]["rule"] == rules[0]

    blocker = qtbot.waitSignal(re.rule_signal, timeout=5000)

    re.callback_conn(weakref.ref(widget), 0, 0, value=True)
    re.callback_value(weakref.ref(widget), 0, 0, trigger=True, value=5)
    assert re.widget_map[weakref.ref(widget)][0]["calculate"] is True

    blocker.wait()
    assert re.widget_map[weakref.ref(widget)][0]["calculate"] is False
    assert not widget.isVisible()


@pytest.mark.parametrize("use_enum, visible", [(None, True), (True, True), (False, False)])
def test_rules_enums(use_enum, visible, qtbot, caplog):
    """
    Test the rules mechanism with enums.

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

    rules = [
        {
            "name": "Rule #1",
            "property": "Visible",
            "expression": 'ch[0] == "RUN"',
            "channels": [{"channel": "ca://TESTRULES:Float", "trigger": True}],
        }
    ]
    if use_enum is not None:
        rules[0]["channels"][0]["use_enum"] = use_enum

    dispatcher = RulesDispatcher()
    dispatcher.register(widget, rules)

    re = dispatcher.rules_engine
    assert weakref.ref(widget) in re.widget_map
    assert len(re.widget_map[weakref.ref(widget)]) == 1
    assert re.widget_map[weakref.ref(widget)][0]["rule"] == rules[0]

    # First we test that we receive a value but we don't have enums yet
    blocker = qtbot.waitSignal(re.rule_signal, timeout=5000)

    re.callback_conn(weakref.ref(widget), 0, 0, value=True)
    re.callback_value(weakref.ref(widget), 0, 0, trigger=True, value=1)
    assert re.widget_map[weakref.ref(widget)][0]["calculate"] is True

    blocker.wait()
    assert re.widget_map[weakref.ref(widget)][0]["calculate"] is False
    assert not widget.isVisible()

    blocker = qtbot.waitSignal(re.rule_signal, timeout=5000)

    # Now receive enums and check that it was evaluated again and proper
    # value was sent making the widget visible on condition of use_enum
    re.callback_conn(weakref.ref(widget), 0, 0, value=True)
    re.callback_enum(weakref.ref(widget), 0, 0, enums=["STOP", "RUN"])
    assert re.widget_map[weakref.ref(widget)][0]["calculate"] is True

    blocker.wait()
    assert re.widget_map[weakref.ref(widget)][0]["calculate"] is False
    assert widget.isVisible() == visible


def test_rules_invalid_expr(qtbot, caplog):
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

    rules = [
        {
            "name": "Rule #1",
            "property": "Visible",
            "expression": "ch[0] < 1",
            "channels": [{"channel": "ca://TESTRULES:Float", "trigger": True}],
        }
    ]

    print("! 1")
    dispatcher = RulesDispatcher()
    print("! 2")
    dispatcher.register(widget, rules)
    print("! 3")

    re = dispatcher.rules_engine
    print("! 3")

    assert weakref.ref(widget) in re.widget_map
    print("! 4")

    assert len(re.widget_map[weakref.ref(widget)]) == 1
    print("! 5")

    assert re.widget_map[weakref.ref(widget)][0]["rule"] == rules[0]
    print("! 6")

    caplog.clear()
    print("! 7")

    rules[0]["expression"] = "foo"
    print("! 8")

    dispatcher.register(widget, rules)
    print("! 9")

    assert len(re.widget_map[weakref.ref(widget)]) == 1
    print("! 10")

    re.callback_conn(weakref.ref(widget), 0, 0, value=True)
    print("! 11")

    re.callback_value(weakref.ref(widget), 0, 0, trigger=True, value="a")
    print("! 12")

    # Wait for rule to execute but keep app responsive
    qtbot.wait(5000)
    print("! 13")

    for record in caplog.records:
        assert record.levelno == logging.ERROR
    assert "Error while evaluating Rule" in caplog.text

    print("! 14")

    dispatcher.unregister(widget)
    assert weakref.ref(widget) not in re.widget_map
    print("! 15")


def test_rules_initial_value(qtbot, caplog):
    """
    Test the rules initial value mechanism.

    Parameters
    ----------
    qtbot : fixture
        Parent of all the widgets
    caplog : fixture
        To capture the log messages
    """
    widget = PyDMLabel()
    widget.setText("Defaut Label")
    qtbot.addWidget(widget)
    widget.show()

    rules = [
        {
            "name": "Rule #1",
            "property": "Text",
            "expression": "str(ch[0])",
            "initial_value": "Initial Value Test",
            "channels": [{"channel": "ca://TESTRULES:Float", "trigger": True}],
        }
    ]

    dispatcher = RulesDispatcher()
    dispatcher.register(widget, rules)

    re = dispatcher.rules_engine
    assert weakref.ref(widget) in re.widget_map
    assert len(re.widget_map[weakref.ref(widget)]) == 1
    assert re.widget_map[weakref.ref(widget)][0]["rule"] == rules[0]
    assert widget.text() == "Initial Value Test"
    blocker = qtbot.waitSignal(re.rule_signal, timeout=5000)

    re.callback_conn(weakref.ref(widget), 0, 0, value=True)
    re.callback_value(weakref.ref(widget), 0, 0, trigger=True, value=5)
    assert re.widget_map[weakref.ref(widget)][0]["calculate"] is True

    blocker.wait()
    assert re.widget_map[weakref.ref(widget)][0]["calculate"] is False
    assert widget.text() == str(5)
