# Unit Tests for the PyDMSpinBox widget class


import pytest

from qtpy.QtWidgets import QApplication, QDoubleSpinBox
from qtpy.QtGui import QKeyEvent
from qtpy.QtCore import Property, QEvent, Qt

from ...widgets.spinbox import PyDMSpinbox
from ...tests.widgets.test_lineedit import find_action_from_menu


# --------------------
# POSITIVE TEST CASES
# --------------------

def test_construct(qtbot):
    """
    Test the construction of the widget.

    Expectations:
    All the default values are correctly assigned.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_spinbox = PyDMSpinbox()
    qtbot.addWidget(pydm_spinbox)

    assert pydm_spinbox.valueBeingSet is False
    assert pydm_spinbox.isEnabled() is False
    assert pydm_spinbox._show_step_exponent is True
    assert pydm_spinbox.step_exponent == 0
    assert pydm_spinbox.decimals() == 0
    assert pydm_spinbox.app == QApplication.instance()
    assert pydm_spinbox.isAccelerated() is True


@pytest.mark.parametrize("first_key_pressed, second_key_pressed, keys_pressed_expected_results", [
    (Qt.Key_Left, Qt.Key_Right, (2, 1)),
    (Qt.Key_Right, Qt.Key_Left, (-2, -1)),
])
def test_key_press_event(qtbot, signals, monkeypatch, first_key_pressed, second_key_pressed,
                         keys_pressed_expected_results):
    """
    Test the widget's handling of the key press events.

    Expectations:
    The step exponent value of the spin box will change as the Left Arrow or Right Arrow is pressed.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    monkeypatch : fixture
        To override default behaviors
    first_key_pressed : Qt.Key
        The first key to press to change the spinbox's step exponent value (increase or decrease)
    second_key_pressed: Qt.Key
        The second key to press to change the spinbox's step exponent value (increase or decrease)
    keys_pressed_expected_results : tuple
        The new value after the first key, and then that after the second key, is pressed
    """
    pydm_spinbox = PyDMSpinbox()
    qtbot.addWidget(pydm_spinbox)

    with qtbot.waitExposed(pydm_spinbox):
        pydm_spinbox.show()

    pydm_spinbox.step_exponent = 0
    pydm_spinbox._precision_from_pv = True
    signals.prec_signal[int].connect(pydm_spinbox.precisionChanged)
    signals.prec_signal[int].emit(3)

    INIT_SPINBOX_VALUE = 1.2
    signals.new_value_signal[float].connect(pydm_spinbox.channelValueChanged)
    signals.new_value_signal[float].emit(INIT_SPINBOX_VALUE)

    pydm_spinbox.setFocus()

    def wait_focus():
        return pydm_spinbox.hasFocus()
    qtbot.waitUntil(wait_focus, timeout=5000)

    def press_key_and_verify(key_pressed, key_mod, key_press_count, expected_exp, expected_value):
        if key_mod != Qt.NoModifier:
            # Monkeypatch the Control flag because in this test, we don't properly have the app QApplication instance
            monkeypatch.setattr(QApplication, "queryKeyboardModifiers", lambda *args: key_mod)
        else:
            monkeypatch.setattr(QApplication, "queryKeyboardModifiers", lambda *args: Qt.NoModifier)

        for i in range(0, key_press_count):
            pydm_spinbox.keyPressEvent(QKeyEvent(QEvent.KeyPress, key_pressed, key_mod))
        assert pydm_spinbox.step_exponent == expected_exp

        signals.send_value_signal[float].connect(signals.receiveValue)
        signals.send_value_signal[float].connect(pydm_spinbox.channelValueChanged)

        # Send out the key event to update the value based on the step exponent change
        pydm_spinbox.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier))
        assert pydm_spinbox.value == expected_value

    # Send out the first key event to effect the change of the step exponent
    press_key_and_verify(first_key_pressed, Qt.ControlModifier, 2, keys_pressed_expected_results[0],
                         INIT_SPINBOX_VALUE)

    # Send out the second key press event once to check if it can change the step exponent
    press_key_and_verify(second_key_pressed, Qt.ControlModifier, 1, keys_pressed_expected_results[1],
                         INIT_SPINBOX_VALUE)

    # Make sure the widget can process the UpArrow, DownArrow, PageUp, and PageDown keys
    pydm_spinbox.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Up, Qt.ControlModifier))
    pydm_spinbox.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Down, Qt.ControlModifier))
    pydm_spinbox.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_PageUp, Qt.ControlModifier))
    pydm_spinbox.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_PageDown, Qt.ControlModifier))


def test_widget_ctx_menu(qtbot):
    """
    Test to make sure the widget's context menu contains the specific action for the widget.

    Expectations:
    All specific actions for the widget's context menu are present in that menu.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_spinbox = PyDMSpinbox()
    qtbot.addWidget(pydm_spinbox)

    menu = pydm_spinbox.widget_ctx_menu()
    action_menu = menu.menuAction().menu()
    assert find_action_from_menu(action_menu, "Toggle Show Step Size")


@pytest.mark.parametrize("step_exp", [
    10,
    1,
    0.01,
    0,
    -10,
    -0.001
])
def test_update_step_size(qtbot, step_exp):
    """
    Test the incrementing of the widget's step exponent.

    Expectations:
    The widget's step exponent is incremented correctly, by verifying the value returned by the Qt API singleStep() is
    ten times the step exponent value.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    step_exp : int
        The new step exponent to set
    """
    pydm_spinbox = PyDMSpinbox()
    qtbot.addWidget(pydm_spinbox)

    pydm_spinbox.step_exponent = step_exp
    pydm_spinbox.update_step_size()

    assert pydm_spinbox.singleStep() == 10 ** step_exp


@pytest.mark.parametrize("show_unit, new_unit, step_exp, show_step_exp", [
    (True, "mJ", 0.01, True),
    (True, "light years", 10, True),
    (True, "s", -0.001, True),
    (True, "ms", 1, False),
    (False, "ns", 0.01, True),
    (False, "light years", 1, False),
])
def test_update_format_string(qtbot, signals, show_unit, new_unit, step_exp, show_step_exp):
    """
    Test the widget's capability of updating the format string when various unit and step exponent paramaters are
    updated. This method also test showStepExponent property and setter.

    Expectations:
    The format string is correctly produced.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    show_unit : bool
        True if the unit is to be displayed on the widget; False if otherwise
    new_unit : str
        The new unit to be displayed on the widget
    step_exp : int
        The step exponent for widget's values
    show_step_exp : bool
        True if the step exponent is to be displayed on the widget; False if otherwise
    """
    pydm_spinbox = PyDMSpinbox()
    qtbot.addWidget(pydm_spinbox)

    pydm_spinbox.step_exponent = step_exp
    pydm_spinbox.showStepExponent = show_step_exp
    assert pydm_spinbox.showStepExponent == show_step_exp

    INIT_SPINBOX_VALUE = 1.2
    signals.new_value_signal[float].connect(pydm_spinbox.channelValueChanged)
    signals.new_value_signal[float].emit(INIT_SPINBOX_VALUE)

    units = ""
    pydm_spinbox.showUnits = show_unit
    if show_unit:
        signals.unit_signal[str].connect(pydm_spinbox.unitChanged)
        signals.unit_signal.emit(new_unit)
        units = " {}".format(pydm_spinbox._unit)

        assert pydm_spinbox._unit == new_unit
    else:
        assert pydm_spinbox._unit == ""

    if show_step_exp:
        current_suffix = pydm_spinbox.suffix()
        expected_suffix = "{0} Step: 1E{1}".format(units, pydm_spinbox.step_exponent)
        assert current_suffix == expected_suffix
        assert pydm_spinbox.toolTip() == ""
    else:
        current_suffix = pydm_spinbox.suffix()
        expected_tooltip = "Step: 1E{0:+d}".format(pydm_spinbox.step_exponent)

        assert current_suffix == units
        assert pydm_spinbox.lineEdit().toolTip() == expected_tooltip


@pytest.mark.parametrize("init_value, user_typed_value, precision", [
    (123, 456, 3),
    (1.23, 4.56, 2),
    (1.23, 5, 0),
    (0, 12.3, 2),
    (-1.23, 4.6, 1)
])
def test_send_value(qtbot, signals, init_value, user_typed_value, precision):
    """
    Test sending the value from the widget to the channel. This method tests value_changed() and precision_changed().

    Expectations:
    The correct value is sent to the channelValueChanged slot.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    init_value : float
        The initial value assigned to the spinbox
    user_typed_value : float
        The new value sent to the spinbox via the channel
    precision : int
        The decimal decision for the spinbox's value
    """
    pydm_spinbox = PyDMSpinbox()
    qtbot.addWidget(pydm_spinbox)

    pydm_spinbox.setValue(init_value)

    pydm_spinbox._precision_from_pv = True
    signals.prec_signal[type(precision)].connect(pydm_spinbox.precisionChanged)
    signals.prec_signal[type(precision)].emit(precision)

    signal_type = type(user_typed_value)
    signals.new_value_signal[signal_type].connect(pydm_spinbox.channelValueChanged)
    signals.new_value_signal[signal_type].emit(user_typed_value)

    # Besides receiving the new channel value, simulate the update of the new value to the widget by connecting the
    # channelValueChanged slot to the same signal
    signals.send_value_signal[signal_type].connect(signals.receiveValue)
    signals.send_value_signal[signal_type].connect(pydm_spinbox.channelValueChanged)
    pydm_spinbox.send_value()

    assert pydm_spinbox.value == user_typed_value


@pytest.mark.parametrize("which_limit, new_limit", [
    ("UPPER", 123.456),
    ("LOWER", 12.345)
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
    pydm_spinbox = PyDMSpinbox()
    qtbot.addWidget(pydm_spinbox)

    if which_limit == "UPPER":
        signals.upper_ctrl_limit_signal[type(new_limit)].connect(pydm_spinbox.upperCtrlLimitChanged)
        signals.upper_ctrl_limit_signal[type(new_limit)].emit(new_limit)

        assert pydm_spinbox.get_ctrl_limits()[1] == new_limit
    elif which_limit == "LOWER":
        signals.lower_ctrl_limit_signal[type(new_limit)].connect(pydm_spinbox.lowerCtrlLimitChanged)
        signals.lower_ctrl_limit_signal[type(new_limit)].emit(new_limit)

        assert pydm_spinbox.get_ctrl_limits()[0] == new_limit
