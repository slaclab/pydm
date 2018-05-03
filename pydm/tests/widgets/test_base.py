# Unit Tests for the base widget classes

import pytest


from ...PyQt.QtCore import Qt
from ...PyQt.QtGui import QColor
from ...utilities import is_pydm_app
from ...application import PyDMApplication
from ...widgets.base import compose_stylesheet, is_channel_valid, PyDMWidget, PyDMWritableWidget
from ...widgets.label import PyDMLabel
from ...widgets.pushbutton import PyDMPushButton
from ...widgets.line_edit import PyDMLineEdit
from ...widgets.channel import PyDMChannel


# --------------------
# POSITIVE TEST CASES
# --------------------

@pytest.mark.parametrize("base_class, obj_class_name, obj_name, expected_style", [
    ("PyDMWritableWidget", PyDMPushButton, None, "PyDMWritableWidget {color: #EB0000; }"),
    ("PyDMWidget", PyDMLabel, None, "PyDMWidget {color: #EB0000; }"),
    ("PyDMWritableWidget", None, None, "PyDMWritableWidget {color: #EB0000; }"),
    (None, PyDMPushButton, None, "PyDMPushButton {color: #EB0000; }"),
    (None, PyDMPushButton, "PushButton", "PyDMPushButton#PushButton {color: #EB0000; }"),
    (None, None, "PushButton", " {color: #EB0000; }"),
])
def test_compose_stylesheet(monkeypatch, test_alarm_style_sheet_map, base_class, obj_class_name, obj_name,
                            expected_style):
    """
    Test the style generated for the widget based on an alarm event.

    Expectations:
    The style is generated correctly, taken into account the widget's base class, the widget's class, and the widget's
    name.

    Parameters
    ----------
    monkeypatch : fixture
        To temporarily override the behavior of a class
    test_alarm_style_sheet_map : fixture
        The widget's style map depending on the alarm event
    base_class : str
        The base class name of the widget
    obj_class_name : type
        The object type of the widget -- used for creating a new widget object
    obj_name : str
        The name of a widget object
    expected_style : str
        The expected style for an alarm event corresponding to the widget
    """
    obj = None
    if obj_class_name:
        obj = obj_class_name()

    if obj_name:
        # Pretend that the push button can have an object name to test the object name concatenation to the style string
        monkeypatch.setattr(PyDMPushButton, "objectName", lambda *args: obj_name)

    style = dict(test_alarm_style_sheet_map[PyDMWidget.ALARM_CONTENT][PyDMWidget.ALARM_MAJOR])
    style_name = compose_stylesheet(style, base_class=base_class, obj=obj)
    assert style_name == expected_style


@pytest.mark.parametrize("channel_address, expected", [
    ("CA://MA_TEST", True),
    ("", False),
    (None, False),
])
def test_is_channel_valid(channel_address, expected):
    """
    Test to ensure channel validation.

    Expectations:
    If the channel is valid, i.e. not empty or None, the evaluation result is True. Otherwise, the result is False.

    Parameters
    ----------
    channel_address : str
        The address of a data channel
    expected : bool
        The expected validation result
    """
    assert is_channel_valid(channel_address) == expected


test_local_connection_status_color_map = {
        False: QColor(0, 0, 0),
        True: QColor(0, 0, 0,)
}

@pytest.mark.parametrize("init_channel", [
    "CA://MA_TEST",
    "",
    None,
])
def test_pydm_widget_construct(qtbot, test_alarm_style_sheet_map, init_channel):
    """
    Test the construction of the widget.

    Expectations:
    The widget is constructed with the correct default values

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    test_alarm_style_sheet_map : dict
        The map containing the styles corresponding to alarm events
    init_channel : str
        The channel the widget is going to be initialized with
    """
    # Initialize a PyDMLabel because it is a PyDMWidget
    pydm_label = PyDMLabel(init_channel=init_channel)
    qtbot.addWidget(pydm_label)

    assert pydm_label.app is None if not is_pydm_app else not None
    assert pydm_label._connected is not is_pydm_app
    assert pydm_label._color == test_local_connection_status_color_map[False]
    assert pydm_label._channel == init_channel
    assert pydm_label._channels is None
    assert pydm_label._show_units is False
    assert pydm_label._alarm_sensitive_content is False
    assert pydm_label.alarmSensitiveBorder is True
    assert pydm_label._alarm_flags == (PyDMWidget.ALARM_CONTENT * pydm_label._alarm_sensitive_content) | (
            PyDMWidget.ALARM_BORDER * pydm_label._alarm_sensitive_border)
    assert pydm_label._alarm_state == PyDMWidget.ALARM_DISCONNECTED
    assert pydm_label._style == test_alarm_style_sheet_map[pydm_label._alarm_flags][pydm_label._alarm_state]

    if is_pydm_app and is_channel_valid(init_channel):
        assert pydm_label._tooltip == ""
    else:
        assert pydm_label._tooltip is None

    assert pydm_label._precision_from_pv is True
    assert pydm_label._prec == 0
    assert pydm_label._unit == ""

    assert pydm_label._upper_ctrl_limit is None
    assert pydm_label._lower_ctrl_limit is None

    assert pydm_label.enum_strings is None
    assert pydm_label.format_string == "{}"

    assert pydm_label.value is None
    assert pydm_label.channeltype is None
    assert pydm_label.subtype is None

    assert pydm_label.contextMenuPolicy() == Qt.DefaultContextMenu
    assert pydm_label.contextMenuEvent


@pytest.mark.parametrize("init_channel", [
    "CA://MA_TEST",
    "",
    None,
])
def test_widget_ctx_menu(qtbot, init_channel):
    """
    Test the initial context menu creation.

    Expectations:
    The context menu is empty in the beginning.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    init_channel : str
        The channel the widget is going to be initialized with
    """
    pydm_label = PyDMLabel(init_channel=init_channel)
    qtbot.addWidget(pydm_label)

    assert pydm_label.widget_ctx_menu() is None


@pytest.mark.parametrize("init_channel", [
    "CA://MA_TEST",
    "",
    None,
])
def test_pydmwidget_init_for_designer(qtbot, init_channel):
    """
    Test the initialization sequence of a PyDMWidget object.

    Expectations:
    The widget is initialized correctly.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    init_channel : str
        The channel the widget is going to be initialized with
    """
    pydm_label = PyDMLabel(init_channel=init_channel)
    qtbot.addWidget(pydm_label)

    pydm_label._connected = False
    pydm_label.init_for_designer()
    assert pydm_label._connected is True


@pytest.mark.parametrize("init_channel", [
    "CA://MA_TEST",
    "",
    None,
])
def test_pydmwritablewidget_init_for_designer(qtbot, init_channel):
    """
    Test the initialization sequence of a PyDMWritableWidget object.

    Expectations:
    The widget is initialized correctly.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    init_channel : str
        The channel the widget is going to be initialized with
    """
    # Initialize a PyDMLineEdit because it is a PyDMWritableWidget
    pydm_lineedit = PyDMLineEdit(init_channel=init_channel)
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit._connected = False
    pydm_lineedit.init_for_designer()
    assert pydm_lineedit._connected is True


@pytest.mark.parametrize("which_limit, new_limit", [
    ("UPPER", 123.456),
    ("LOWER", 12.345),
])
def test_ctrl_limit_changed(qtbot, signals, which_limit, new_limit):
    """
    Test the upper and lower limit settings.

    Expectations:
        The upper or lower limit can be emitted and subsequently read correctly.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    which_limit : str
        "UPPER" if the new value is intended for the upper limit, "LOWER" for the lower limit
    new_limit : float
        The new limit value
    """
    pydm_label = PyDMLabel(init_channel="CA://MA_TEST")
    qtbot.addWidget(pydm_label)

    if which_limit == "UPPER":
        signals.upper_ctrl_limit_signal[type(new_limit)].connect(pydm_label.upperCtrlLimitChanged)
        signals.upper_ctrl_limit_signal[type(new_limit)].emit(new_limit)

        assert pydm_label.get_ctrl_limits()[1] == new_limit
    elif which_limit == "LOWER":
        signals.lower_ctrl_limit_signal[type(new_limit)].connect(pydm_label.lowerCtrlLimitChanged)
        signals.lower_ctrl_limit_signal[type(new_limit)].emit(new_limit)

        assert pydm_label.get_ctrl_limits()[0] == new_limit


def test_force_redraw(qtbot, signals):
    """
    Test the forced redraw of a PyDMWidget object to ensure no exception will be raised.

    Expectations:
    The signal connected to the force_redraw slot will respond to the emit without raising any exception.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    """
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    signals.send_value_signal[int].connect(pydm_label.force_redraw)
    signals.send_value_signal[int].emit(123)


def test_precision_from_pv(qtbot):
    """
    Test setting the flag whether the precision is set to the widget from the PV.

    Expectations:
    The widget can retain the new precision source flag value.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    """
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    is_precision_from_pv = pydm_label.precisionFromPV

    # Flip the original flag value. Now the widget should contain the opposite value from before
    pydm_label.precisionFromPV = not is_precision_from_pv

    assert pydm_label.precisionFromPV is not is_precision_from_pv


def test_precision(qtbot):
    """
    Test setting the precision is set to the widget.

    Expectations:
    The widget can retain the new precision value.

    Parameters
    ----------
    qtbot : fixture
       pytest-qt window for widget test
    """
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    pydm_label.precision = 3
    precision = pydm_label.precision

    pydm_label.precision = precision * 4
    assert pydm_label.precision == precision * 4


def test_channels_for_tools(qtbot):
    """
    Test the channel exposure for external tools.

    Expectations:
    The current default implementation is to provide the same channels via channel_for_tools as with channels(). This
    test ensures that will happen.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    assert all(x == y for x, y in zip(pydm_label.channels(), pydm_label.channels_for_tools()))


def test_pydmwidget_channels(qtbot):
    """
    Test the channels population for the widget whose base class PyDMWidget

    Expectations:
    1. If the widget does not have channels populated, it will be populated with the default channels, containing all
        the signals pertaining to its base class.
    2. Otherwise, the widget will contain just the channels from its latest assignment.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    assert pydm_label._channel is None
    assert pydm_label._channels is None

    pydm_channels = pydm_label.channels()[0]

    default_pydm_channels = PyDMChannel(address=pydm_label.channel,
                                        connection_slot=pydm_label.connectionStateChanged,
                                        value_slot=pydm_label.channelValueChanged,
                                        severity_slot=pydm_label.alarmSeverityChanged,
                                        enum_strings_slot=pydm_label.enumStringsChanged,
                                        unit_slot=pydm_label.unitChanged,
                                        prec_slot=pydm_label.precisionChanged,
                                        upper_ctrl_limit_slot=pydm_label.upperCtrlLimitChanged,
                                        lower_ctrl_limit_slot=pydm_label.lowerCtrlLimitChanged,
                                        value_signal=None,
                                        write_access_slot=None)
    assert pydm_channels == default_pydm_channels

    new_channel = PyDMChannel(address=pydm_label.channel,
                              connection_slot=pydm_label.connectionStateChanged,
                              upper_ctrl_limit_slot=None,
                              lower_ctrl_limit_slot=None)
    pydm_label._channels = [new_channel]
    assert pydm_label.channels()[0] == new_channel


def test_pydmwritablewidget_channels(qtbot):
    """
    Test the channels population for the widget whose base class PyDMWritableWidget

    Expectations:
    1. If the widget does not have channels populated, it will be populated with the default channels, containing all
        the signals pertaining to its base class.
    2. Otherwise, the widget will contain just the channels from its latest assignment.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """

    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    assert pydm_lineedit._channel is None
    assert pydm_lineedit._channels is None

    pydm_channels = pydm_lineedit.channels()[0]

    default_pydm_channels = PyDMChannel(address=pydm_lineedit.channel,
                                        connection_slot=pydm_lineedit.connectionStateChanged,
                                        value_slot=pydm_lineedit.channelValueChanged,
                                        severity_slot=pydm_lineedit.alarmSeverityChanged,
                                        enum_strings_slot=pydm_lineedit.enumStringsChanged,
                                        unit_slot=pydm_lineedit.unitChanged,
                                        prec_slot=pydm_lineedit.precisionChanged,
                                        upper_ctrl_limit_slot=pydm_lineedit.upperCtrlLimitChanged,
                                        lower_ctrl_limit_slot=pydm_lineedit.lowerCtrlLimitChanged,
                                        value_signal=pydm_lineedit.send_value_signal,
                                        write_access_slot=pydm_lineedit.writeAccessChanged)
    assert pydm_channels == default_pydm_channels

    new_channel = PyDMChannel(address=pydm_lineedit.channel,
                              connection_slot=pydm_lineedit.connectionStateChanged,
                              upper_ctrl_limit_slot=None,
                              lower_ctrl_limit_slot=None)
    pydm_lineedit._channels = [new_channel]
    assert pydm_lineedit.channels()[0] == new_channel


@pytest.mark.parametrize("channel_address, connected, write_access, is_app_read_only", [
    ("CA://MA_TEST", True, True, True),
    ("CA://MA_TEST", True, False, True),
    ("CA://MA_TEST", True, True, False),
    ("CA://MA_TEST", True, False, False),
    ("CA://MA_TEST", False, True, True),
    ("CA://MA_TEST", False, False, True),
    ("CA://MA_TEST", False, True, False),
    ("CA://MA_TEST", False, False, False),
    ("", False, False, False),
    (None, False, False, False),
])
def test_pydmwritable_check_enable_state(qtbot, monkeypatch, channel_address, connected, write_access,
                                         is_app_read_only):
    """
    Test the tooltip generated depending on the channel address validation, connection, write access, and whether the
    app is read-only. This test is for a widget whose base class is PyDMWritableWidget.

    Expectations:
    1. The widget's tooltip will update only if the channel address is valid.
    2. If the data channel is disconnected, the widget's tooltip will  "PV is disconnected"
    3. If the data channel is connected, but it has no write access:
        a. If the app is read-only, the tooltip will read  "Running PyDM on Read-Only mode."
        b. If the app is not read-only, the tooltip will read "Access denied by Channel Access Security."

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To override the default behavior of PyDMApplication.is_read_only()
    channel_address : str
        The channel address
    connected : bool
        True if the channel is connected; False otherwise
    write_access : bool
        True if the widget has write access to the channel; False otherwise
    is_app_read_only : bool
        True if the PyDM app is read-only; False otherwise
    """
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit.channel = channel_address
    pydm_lineedit._connected = connected
    pydm_lineedit._write_access = write_access

    monkeypatch.setattr(PyDMApplication, 'is_read_only', lambda *args: (is_app_read_only))

    original_tooltip = "Original Tooltip"
    pydm_lineedit.setToolTip(original_tooltip)
    pydm_lineedit.check_enable_state()

    actual_tooltip = pydm_lineedit.toolTip()
    if is_channel_valid(channel_address):
        if not pydm_lineedit._connected:
            assert "PV is disconnected." in actual_tooltip
        elif not write_access:
            if is_pydm_app() and pydm_lineedit.app.is_read_only():
                assert "Running PyDM on Read-Only mode." in actual_tooltip
            else:
                assert "Access denied by Channel Access Security." in actual_tooltip
    else:
        assert actual_tooltip == original_tooltip


@pytest.mark.parametrize("alarm_type, alarm, expected_qcolor", [

    (PyDMWidget.ALARM_CONTENT, PyDMWidget.ALARM_NONE, {"color": "black"}),
    (PyDMWidget.ALARM_CONTENT, PyDMWidget.ALARM_MINOR, {"color": "#EBEB00"}),
    (PyDMWidget.ALARM_CONTENT, PyDMWidget.ALARM_MAJOR, {"color": "#EB0000"}),
    (PyDMWidget.ALARM_CONTENT, PyDMWidget.ALARM_INVALID, {"color": "#EB00EB"}),
    (PyDMWidget.ALARM_CONTENT, PyDMWidget.ALARM_DISCONNECTED, {"color": "#EBEBEB"}),

    (PyDMWidget.ALARM_CONTENT | PyDMWidget.ALARM_BORDER, PyDMWidget.ALARM_NONE,
     {"color": "black", "border": "2px solid transparent"}),
    (PyDMWidget.ALARM_CONTENT | PyDMWidget.ALARM_BORDER, PyDMWidget.ALARM_MINOR,
     {"color": "#EBEB00", "border": "2px solid #EBEB00"}),
    (PyDMWidget.ALARM_CONTENT | PyDMWidget.ALARM_BORDER, PyDMWidget.ALARM_MAJOR,
     {"color": "#EB0000", "border": "2px solid #EB0000"}),
    (PyDMWidget.ALARM_CONTENT | PyDMWidget.ALARM_BORDER, PyDMWidget.ALARM_INVALID,
     {"color": "#EB00EB", "border": "2px solid #EB00EB"}),
    (PyDMWidget.ALARM_CONTENT | PyDMWidget.ALARM_BORDER, PyDMWidget.ALARM_DISCONNECTED,
     {"color": "#EBEBEB", "border": "2px solid #EBEBEB"}),
])
def test_qcolor_for_alarm(qtbot, alarm_type, alarm, expected_qcolor):
    """
    Test the QColor object generated for the widget based on an alarm context.

    Expectations:
    The QColor object will be correctly generated as expected.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    alarm_type : int
        The alarm type, e.g. AlARM_CONTENT, ALARM_INDICATOR, ALARM_BORDER, ALARM_CONTENT | ALARM_BORDER, etc.
    alarm : int
        The alarm severity, e.g. ALARM_NONE, ALARM_MINOR, ALARM_MAJOR, ALARM_INVALID, ALARM_DISCONNECTED
    expected_qcolor : QColor
        The expected QColor to be generated
    """
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    qcolor = pydm_label.qcolor_for_alarm(alarm, alarm_type)
    assert qcolor == QColor(expected_qcolor["color"])
