# Unit Tests for the PyDMLineEdit Widget

import os
import platform
import pytest
import time

from pydm.widgets.datetime import PyDMDateTimeEdit, TimeBase
from qtpy.QtCore import QDateTime


@pytest.mark.parametrize(
    "init_channel",
    [
        "CA://MTEST",
        "",
        None,
    ],
)
def test_construct(qtbot, init_channel):
    """
    Test the widget construct.
    Expectations:
    All parameters have the correct default value.

    Parameters
    ----------
     qtbot : fixture
        Window for widget testing
    init_channel : str
        The data channel to be used by the widget

    """
    pydm_datetimeedit = PyDMDateTimeEdit(init_channel=init_channel)
    qtbot.addWidget(pydm_datetimeedit)

    if init_channel:
        assert pydm_datetimeedit.channel == str(init_channel)
    else:
        assert pydm_datetimeedit.channel is None

    assert pydm_datetimeedit.blockPastDate
    assert pydm_datetimeedit.relative
    assert pydm_datetimeedit.timeBase == TimeBase.Milliseconds


@pytest.mark.xfailif(
    platform.system() == "Windows",
    reason="These tests will fail on Windows, we can't easily modify time",
)
@pytest.mark.parametrize(
    "value, expected_value",
    [
        # Assuming the time is localized to EST
        (0, "1969/12/31 19:00:00.000"),
        (1000, "1969/12/31 19:00:01.000"),
        (60000, "1969/12/31 19:01:00.000"),
        (3600000, "1969/12/31 20:00:00.000"),
        (18000000, "1970/01/01 00:00:00.000"),
        (0.0, "1969/12/31 19:00:00.000"),
        (1000.0, "1969/12/31 19:00:01.000"),
        (60000.0, "1969/12/31 19:01:00.000"),
        (3600000.0, "1969/12/31 20:00:00.000"),
        (18000000.0, "1970/01/01 00:00:00.000"),
    ],
)
def test_value_changed(qtbot, signals, value, expected_value):
    """
    Test the widget's handling of the value changed event.

    Expectations:
    The following settings are in place after the value changed signal is emitted:
    1. The value displayed by the widget is the new value
    2. The value format maintained by the widget the correct format for the new value

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    value : int, float
        The value to be displayed by the widget
    expected_value : str
        The expected displayed value of the widget
    """
    # These tests will fail on Windows, we can't easily modify time
    if platform.system() == "Windows":
        return

    os.environ["TZ"] = "America/New_York"
    time.tzset()

    pydm_datetimeedit = PyDMDateTimeEdit()
    pydm_datetimeedit.blockPastDate = False
    pydm_datetimeedit.relative = False
    pydm_datetimeedit.timeBase = TimeBase.Milliseconds
    qtbot.addWidget(pydm_datetimeedit)

    signals.new_value_signal[type(value)].connect(pydm_datetimeedit.channelValueChanged)
    signals.new_value_signal[type(value)].emit(value)

    assert pydm_datetimeedit.text() == expected_value


@pytest.mark.xfail(
    platform.system() == "Windows",
    reason="These tests will fail on Windows, we can't easily modify time",
)
@pytest.mark.parametrize(
    "value, time_base",
    [
        (0, TimeBase.Milliseconds),
        (1000, TimeBase.Milliseconds),
        (60000, TimeBase.Milliseconds),
        (3600000, TimeBase.Milliseconds),
        (18000000, TimeBase.Milliseconds),
        (0.0, TimeBase.Milliseconds),
        (1000.0, TimeBase.Milliseconds),
        (60000.0, TimeBase.Milliseconds),
        (3600000.0, TimeBase.Milliseconds),
        (18000000.0, TimeBase.Milliseconds),
        (0, TimeBase.Seconds),
        (1000, TimeBase.Seconds),
        (60000, TimeBase.Seconds),
        (3600000, TimeBase.Seconds),
        (18000000, TimeBase.Seconds),
        (0.0, TimeBase.Seconds),
        (1000.0, TimeBase.Seconds),
        (60000.0, TimeBase.Seconds),
        (3600000.0, TimeBase.Seconds),
        (18000000.0, TimeBase.Seconds),
    ],
)
def test_value_round_trip(qtbot, value, time_base):
    """
    Test that using the widget as a setpoint is self-consistent.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    value : int, float
        The milliseconds from the epoch, whose type can vary
        depending on what widget we're hooked up to
    time_base : TimeBase
        Whether we're storing the time in seconds or milliseconds
    """
    os.environ["TZ"] = "America/New_York"
    time.tzset()

    pydm_datetimeedit = PyDMDateTimeEdit()
    pydm_datetimeedit.blockPastDate = False
    pydm_datetimeedit.relative = False
    pydm_datetimeedit.timeBase = time_base
    qtbot.addWidget(pydm_datetimeedit)

    last_value = None

    def collect_value(new_value):
        nonlocal last_value
        last_value = new_value

    goal_type = type(value)

    pydm_datetimeedit.channeltype = goal_type
    pydm_datetimeedit.send_value_signal[goal_type].connect(collect_value)

    dt = QDateTime()
    if time_base == TimeBase.Milliseconds:
        set_value = value
    elif time_base == TimeBase.Seconds:
        set_value = goal_type(value * 1000)
    else:
        raise RuntimeError(f"Please add new test branch for {time_base}")

    dt.setMSecsSinceEpoch(int(set_value))

    pydm_datetimeedit.setDateTime(dt)

    with qtbot.waitSignal(pydm_datetimeedit.send_value_signal[goal_type], timeout=1000):
        pydm_datetimeedit.send_value()

    assert last_value == value
