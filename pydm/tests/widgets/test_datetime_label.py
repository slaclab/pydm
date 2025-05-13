# Unit Tests for the PyDMLabel Widget


import os
import platform
import pytest
import time

from pydm.widgets.datetime import PyDMDateTimeLabel, TimeBase

# --------------------
# POSITIVE TEST CASES
# --------------------


def test_construct(qtbot):
    """
    Test the basic instantiation of the widget.

    Expectations:
    The widget was created with the following default settings:
    1. DisplayFormat is Default
    2. String encoding is the same as that specified in the PyDM App, or UTF-8

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_label = PyDMDateTimeLabel()

    qtbot.addWidget(pydm_label)

    assert pydm_label.relative == True
    assert pydm_label.timeBase == TimeBase.Milliseconds
    assert pydm_label.textFormat == "yyyy/MM/dd hh:mm:ss.zzz"


@pytest.mark.parametrize(
    "value, text_format, expected_value",
    [
        # Assuming the time is localized to EST
        (0, "yyyy-MM-dd", "1969-12-31"),
        (0, "yyyy-MM-dd-hh-mm-ss-zzz", "1969-12-31-19-00-00-000"),
        (1000, "yyyy-MM-dd-hh-mm-ss-zzz", "1969-12-31-19-00-01-000"),
        (60000, "yyyy-MM-dd-hh-mm-ss-zzz", "1969-12-31-19-01-00-000"),
        (3600000, "yyyy-MM-dd-hh-mm-ss-zzz", "1969-12-31-20-00-00-000"),
        (18000000, "yyyy-MM-dd-hh-mm-ss-zzz", "1970-01-01-00-00-00-000"),
        (0.0, "yyyy-MM-dd", "1969-12-31"),
        (0.0, "yyyy-MM-dd-hh-mm-ss-zzz", "1969-12-31-19-00-00-000"),
        (1000.0, "yyyy-MM-dd-hh-mm-ss-zzz", "1969-12-31-19-00-01-000"),
        (60000.0, "yyyy-MM-dd-hh-mm-ss-zzz", "1969-12-31-19-01-00-000"),
        (3600000.0, "yyyy-MM-dd-hh-mm-ss-zzz", "1969-12-31-20-00-00-000"),
        (18000000.0, "yyyy-MM-dd-hh-mm-ss-zzz", "1970-01-01-00-00-00-000"),
    ],
)
def test_value_changed(qtbot, signals, value, text_format, expected_value):
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
    text_format : str
        The format of the widget's displayed value
    expected_value : str
        The expected displayed value of the widget
    """
    # These tests will fail on Windows, we can't easily modify time
    if platform.system() == "Windows":
        return

    os.environ["TZ"] = "US/Eastern"
    time.tzset()

    pydm_label = PyDMDateTimeLabel()
    pydm_label.relative = False
    pydm_label.timeBase = TimeBase.Milliseconds
    pydm_label.textFormat = text_format
    qtbot.addWidget(pydm_label)

    signals.new_value_signal[type(value)].connect(pydm_label.channelValueChanged)
    signals.new_value_signal[type(value)].emit(value)

    assert pydm_label.textFormat == text_format
    assert pydm_label.text() == expected_value
