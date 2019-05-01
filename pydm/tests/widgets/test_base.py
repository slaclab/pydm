# Unit Tests for the base widget classes

import json
import logging

import numpy as np
import pytest

logger = logging.getLogger(__name__)

from qtpy.QtCore import Qt, QEvent
from qtpy.QtGui import QMouseEvent, QCursor
from qtpy.QtWidgets import QWidget, QMenu, QApplication
from pydm.utilities import is_pydm_app
from pydm.widgets.base import (is_channel_valid, PyDMPrimitiveWidget,
                               PyDMWidget, PyDMWritableWidget, TextFormatter)


class PrimitiveWidget(QWidget, PyDMPrimitiveWidget):
    def __init__(self, *args, **kwargs):
        super(PrimitiveWidget, self).__init__(*args, **kwargs)


class Widget(QWidget, PyDMWidget):
    def __init__(self, *args, **kwargs):
        super(Widget, self).__init__(*args, **kwargs)


class TextFormatWidget(QWidget, TextFormatter, PyDMWidget):
    def __init__(self, *args, **kwargs):
        super(TextFormatWidget, self).__init__(*args, **kwargs)


class WritableWidget(QWidget, PyDMWritableWidget):
    def __init__(self, *args, **kwargs):
        super(WritableWidget, self).__init__(*args, **kwargs)


def test_is_channel_valid():
    assert is_channel_valid("CA://MA_TEST") == True
    assert is_channel_valid("MA_TEST") == True
    assert is_channel_valid("") == False
    assert is_channel_valid(None) == False


def test_pydmprimitive_constructor(qtbot):
    widget = PrimitiveWidget()
    qtbot.addWidget(widget)
    assert widget._rules is None
    assert widget._opacity == 1.0
    assert widget.opacity() == 1.0


def test_pydmprimitive_rules(qtbot, caplog):
    widget = PrimitiveWidget()
    qtbot.addWidget(widget)

    widget.rules = "foo"
    for record in caplog.records:
        assert record.levelno == logging.ERROR
    assert "Invalid format for Rules" in caplog.text

    rules = [{'name': 'Rule #1', 'property': 'Enable',
              'expression': 'ch[0] > 1',
              'channels': [{'channel': 'ca://MTEST:Float', 'trigger': True}]}]

    rules_json = json.dumps(rules)
    widget.rules = rules_json
    assert widget.rules == rules_json

    rules[0]['name'] = 'Rule #2'
    rules_json = json.dumps(rules)
    widget.rules = rules_json


def test_pydmprimitive_rule_evaluated(qtbot, caplog):
    widget = PrimitiveWidget()
    qtbot.addWidget(widget)
    widget.show()

    payload = {
        'name': 'Test Rule 1',
        'property': 'Invalid Property',
        'value': 'foo'
    }

    widget.rule_evaluated(payload)
    for record in caplog.records:
        assert record.levelno == logging.ERROR
    assert "is not part of this widget properties" in caplog.text

    payload = {
        'name': 'Test Rule 1',
        'property': 'Visible',
        'value': False
    }

    assert widget.isVisible()
    widget.rule_evaluated(payload)
    assert not widget.isVisible()


def test_pydmprimitive_opacity(qtbot):
    widget = PrimitiveWidget()
    qtbot.addWidget(widget)
    assert widget.opacity() == 1.0
    widget.set_opacity(0.1)
    assert widget.opacity() == 0.1
    widget.set_opacity(2.0)
    assert widget.opacity() == 1
    widget.set_opacity(-1)
    assert widget.opacity() == 0


def test_pydmtextformatter_construct(qtbot):
    widget = TextFormatWidget()
    qtbot.addWidget(widget)
    assert widget._show_units is False
    assert widget.format_string == "{}"
    assert widget._precision_from_pv is True
    assert widget._prec == 0
    assert widget._unit == ""


def test_pydmtextformatter_precision(qtbot):
    widget = TextFormatWidget()
    qtbot.addWidget(widget)
    widget.value = 10
    assert widget.precisionFromPV is True
    assert widget._prec == 0
    widget.precision = 10
    assert widget._prec == 0
    widget.precisionFromPV = False
    widget.precision = 2
    assert widget._prec == 2

    widget.precision == 2
    widget.precisionFromPV = False
    widget.precision_changed(10)
    assert widget.precision == 2
    widget.precisionFromPV = True
    widget.precision_changed(5)
    assert widget.precision == 5


def test_pydmtextformatter_units(qtbot):
    widget = TextFormatWidget()
    qtbot.addWidget(widget)
    widget.value = 10
    assert widget._unit == ""
    assert widget.showUnits is False
    widget.showUnits = True
    assert widget.showUnits is True
    widget.unit_changed("s")
    assert widget._unit == "s"


def test_pydmtextformatter_update_format_string(qtbot):
    widget = TextFormatWidget()
    qtbot.addWidget(widget)
    assert widget.value is None
    assert widget._prec == 0

    widget.value = 1.0
    widget._prec = 2
    widget.show
    fmt = widget.update_format_string()
    assert fmt == "{:.2f}"
    widget.unit_changed("ms")
    widget.showUnits = True
    assert widget.format_string == "{:.2f} ms"


@pytest.mark.parametrize("init_channel", [
    "CA://MA_TEST",
    "",
    None,
])
def test_pydmwidget_construct(qtbot, init_channel):
    # Initialize a Widget
    widget = Widget(init_channel=init_channel)
    qtbot.addWidget(widget)

    assert widget.app is None if not is_pydm_app else not None
    assert widget._connected is not is_pydm_app
    if init_channel is None:
        assert widget.channels() is None
    else:
        assert len(widget.channels()) == 1
    assert widget._show_units is False
    assert widget._alarm_sensitive_content is False
    assert widget.alarmSensitiveBorder is True
    if init_channel:
        assert widget._alarm_state == PyDMWidget.ALARM_DISCONNECTED
    else:
        assert widget._alarm_state == PyDMWidget.ALARM_NONE

    if is_pydm_app and is_channel_valid(init_channel):
        assert widget._tooltip == ""
    else:
        assert widget._tooltip is None

    assert widget._upper_ctrl_limit is None
    assert widget._lower_ctrl_limit is None

    assert widget.enum_strings is None

    assert widget.value is None
    assert widget.channeltype is None
    assert widget.subtype is None

    assert widget.contextMenuPolicy() == Qt.DefaultContextMenu
    assert widget.contextMenuEvent
    assert widget.rules is None

    assert widget.opacity() == 1.0



def test_pydmwidget_destroyed(qtbot):
    widget = Widget(init_channel="tst://foo")
    blocker = qtbot.waitSignal(widget.destroyed)
    widget.deleteLater()
    blocker.wait()


def test_pydmwidget_context_menu(qtbot):
    widget = Widget()
    qtbot.addWidget(widget)
    assert widget.widget_ctx_menu() is None
    menu = widget.generate_context_menu()
    assert menu is not None


def test_pydmwidget_open_context_menu(qtbot, monkeypatch, caplog):
    widget = Widget()
    qtbot.addWidget(widget)

    def mock_exec_(*args, **kwargs):
        logger.info("Context Menu displayed.")

    caplog.clear()
    with caplog.at_level(logging.INFO):
        monkeypatch.setattr(QMenu, "exec_", mock_exec_)
        mouse_event = QMouseEvent(QMouseEvent.MouseButtonRelease,
                                  widget.rect().center(), Qt.RightButton,
                                  Qt.RightButton,
                                  Qt.NoModifier)
        widget.open_context_menu(mouse_event)
        assert "Context Menu displayed." in caplog.text


def test_pydmwidget_init_for_designer(qtbot):
    widget = Widget()
    qtbot.addWidget(widget)
    assert widget._connected is False
    widget.init_for_designer()
    assert widget._connected is True


def test_pydmwidget_connection_changed(qtbot):
    widget = Widget()
    qtbot.addWidget(widget)

    # Initial State without a channel
    assert widget._connected is False
    assert widget.alarmSeverity == widget.ALARM_NONE

    widget.setToolTip('Test Tooltip')
    assert widget.restore_original_tooltip() == 'Test Tooltip'

    widget.channel = 'foo://bar'

    assert widget._connected is False
    assert widget.alarmSeverity == widget.ALARM_DISCONNECTED

    assert widget.isEnabled() is False
    assert 'Channel is disconnected.' in widget.toolTip()

    widget.connection_changed(True)
    assert widget._connected is True
    assert widget.isEnabled()
    assert widget.toolTip() == "Test Tooltip"

    widget.connection_changed(False)
    assert widget._connected is False
    assert widget.isEnabled() is False
    assert 'Channel is disconnected.' in widget.toolTip()


@pytest.mark.parametrize(
    "new_value, _type, _subtype",
    [
        ('Foo', str, None),
        (False, bool, None),
        (1, int, None),
        (1.0, float, None),
        (np.zeros(2, dtype=np.uint8), np.ndarray, np.uint8)
    ]
)
def test_pydmwidget_value_changed(qtbot, new_value, _type, _subtype):
    widget = Widget()
    qtbot.addWidget(widget)

    assert widget.value is None
    assert widget.channeltype is None
    assert widget.subtype is None

    widget.value_changed(new_value)
    if isinstance(new_value, np.ndarray):
        assert np.array_equal(widget.value, new_value)
    else:
        assert widget.value == new_value
    assert widget.channeltype == _type
    assert widget.subtype == _subtype


def test_pydmwidget_alarmSeverity(qtbot):
    widget = Widget()
    qtbot.addWidget(widget)

    assert widget.alarmSeverity == widget.ALARM_NONE
    widget.alarmSeverity = widget.ALARM_INVALID
    assert widget.alarmSeverity == widget.ALARM_INVALID


def test_pydmwidget_alarm_severity_changed(qtbot):
    widget = Widget()
    qtbot.addWidget(widget)

    assert widget._alarm_state == widget.ALARM_NONE
    widget.alarm_severity_changed(widget.ALARM_NONE)

    widget2 = Widget(init_channel='foo://bar')
    qtbot.addWidget(widget2)

    assert widget2._alarm_state == widget.ALARM_DISCONNECTED
    widget2.alarm_severity_changed(widget.ALARM_INVALID)
    assert widget2._alarm_state == widget.ALARM_DISCONNECTED
    widget2.connection_changed(True)
    assert widget2._alarm_state == widget.ALARM_NONE
    widget2.alarm_severity_changed(widget.ALARM_MAJOR)
    assert widget2._alarm_state == widget.ALARM_MAJOR


def test_pydmwidget_enum_strings_changed(qtbot):
    widget = Widget()
    qtbot.addWidget(widget)

    assert widget.enum_strings is None
    entries = ['foo', 'bar', 'test']
    widget.enum_strings_changed(entries)
    assert widget.enum_strings == entries


def test_pydmwidget_eventFilter(qapp, qtbot):
    widget = Widget(init_channel='foo://bar')
    qtbot.addWidget(widget)
    mouse_event = QMouseEvent(QMouseEvent.MouseButtonPress,
                              widget.rect().center(), Qt.MiddleButton,
                              Qt.MiddleButton,
                              Qt.NoModifier)
    ret = qapp.notify(widget, mouse_event)
    assert ret is True

    mouse_event = QMouseEvent(QMouseEvent.MouseButtonPress,
                              widget.rect().center(), Qt.LeftButton,
                              Qt.LeftButton,
                              Qt.NoModifier)
    ret = qapp.notify(widget, mouse_event)
    assert ret is False


def test_pydmwidget_show_address_tooltip(qapp, qtbot, caplog):
    widget = Widget()
    qtbot.addWidget(widget)
    clipboard = qapp.clipboard()

    mouse_event = QMouseEvent(QMouseEvent.MouseButtonPress,
                              widget.rect().center(), Qt.MiddleButton,
                              Qt.MiddleButton,
                              Qt.NoModifier)

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        widget.show_address_tooltip(mouse_event)
        assert 'has no PyDM Channels' in caplog.text

    caplog.clear()
    widget.channel = 'foo://bar'
    widget.show_address_tooltip(mouse_event)
    assert 'bar' in clipboard.text()


def test_pydmwidget_limits_changed(qtbot):
    widget = Widget()
    qtbot.addWidget(widget)

    assert widget._upper_ctrl_limit is None
    assert widget._lower_ctrl_limit is None

    widget.upper_limit_changed(10)
    assert widget._upper_ctrl_limit == 10

    widget.lower_limit_changed(-10)
    assert widget._lower_ctrl_limit == -10

    assert widget.get_ctrl_limits() == (-10, 10)


def test_pydmwidget_force_redraw(qtbot):
    # Yes... I added a test for a one-line method... every single % counts! :P
    widget = Widget()
    qtbot.addWidget(widget)
    widget.force_redraw()


def test_pydmwidget_setx_sety(qtbot):
    widget = Widget()
    qtbot.addWidget(widget)

    widget.setX(456)
    widget.setY(123)
    pos = widget.pos()
    assert pos.x() == 456
    assert pos.y() == 123


def test_pydmwidget_alarm_sensitive_flags(qtbot):
    widget = Widget()
    qtbot.addWidget(widget)

    assert widget.alarmSensitiveBorder is True
    assert widget.alarmSensitiveContent is False

    widget.alarmSensitiveBorder = False
    assert widget.alarmSensitiveBorder is False

    widget.alarmSensitiveContent = True
    assert widget.alarmSensitiveContent is True


def test_pydmwidget_channel(qtbot):
    widget = Widget()
    qtbot.addWidget(widget)
    assert widget.channel is None
    assert widget.channels() is None
    assert widget.channels_for_tools() is None

    widget.channel = "ca://MTEST:Float"
    assert widget.channel == "ca://MTEST:Float"
    assert len(widget.channels()) == 1
    assert widget.channels_for_tools() == widget.channels()
    addr = widget.channels()[0].address
    widget.channel = "ca://outro"
    assert addr != widget.channels()[0].address


def test_pydmwidget_receive_data(qtbot):
    from pydm.data_store import DataKeys

    widget = Widget()
    qtbot.addWidget(widget)

    data = None
    introspection = {DataKeys.CONNECTION: 'conn',
                     DataKeys.VALUE: 'val'}
    widget._receive_data(data, introspection)
    assert widget._connected is False
    assert widget.value is None

    data = {'conn': True, 'val': 1.2}
    widget._receive_data(data, introspection)
    assert widget._connected is True
    assert widget.value == 1.2


def test_pydmwritable_construct(qtbot):
    widget = WritableWidget()
    qtbot.addWidget(widget)
    assert widget._write_access is False


def test_pydmwritable_init_for_designer(qtbot):
    widget = WritableWidget()
    qtbot.addWidget(widget)
    assert widget._write_access is False
    widget.init_for_designer()
    assert widget._write_access is True


def test_pydmwritable_eventFilter(qapp, qtbot):
    widget = WritableWidget()
    qtbot.addWidget(widget)

    QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
    cursor = QApplication.overrideCursor()
    assert cursor.shape() == Qt.ArrowCursor

    enter_event = QEvent(QEvent.Enter)
    assert enter_event.type() == QEvent.Enter
    leave_event = QEvent(QEvent.Leave)
    assert leave_event.type() == QEvent.Leave

    QApplication.sendEvent(widget, enter_event)
    qapp.processEvents()
    assert QApplication.overrideCursor() == cursor

    widget.channel = "ca://TEST"
    QApplication.sendEvent(widget, enter_event)
    qapp.processEvents()
    assert QApplication.overrideCursor().shape() == Qt.ForbiddenCursor

    QApplication.sendEvent(widget, leave_event)
    qapp.processEvents()
    assert QApplication.overrideCursor() == cursor
    qapp.processEvents()


def test_pydmwritable_write_access_changed(qtbot):
    widget = WritableWidget()
    qtbot.addWidget(widget)
    assert widget._write_access is False
    widget.write_access_changed(True)
    assert widget._write_access is True


def test_pydmwritable_check_enable_state(qtbot):
    from pydm import data_plugins
    widget = WritableWidget()
    qtbot.addWidget(widget)
    widget.setToolTip("Initial Tooltip")
    widget.channel = "ca://test"
    assert widget._connected is False
    assert widget._write_access is False
    assert widget.isEnabled() is False
    assert "disconnected" in widget.toolTip()

    widget.connection_changed(True)
    assert widget._connected is True
    assert widget.isEnabled() is False
    assert "No Write Access" in widget.toolTip()

    widget.write_access_changed(True)
    assert widget._write_access is True
    assert widget.isEnabled() is True
    assert widget.toolTip() == "Initial Tooltip"

    data_plugins.set_read_only(True)
    widget.check_enable_state()
    assert widget.isEnabled() is False
    assert "PyDM on Read-Only" in widget.toolTip()
    data_plugins.set_read_only(False)


def test_pydmwritable_write_to_channel(qapp, qtbot, test_plugin, caplog):
    widget = WritableWidget(init_channel="tst://write")
    qtbot.addWidget(widget)

    connections = test_plugin.connections
    tst_conn = connections[list(connections.keys())[0]]
    assert tst_conn.payload_received is None

    blocker = qtbot.waitSignal(tst_conn.notify)
    intro = {"FOO": "foo", "BAR": "bar"}
    data = {"DATA1": "data1", "DATA2": "data2"}
    tst_conn.write_introspection(intro)
    tst_conn.write_data(data)
    blocker.wait()

    caplog.clear()
    with caplog.at_level(logging.ERROR):
        widget.write_to_channel(value="Invalid Test Write", key="Invalid")
        assert "Could not find real key" in caplog.text

    put_blocker = qtbot.waitSignal(widget.channels()[0].transmit)

    widget.write_to_channel(value="Test Write", key="BAR")
    qapp.processEvents()

    put_blocker.wait()
    assert tst_conn.payload_received == {"bar": "Test Write"}

    # Life could be easier but Python 2.7 has no `clear` for lists...
    # so we gotta improvise
    del widget._channels[:]
    caplog.clear()
    with caplog.at_level(logging.ERROR):
        widget.write_to_channel(value="Invalid Test Write", key="Invalid")
        assert "No channel configured for widget." in caplog.text
