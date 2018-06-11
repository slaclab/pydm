# Unit Tests for the PyDMCheckbox Widget

import pytest
from ...widgets.checkbox import PyDMCheckbox


# --------------------
# POSITIVE TEST CASES
# --------------------

@pytest.mark.parametrize("init_channel", [
    "CA://MTEST",
    "",
    None,
])
def test_construct(qtbot, init_channel):
    """
    Test the widget construct.

    Expectations:
    The widget's initial state is unchecked.

    Parameters
    ----------
     qtbot : fixture
        Window for widget testing
    init_channel : str
        The data channel to be used by the widget
    """
    pydm_checkbox = PyDMCheckbox(init_channel=init_channel)
    qtbot.addWidget(pydm_checkbox)

    assert not pydm_checkbox.isChecked()


@pytest.mark.parametrize("init_checked_status, new_value", [
    (True, 0),
    (True, -1),
    (False, 0),
    (False, -66),
    (True, 1),
    (False, 1),
    (True, 999),
    (False, 999),
])
def test_value_changed(qtbot, signals, init_checked_status, new_value):
    """

    Test the widget's checked status when the value changes via the data channel.

    Expectations:

    1. If the channel data value is larger than 0, the widget is checked
    2. The widget is unchecked if the channel value is 0

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    init_checked_status : bool
        True if the widget is initially checked; False otherwise
    new_value : int
        The value sent to the widget from the channel
    """
    pydm_checkbox = PyDMCheckbox()
    qtbot.addWidget(pydm_checkbox)

    pydm_checkbox.setChecked(init_checked_status)

    signals.send_value_signal[type(new_value)].connect(pydm_checkbox.channelValueChanged)
    signals.send_value_signal[type(new_value)].emit(new_value)

    assert pydm_checkbox.isChecked() if new_value > 0 else not pydm_checkbox.isChecked()


@pytest.mark.parametrize("is_checked", [
    True,
    False,
    None,
])
def test_send_value(qtbot, signals, is_checked):
    """
    Test the data sent from the widget to the channel when the widget is checked or unchecked.

    Expectations:

    1. If the widget is checked, it will send out 1 as the value to the channel
    2. If the widget is unchecked, it will send out 0 as the value to the channel

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    is_checked : bool
        True if the widget is checked before sending out the value; False if it is not checked
    """
    pydm_checkbox = PyDMCheckbox()
    qtbot.addWidget(pydm_checkbox)

    pydm_checkbox.send_value_signal[int].connect(signals.receiveValue)
    pydm_checkbox.send_value(is_checked)

    assert signals.value == 1 if is_checked else signals.value == 0

