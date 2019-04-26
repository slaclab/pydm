# Unit Tests for the base widget classes

import json
import logging

import numpy as np
import pytest

logger = logging.getLogger(__name__)

from qtpy.QtCore import Qt
from qtpy.QtGui import QMouseEvent
from qtpy.QtWidgets import QWidget, QMenu
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
    assert 'PV is disconnected.' in widget.toolTip()

    widget.connection_changed(True)
    assert widget._connected is True
    assert widget.isEnabled()
    assert widget.toolTip() == "Test Tooltip"

    widget.connection_changed(False)
    assert widget._connected is False
    assert widget.isEnabled() is False
    assert 'PV is disconnected.' in widget.toolTip()


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
    assert clipboard.text() == 'bar'


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


#
# @pytest.mark.parametrize("which_limit, new_limit", [
#     ("UPPER", 123.456),
#     ("LOWER", 12.345),
# ])
# def test_ctrl_limit_changed(qtbot, signals, which_limit, new_limit):
#     """
#     Test the upper and lower limit settings.
#
#     Expectations:
#         The upper or lower limit can be emitted and subsequently read correctly.
#
#     Parameters
#     ----------
#     qtbot : fixture
#         pytest-qt window for widget test
#     signals : fixture
#         The signals fixture, which provides access signals to be bound to the
#         appropriate slots
#     which_limit : str
#         "UPPER" if the new value is intended for the upper limit, "LOWER" for the lower limit
#     new_limit : float
#         The new limit value
#     """
#     pydm_label = PyDMLabel(init_channel="CA://MA_TEST")
#     qtbot.addWidget(pydm_label)
#
#     if which_limit == "UPPER":
#         signals.upper_ctrl_limit_signal[type(new_limit)].connect(
#             pydm_label.upperCtrlLimitChanged)
#         signals.upper_ctrl_limit_signal[type(new_limit)].emit(new_limit)
#
#         assert pydm_label.get_ctrl_limits()[1] == new_limit
#     elif which_limit == "LOWER":
#         signals.lower_ctrl_limit_signal[type(new_limit)].connect(
#             pydm_label.lowerCtrlLimitChanged)
#         signals.lower_ctrl_limit_signal[type(new_limit)].emit(new_limit)
#
#         assert pydm_label.get_ctrl_limits()[0] == new_limit
#
#
# def test_force_redraw(qtbot, signals):
#     """
#     Test the forced redraw of a PyDMWidget object to ensure no exception will be raised.
#
#     Expectations:
#     The signal connected to the force_redraw slot will respond to the emit without raising any exception.
#
#     Parameters
#     ----------
#     qtbot : fixture
#         pytest-qt window for widget test
#     signals : fixture
#         The signals fixture, which provides access signals to be bound to the appropriate slots
#     """
#     pydm_label = PyDMLabel()
#     qtbot.addWidget(pydm_label)
#
#     signals.send_value_signal[int].connect(pydm_label.force_redraw)
#     signals.send_value_signal[int].emit(123)
#
#
# def test_precision_from_pv(qtbot):
#     """
#     Test setting the flag whether the precision is set to the widget from the PV.
#
#     Expectations:
#     The widget can retain the new precision source flag value.
#
#     Parameters
#     ----------
#     qtbot : fixture
#         pytest-qt window for widget test
#     """
#     pydm_label = PyDMLabel()
#     qtbot.addWidget(pydm_label)
#
#     is_precision_from_pv = pydm_label.precisionFromPV
#
#     # Flip the original flag value. Now the widget should contain the opposite value from before
#     pydm_label.precisionFromPV = not is_precision_from_pv
#
#     assert pydm_label.precisionFromPV is not is_precision_from_pv
#
#
# def test_precision(qtbot):
#     """
#     Test setting the precision is set to the widget.
#
#     Expectations:
#     The widget can retain the new precision value.
#
#     Parameters
#     ----------
#     qtbot : fixture
#        pytest-qt window for widget test
#     """
#     pydm_label = PyDMLabel()
#     qtbot.addWidget(pydm_label)
#
#     pydm_label.precision = 3
#     precision = pydm_label.precision
#
#     pydm_label.precision = precision * 4
#     assert pydm_label.precision == precision * 4
#
#
# def test_channels_for_tools(qtbot):
#     """
#     Test the channel exposure for external tools.
#
#     Expectations:
#     The current default implementation is to provide the same channels via channel_for_tools as with channels(). This
#     test ensures that will happen.
#
#     Parameters
#     ----------
#     qtbot : fixture
#         Window for widget testing
#     """
#     pydm_label = PyDMLabel(init_channel='tst://This')
#     qtbot.addWidget(pydm_label)
#
#     assert all(x == y for x, y in
#                zip(pydm_label.channels(), pydm_label.channels_for_tools()))
#
#
# def test_pydmwidget_channel_change(qtbot):
#     """
#     Test the channel property for changes and the effect on the channels() property.
#
#     Parameters
#     ----------
#     qtbot : fixture
#         Window for widget testing
#
#     """
#     pydm_label = PyDMLabel()
#     qtbot.addWidget(pydm_label)
#     assert pydm_label._channel is None
#     assert pydm_label.channels() is None
#
#     pydm_label.channel = 'foo://bar'
#     assert pydm_label._channel == 'foo://bar'
#     assert pydm_label.channels()[0]._config == parse_channel_config('foo://bar', force_dict=True)
#
#     pydm_label.channel = 'abc://def'
#     assert pydm_label._channel == 'abc://def'
#     assert pydm_label.channels()[0]._config == parse_channel_config('abc://def', force_dict=True)
#
#
# @pytest.mark.parametrize(
#     "channel_address, connected, write_access, is_app_read_only", [
#         ("CA://MA_TEST", True, True, True),
#         ("CA://MA_TEST", True, False, True),
#         ("CA://MA_TEST", True, True, False),
#         ("CA://MA_TEST", True, False, False),
#         ("CA://MA_TEST", False, True, True),
#         ("CA://MA_TEST", False, False, True),
#         ("CA://MA_TEST", False, True, False),
#         ("CA://MA_TEST", False, False, False),
#         ("", False, False, False),
#         (None, False, False, False),
#     ])
# def test_pydmwritable_check_enable_state(qtbot, channel_address,
#                                          connected, write_access,
#                                          is_app_read_only):
#     """
#     Test the tooltip generated depending on the channel address validation, connection, write access, and whether the
#     app is read-only. This test is for a widget whose base class is PyDMWritableWidget.
#
#     Expectations:
#     1. The widget's tooltip will update only if the channel address is valid.
#     2. If the data channel is disconnected, the widget's tooltip will  "PV is disconnected"
#     3. If the data channel is connected, but it has no write access:
#         a. If the app is read-only, the tooltip will read  "Running PyDM on Read-Only mode."
#         b. If the app is not read-only, the tooltip will read "Access denied by Channel Access Security."
#
#     Parameters
#     ----------
#     qtbot : fixture
#         Window for widget testing
#     channel_address : str
#         The channel address
#     connected : bool
#         True if the channel is connected; False otherwise
#     write_access : bool
#         True if the widget has write access to the channel; False otherwise
#     is_app_read_only : bool
#         True if the PyDM app is read-only; False otherwise
#     """
#     pydm_lineedit = PyDMLineEdit()
#     qtbot.addWidget(pydm_lineedit)
#
#     pydm_lineedit.channel = channel_address
#     pydm_lineedit._connected = connected
#     pydm_lineedit._write_access = write_access
#
#     data_plugins.set_read_only(is_app_read_only)
#
#     original_tooltip = "Original Tooltip"
#     pydm_lineedit.setToolTip(original_tooltip)
#     pydm_lineedit.check_enable_state()
#
#     actual_tooltip = pydm_lineedit.toolTip()
#     if is_channel_valid(channel_address):
#         if not pydm_lineedit._connected:
#             assert "PV is disconnected." in actual_tooltip
#         elif not write_access:
#             if data_plugins.is_read_only():
#                 assert "Running PyDM on Read-Only mode." in actual_tooltip
#             else:
#                 assert "Access denied by Channel Access Security." in actual_tooltip
#     else:
#         assert actual_tooltip == original_tooltip
#
#
# def test_pydmwidget_setx_sety(qtbot):
#     """
#     Test the setX and setY method.
#
#     Parameters
#     ----------
#     qtbot : fixture
#         Window for widget testing
#
#     Returns
#     -------
#     None
#     """
#     pydm_label = PyDMLabel()
#     qtbot.addWidget(pydm_label)
#
#     pydm_label.setX(456)
#     pydm_label.setY(123)
#     pos = pydm_label.pos()
#     assert pos.x() == 456
#     assert pos.y() == 123
#

#
# def test_pydmwidget_rule_evaluated(qtbot, caplog):
#     """
#     Test the rules mechanism.
#
#     Parameters
#     ----------
#     qtbot : fixture
#         Window for widget testing
#     caplog : fixture
#         To capture the log messages
#     """
#     caplog.clear()
#     widget = PyDMLineEdit()
#     qtbot.addWidget(widget)
#     widget.show()
#
#     payload = {
#         'name': 'Test Rule 1',
#         'property': 'Invalid Property',
#         'value': 'foo'
#     }
#
#     widget.rule_evaluated(payload)
#     for record in caplog.records:
#         assert record.levelno == logging.ERROR
#     assert "is not part of this widget properties" in caplog.text
#
#     payload = {
#         'name': 'Test Rule 1',
#         'property': 'Visible',
#         'value': False
#     }
#
#     assert widget.isVisible()
#     widget.rule_evaluated(payload)
#     assert not widget.isVisible()
#
