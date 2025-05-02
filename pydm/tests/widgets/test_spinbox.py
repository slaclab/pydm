# Unit Tests for the PyDMSpinBox widget class


import pytest

from qtpy.QtWidgets import QApplication, QWidget
from qtpy.QtGui import QKeyEvent
from qtpy.QtCore import QEvent, Qt

from pydm.widgets.spinbox import PyDMSpinbox
from pydm.tests.widgets.test_lineedit import find_action_from_menu


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
    parent = QWidget()
    qtbot.addWidget(parent)

    pydm_spinbox = PyDMSpinbox(parent)
    qtbot.addWidget(pydm_spinbox)

    assert pydm_spinbox.valueBeingSet is False
    assert pydm_spinbox.isEnabled() is False
    assert pydm_spinbox._show_step_exponent is True
    assert pydm_spinbox.step_exponent == 0
    assert pydm_spinbox.decimals() == 0
    assert pydm_spinbox.app == QApplication.instance()
    assert pydm_spinbox.isAccelerated() is True
    assert pydm_spinbox._write_on_press is False
    assert pydm_spinbox.parent() == parent

    # This prevents pyside6 from deleting the internal c++ object
    # ("Internal C++ object (PyDMDateTimeLabel) already deleted")
    parent.deleteLater()
    pydm_spinbox.deleteLater()


@pytest.mark.parametrize(
    "first_key_pressed, second_key_pressed, keys_pressed_expected_results",
    [
        (Qt.Key_Left, Qt.Key_Right, (2, 1)),
        (Qt.Key_Right, Qt.Key_Left, (-2, -1)),
    ],
)
def test_key_press_event(
    qtbot, signals, monkeypatch, first_key_pressed, second_key_pressed, keys_pressed_expected_results
):
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
    pydm_spinbox.setEnabled(True)

    with qtbot.waitExposed(pydm_spinbox):
        pydm_spinbox.show()

    pydm_spinbox.step_exponent = 0
    pydm_spinbox.precisionFromPV = True
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
    press_key_and_verify(first_key_pressed, Qt.ControlModifier, 2, keys_pressed_expected_results[0], INIT_SPINBOX_VALUE)

    # Send out the second key press event once to check if it can change the step exponent
    press_key_and_verify(
        second_key_pressed, Qt.ControlModifier, 1, keys_pressed_expected_results[1], INIT_SPINBOX_VALUE
    )

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


@pytest.mark.parametrize("step_exp", [10, 1, 0.01, 0, -10, -0.001])
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

    assert pydm_spinbox.singleStep() == 10**step_exp


@pytest.mark.parametrize(
    "show_unit, new_unit, step_exp, show_step_exp",
    [
        (True, "mJ", 0.01, True),
        (True, "light years", 10, True),
        (True, "s", -0.001, True),
        (True, "ms", 1, False),
        (False, "ns", 0.01, True),
        (False, "light years", 1, False),
    ],
)
def test_update_format_string(qtbot, signals, show_unit, new_unit, step_exp, show_step_exp):
    """
    Test the widget's capability of updating the format string when various unit and step exponent parameters are
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


@pytest.mark.parametrize(
    "init_value, user_typed_value, precision",
    [(123, 456, 3), (1.23, 4.56, 2), (1.23, 5, 0), (0, 12.3, 2), (-1.23, 4.6, 1)],
)
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

    pydm_spinbox.precisionFromPV = True
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


@pytest.mark.parametrize(
    "which_limit, new_limit, user_defined_limits",
    [("UPPER", 123.456, False), ("LOWER", 12.345, False), ("UPPER", 987.654, True), ("LOWER", 9.321, True)],
)
def test_ctrl_limit_changed(qtbot, signals, which_limit, new_limit, user_defined_limits):
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
    user_defined_limits : bool
        True if the spinbox should set its range based on user defined values, False if it should take its
        range from the PV itself
    """
    pydm_spinbox = PyDMSpinbox()
    qtbot.addWidget(pydm_spinbox)
    pydm_spinbox.userDefinedLimits = user_defined_limits
    pydm_spinbox.userMinimum = -10.5
    pydm_spinbox.userMaximum = 10.5
    pydm_spinbox.precisionFromPV = False
    pydm_spinbox.precision = 3

    if which_limit == "UPPER":
        signals.upper_ctrl_limit_signal[type(new_limit)].connect(pydm_spinbox.upperCtrlLimitChanged)
        signals.upper_ctrl_limit_signal[type(new_limit)].emit(new_limit)

        assert pydm_spinbox.get_ctrl_limits()[1] == new_limit
        if not user_defined_limits:
            # Not user_defined_limits means the range of the spinbox should stay in sync with the PV
            assert pydm_spinbox.maximum() == new_limit
        else:
            # Otherwise while we still store the limits on the base widget, the spinbox remains at the user-set values
            assert pydm_spinbox.maximum() == 10.5
    elif which_limit == "LOWER":
        signals.lower_ctrl_limit_signal[type(new_limit)].connect(pydm_spinbox.lowerCtrlLimitChanged)
        signals.lower_ctrl_limit_signal[type(new_limit)].emit(new_limit)

        assert pydm_spinbox.get_ctrl_limits()[0] == new_limit
        if not user_defined_limits:
            assert pydm_spinbox.minimum() == new_limit
        else:
            assert pydm_spinbox.minimum() == -10.5


def test_reset_limits(qtbot):
    """
    Test that when reset_limits() is called, the range of the spinbox is set as expected
    """
    # Set up a spinbox with some initial user set limits
    pydm_spinbox = PyDMSpinbox()
    qtbot.addWidget(pydm_spinbox)
    pydm_spinbox.userDefinedLimits = True
    pydm_spinbox.userMinimum = -10.5
    pydm_spinbox.userMaximum = 10.5
    pydm_spinbox.precisionFromPV = False
    pydm_spinbox.precision = 1

    # Also set a couple limits based on info we could have gotten back from the channel
    pydm_spinbox._lower_ctrl_limit = -5
    pydm_spinbox._upper_ctrl_limit = 5

    # This first call to reset_limits should essentially do nothing as nothing has happened
    # that would cause the range of the spinbox to change
    pydm_spinbox.reset_limits()
    assert pydm_spinbox.minimum() == -10.5
    assert pydm_spinbox.maximum() == 10.5

    # Turning off user defined limits should now cause the range to be set by the values received from the channel
    pydm_spinbox.userDefinedLimits = False
    assert pydm_spinbox.minimum() == -5
    assert pydm_spinbox.maximum() == 5

    # Finally flip it back to ensure it switches back to the user-defined range as expected
    pydm_spinbox.userDefinedLimits = True
    assert pydm_spinbox.minimum() == -10.5
    assert pydm_spinbox.maximum() == 10.5


@pytest.mark.parametrize(
    "key_pressed, initial_spinbox_value, expected_result, write_on_press",
    [
        (Qt.Key_Up, 1, 2, True),
        (Qt.Key_Down, 1, 0, True),
        (Qt.Key_Up, 1, 1, False),
        (Qt.Key_Down, 1, 1, False),
    ],
)
def test_write_on_press(
    qtbot, signals, monkeypatch, key_pressed, initial_spinbox_value, expected_result, write_on_press
):
    """
    Test sending the value from the widget to the channel on key press when writeOnPress enabled.

    Expectations:
    The correct value is sent to the channelValueChanged slot on key press and no value is send when disabled.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    monkeypatch : fixture
        To override default behaviors
    key_pressed : Qt.Key
        The key to press to change the spinbox's step exponent value (increase or decrease)
    inital_spinbox_value: float
        Initial value assigned to spinbox
    expected_result : float
        Value expected after key press
    write_on_press: bool
        Whether or not to enable write on press
    """
    pydm_spinbox = PyDMSpinbox()
    qtbot.addWidget(pydm_spinbox)

    with qtbot.waitExposed(pydm_spinbox):
        pydm_spinbox.show()

    pydm_spinbox.step_exponent = 0
    pydm_spinbox.precisionFromPV = True
    signals.prec_signal[int].connect(pydm_spinbox.precisionChanged)
    signals.prec_signal[int].emit(3)

    # set up signals
    pydm_spinbox.send_value_signal[float].connect(signals.receiveValue)
    signals.new_value_signal[float].connect(pydm_spinbox.channelValueChanged)
    signals.new_value_signal[float].emit(initial_spinbox_value)

    def press_key_and_verify(key_pressed, key_mod, expected_value, write_on_press):
        # reset value to initial value
        pydm_spinbox.value_changed(initial_spinbox_value)
        pydm_spinbox.send_value()

        #  use modifier if left/right keys
        if key_mod != Qt.NoModifier:
            # Monkeypatch the Control flag because in this test, we don't properly have the app QApplication instance
            monkeypatch.setattr(QApplication, "queryKeyboardModifiers", lambda *args: key_mod)
        else:
            monkeypatch.setattr(QApplication, "queryKeyboardModifiers", lambda *args: Qt.NoModifier)

        pydm_spinbox.writeOnPress = write_on_press
        pydm_spinbox.keyPressEvent(QKeyEvent(QEvent.KeyPress, key_pressed, key_mod))

        # Check for change if write on press enabled
        if pydm_spinbox.writeOnPress:
            assert signals.value == expected_value

        # Check for no change if disabled
        else:
            assert signals.value == initial_spinbox_value

    # check the key press with write_on_press
    press_key_and_verify(key_pressed, Qt.NoModifier, expected_result, write_on_press)

    # check that changing the exponent does not modify
    press_key_and_verify(Qt.Key_Left, Qt.ControlModifier, initial_spinbox_value, write_on_press)
    press_key_and_verify(Qt.Key_Right, Qt.ControlModifier, initial_spinbox_value, write_on_press)
