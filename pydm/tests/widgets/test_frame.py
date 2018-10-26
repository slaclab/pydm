# Unit Tests for the Frame Widget


import pytest

from ...widgets.base import is_channel_valid
from ... import data_plugins
from ...widgets.base import PyDMWidget
from ...widgets.frame import PyDMFrame


# --------------------
# POSITIVE TEST CASES
# --------------------

def test_construct(qtbot):
    """
    Test the construction of the widget.

    Expectations:
    The correct default values are assigned to the widget's attributes.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    """
    pydm_frame = PyDMFrame()
    qtbot.addWidget(pydm_frame)

    assert pydm_frame._disable_on_disconnect is False
    assert pydm_frame.alarmSensitiveBorder is False


@pytest.mark.parametrize("init_value, new_value", [
    (False, True),
    (True, False),
    (False, False),
    (True, True)
])
def test_disable_on_disconnect(qtbot, init_value, new_value):
    """
    Test setting the flag to disable the widget when there's a channel disconnection.

    Expectations:
    The widget retains the new Boolean setting.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    init_value : bool
        The initial flag to whether disable a widget at disconnection. True is to disable the widget in that event;
        False is not to disable.
    new_value
        The flag to change the widget disabling setting. True is to disable the widget in that event;
        False is not to disable.
    """
    pydm_frame = PyDMFrame()
    qtbot.addWidget(pydm_frame)

    pydm_frame._disable_on_disconnect = init_value
    pydm_frame.disableOnDisconnect = new_value
    assert pydm_frame.disableOnDisconnect == new_value


@pytest.mark.parametrize("channel, alarm_sensitive_content, alarm_sensitive_border, new_alarm_severity", [
    (None, False, False, PyDMWidget.ALARM_NONE),
    (None, False, True, PyDMWidget.ALARM_NONE),
    (None, True, False, PyDMWidget.ALARM_NONE),
    (None, True, True, PyDMWidget.ALARM_NONE),

    (None, False, False, PyDMWidget.ALARM_MAJOR),
    (None, False, True, PyDMWidget.ALARM_MAJOR),
    (None, True, False, PyDMWidget.ALARM_MAJOR),
    (None, True, True, PyDMWidget.ALARM_MAJOR),

    ("CA://MTEST", False, False, PyDMWidget.ALARM_NONE),
    ("CA://MTEST", False, True, PyDMWidget.ALARM_NONE),
    ("CA://MTEST", True, False, PyDMWidget.ALARM_NONE),
    ("CA://MTEST", True, True, PyDMWidget.ALARM_NONE),

    ("CA://MTEST", False, False, PyDMWidget.ALARM_MINOR),
    ("CA://MTEST", False, True, PyDMWidget.ALARM_MINOR),
    ("CA://MTEST", True, False, PyDMWidget.ALARM_MINOR),
    ("CA://MTEST", True, True, PyDMWidget.ALARM_MINOR),

    ("CA://MTEST", False, False, PyDMWidget.ALARM_MAJOR),
    ("CA://MTEST", False, True, PyDMWidget.ALARM_MAJOR),
    ("CA://MTEST", True, False, PyDMWidget.ALARM_MAJOR),
    ("CA://MTEST", True, True, PyDMWidget.ALARM_MAJOR),

    ("CA://MTEST", False, False, PyDMWidget.ALARM_DISCONNECTED),
    ("CA://MTEST", False, True, PyDMWidget.ALARM_DISCONNECTED),
    ("CA://MTEST", True, False, PyDMWidget.ALARM_DISCONNECTED),
    ("CA://MTEST", True, True, PyDMWidget.ALARM_DISCONNECTED),
])
def test_alarm_severity_change(qtbot, signals, channel, alarm_sensitive_content, alarm_sensitive_border,
                               new_alarm_severity):
    """
    Test the style of the widget changing according to alarm sensitivity settings and alarm severity changes.

    Expectations:
    Depending on the initial widget's settings on whether the widget should change its content area and borders when
    there's an alarm event, the widget's style should reflect changes when there's an alarm event other than ALARM_NONE.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    channel : str
        The data channel address
    alarm_sensitive_content : bool
        True if the content area of the widget will change its color when an alarm happens; False if not
    alarm_sensitive_border : bool
        True if the borders of the widget will change its color when an alarm happens; False if not
    new_alarm_severity : PyDMWidget alarm type
        The new alarm severity that may prompt the widget to change its content area and/or border colors.
    """
    pydm_frame = PyDMFrame()
    qtbot.addWidget(pydm_frame)

    pydm_frame._channel = channel
    pydm_frame.alarmSensitiveContent = alarm_sensitive_content
    pydm_frame.alarmSensitiveBorder = alarm_sensitive_border


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
def test_check_enable_state(qtbot, signals, channel_address, connected, write_access, is_app_read_only):
    """
    Test the tooltip generated depending on the channel address validation, connection, write access, and whether the
    app is read-only.

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
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    channel_address : str
        The channel address
    connected : bool
        True if the channel is connected; False otherwise
    write_access : bool
        True if the widget has write access to the channel; False otherwise
    is_app_read_only : bool
        True if the PyDM app is read-only; False otherwise
    """
    pydm_frame = PyDMFrame()
    qtbot.addWidget(pydm_frame)

    pydm_frame.channel = channel_address

    if not pydm_frame._disable_on_disconnect:
        assert pydm_frame.isEnabled()
    else:
        signals.write_access_signal[bool].connect(pydm_frame.writeAccessChanged)
        signals.write_access_signal[bool].emit(write_access)

        signals.connection_state_signal[bool].connect(pydm_frame.connectionStateChanged)
        signals.connection_state_signal[bool].emit(connected)

        data_plugins.set_read_only(is_app_read_only)

        original_tooltip = "Original Tooltip"
        pydm_frame.setToolTip(original_tooltip)
        pydm_frame.check_enable_state()

        actual_tooltip = pydm_frame.toolTip()
        if is_channel_valid(channel_address):
            if not pydm_frame._connected:
                assert "PV is disconnected." in actual_tooltip
            elif not write_access:
                if data_plugins.is_read_only():
                    assert "Running PyDM on Read-Only mode." in actual_tooltip
                else:
                    assert "Access denied by Channel Access Security." in actual_tooltip
        else:
            assert actual_tooltip == original_tooltip
