import pytest
from logging import ERROR
import numpy as np

from qtpy.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QApplication, QSlider, QWidget
from qtpy.QtCore import Qt, QMargins, QPoint, QEvent, QRect, QSize
from qtpy.QtGui import QMouseEvent
from pydm.widgets.slider import PyDMSlider, PyDMPrimitiveSlider
from pydm.widgets.base import PyDMWidget
from pydm.utilities import checkObjectProperties

# Unit Tests for the PyDMPrimitiveSlider class


@pytest.fixture(scope="module")
def app():
    """Fixture to create a QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def horizontal_slider(app):
    """Fixture to create a PyDMPrimitiveSlider instance for each test."""
    test_slider = PyDMPrimitiveSlider(Qt.Horizontal)
    test_slider.setMinimum(0)
    test_slider.setMaximum(100)
    test_slider.setValue(50)
    test_slider.setSingleStep(1)
    test_slider.resize(200, 30)
    test_slider.show()
    return test_slider


@pytest.fixture
def vertical_slider(app):
    """Fixture to create a vertical PyDMPrimitiveSlider instance for each test."""
    test_slider = PyDMPrimitiveSlider(Qt.Vertical)
    test_slider.setMinimum(0)
    test_slider.setMaximum(100)
    test_slider.setValue(50)
    test_slider.setSingleStep(1)
    test_slider.resize(30, 200)
    test_slider.show()
    return test_slider


@pytest.mark.parametrize("slider_fixture", ["horizontal_slider", "vertical_slider"])
def test_mousePressEvent(slider_fixture, qtbot, request):
    """Test mousePressEvent when clicking off and on the handle"""
    test_slider = request.getfixturevalue(slider_fixture)
    handle_rect = test_slider.getHandleRect()

    if test_slider.orientation() == Qt.Horizontal:
        pos_off_handle = QPoint(handle_rect.right() + 10, handle_rect.center().y())
        increment = 1
    else:  # Vertical
        pos_off_handle = QPoint(handle_rect.center().x(), handle_rect.bottom() + 10)
        increment = -1

    qtbot.mouseClick(test_slider, Qt.LeftButton, pos=pos_off_handle)
    assert not test_slider.isDraggingHandle
    assert test_slider.value() == 50 + increment

    pos_on_handle = handle_rect.center()
    qtbot.mousePress(test_slider, Qt.LeftButton, pos=pos_on_handle)
    assert test_slider.isDraggingHandle
    assert test_slider.dragStartValue == test_slider.value()


@pytest.mark.parametrize("slider_fixture", ["horizontal_slider", "vertical_slider"])
def test_mouseMoveEvent(slider_fixture, qtbot, request):
    """Test the mouseMoveEvent method by posting QMouseEvent instances."""
    test_slider = request.getfixturevalue(slider_fixture)
    handle_rect = test_slider.getHandleRect()
    start_pos = handle_rect.center()
    drag_distance = 100

    if test_slider.orientation() == Qt.Horizontal:
        end_pos = QPoint(start_pos.x() + drag_distance, start_pos.y())
    else:
        end_pos = QPoint(start_pos.x(), start_pos.y() - drag_distance)

    initial_value = test_slider.value()

    press_event = QMouseEvent(
        QEvent.MouseButtonPress,
        start_pos,  # localPos
        start_pos,  # globalPos
        Qt.LeftButton,  # button
        Qt.LeftButton,  # buttons
        Qt.NoModifier,
    )  # modifiers
    QApplication.postEvent(test_slider, press_event)
    QApplication.processEvents()

    move_event = QMouseEvent(
        QEvent.MouseMove,
        end_pos,  # localPos
        end_pos,  # globalPos
        Qt.LeftButton,  # button
        Qt.LeftButton,  # buttons
        Qt.NoModifier,
    )  # modifiers
    QApplication.postEvent(test_slider, move_event)
    QApplication.processEvents()

    release_event = QMouseEvent(
        QEvent.MouseButtonRelease,
        end_pos,  # localPos
        end_pos,  # globalPos
        Qt.LeftButton,  # button
        Qt.LeftButton,  # buttons
        Qt.NoModifier,
    )  # modifier
    QApplication.postEvent(test_slider, release_event)
    QApplication.processEvents()

    actual_value = test_slider.value()

    assert actual_value != initial_value
    assert actual_value == 100


@pytest.mark.parametrize("slider_fixture", ["horizontal_slider", "vertical_slider"])
def test_mouseReleaseEvent(slider_fixture, qtbot, request):
    """Test mouseReleaseEvent to stop dragging."""
    test_slider = request.getfixturevalue(slider_fixture)
    handle_rect = test_slider.getHandleRect()
    pos_on_handle = handle_rect.center()
    qtbot.mousePress(test_slider, Qt.LeftButton, pos=pos_on_handle)
    assert test_slider.isDraggingHandle

    qtbot.mouseRelease(test_slider, Qt.LeftButton, pos=pos_on_handle)

    assert not test_slider.isDraggingHandle
    assert test_slider.cursor().shape() == Qt.ArrowCursor


@pytest.mark.parametrize("slider_fixture", ["horizontal_slider", "vertical_slider"])
def test_getHandleRect(slider_fixture, request):
    """Test getHandleRect method."""
    test_slider = request.getfixturevalue(slider_fixture)
    handle_rect = test_slider.getHandleRect()
    assert isinstance(handle_rect, QRect)
    assert test_slider.rect().contains(handle_rect)


@pytest.mark.parametrize("slider_fixture", ["horizontal_slider", "vertical_slider"])
def test_getPositions(slider_fixture, request):
    """Test getPositions method."""
    test_slider = request.getfixturevalue(slider_fixture)
    event = QMouseEvent(QEvent.MouseButtonPress, QPoint(50, 10), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    handle_pos, click_pos = test_slider.getPositions(event)
    assert isinstance(handle_pos, float)
    assert isinstance(click_pos, int)
    if test_slider.orientation() == Qt.Horizontal:
        assert 0 <= click_pos <= test_slider.width()
    else:
        assert 0 <= click_pos <= test_slider.height()


@pytest.mark.parametrize("slider_fixture", ["horizontal_slider", "vertical_slider"])
def test_shouldIncrement(slider_fixture, request):
    """Test shouldIncrement method."""
    test_slider = request.getfixturevalue(slider_fixture)

    if test_slider.orientation() == Qt.Horizontal:
        # Click is to the right of the handle
        assert test_slider.shouldIncrement(50, 70) is True
        # Click is to the left of the handle
        assert test_slider.shouldIncrement(70, 50) is False
    else:
        # Click is above the handle (smaller y)
        assert test_slider.shouldIncrement(70, 50) is True
        # Click is below the handle (larger y)
        assert test_slider.shouldIncrement(50, 70) is False


@pytest.mark.parametrize("slider_fixture", ["horizontal_slider", "vertical_slider"])
def test_getHandleSize(slider_fixture, request):
    """Test getHandleSize method."""
    test_slider = request.getfixturevalue(slider_fixture)
    handle_size = test_slider.getHandleSize()
    assert handle_size is not None
    assert isinstance(handle_size.width(), int)
    assert isinstance(handle_size.height(), int)

    if test_slider.orientation() == Qt.Horizontal:
        assert handle_size == QSize(20, test_slider.height() // 2)
    else:
        assert handle_size == QSize(test_slider.width() // 2, 20)


@pytest.mark.parametrize("slider_fixture", ["horizontal_slider", "vertical_slider"])
def test_getSliderLength(slider_fixture, request):
    """Test getSliderLength method."""
    test_slider = request.getfixturevalue(slider_fixture)
    slider_length = test_slider.getSliderLength()
    assert isinstance(slider_length, int)
    if test_slider.orientation() == Qt.Horizontal:
        assert slider_length <= test_slider.width()
    else:
        assert slider_length <= test_slider.height()


@pytest.mark.parametrize("slider_fixture", ["horizontal_slider", "vertical_slider"])
def test_getSliderPosition(slider_fixture, request):
    """Test getSliderPosition method."""
    test_slider = request.getfixturevalue(slider_fixture)
    slider_position = test_slider.getSliderPosition()
    assert isinstance(slider_position, float)
    if test_slider.orientation() == Qt.Horizontal:
        assert 0 <= slider_position <= test_slider.width()
    else:
        assert 0 <= slider_position <= test_slider.height()


# Unit Tests for the PyDMSlider Widget


# additional props we expect to get added to PyDMSlider class RULE_PROPERTIES
expected_slider_properties = {"Set Step Size ": ["step_size", float]}


def test_construct(qtbot):
    """
    Test the construction of the widget.

    Expectations:
    Default values are correctly assigned.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    parent = QWidget()
    qtbot.addWidget(parent)

    pydm_slider = PyDMSlider(parent)
    assert checkObjectProperties(pydm_slider, expected_slider_properties) is True
    qtbot.addWidget(pydm_slider)

    assert pydm_slider.alarmSensitiveContent is True
    assert pydm_slider.alarmSensitiveBorder is False
    assert pydm_slider._show_limit_labels is True
    assert pydm_slider._show_value_label is True
    assert pydm_slider._user_defined_limits is False
    assert pydm_slider._needs_limit_info is True
    assert pydm_slider._minimum is None
    assert pydm_slider._maximum is None
    assert pydm_slider._user_minimum == -10.0
    assert pydm_slider._user_maximum == 10.0
    assert pydm_slider._num_steps == 101
    assert pydm_slider.orientation == Qt.Horizontal
    assert pydm_slider.isEnabled() is False

    assert type(pydm_slider.low_lim_label) == QLabel
    assert pydm_slider.low_lim_label.sizePolicy() == QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    assert pydm_slider.low_lim_label.alignment() == Qt.Alignment(int(Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter))

    assert type(pydm_slider.high_lim_label) == QLabel
    assert pydm_slider.high_lim_label.sizePolicy() == QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    assert pydm_slider.high_lim_label.alignment() == Qt.Alignment(
        int(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
    )

    assert type(pydm_slider._slider) == PyDMPrimitiveSlider
    assert pydm_slider._slider.orientation() == Qt.Orientation(Qt.Horizontal)

    assert pydm_slider._slider_position_to_value_map is None
    assert pydm_slider._mute_internal_slider_changes is False
    assert pydm_slider._orientation == Qt.Horizontal
    assert pydm_slider.parent() == parent

    # This prevents pyside6 from deleting the internal c++ object
    # ("Internal C++ object (PyDMDateTimeLabel) already deleted")
    parent.deleteLater()
    pydm_slider.deleteLater()


def test_init_for_designer(qtbot):
    """
    Test the configuration method for using with Qt Designer.

    Expectations:
    The widget's internal value is set to 0.0.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_slider = PyDMSlider()
    qtbot.addWidget(pydm_slider)

    pydm_slider.init_for_designer()
    assert pydm_slider.value == 0.0


def test_actions_triggered(qtbot, signals):
    """
    Test emitting values via the widget's action slots.

    Expectations:
    The slot's actions are triggered.

    qtbot : fixture
        pytest-qt window for widget test
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    """
    pydm_slider = PyDMSlider()
    qtbot.addWidget(pydm_slider)

    signals.internal_slider_moved.connect(pydm_slider.internal_slider_action_triggered)
    signals.internal_slider_moved.emit(1)

    signals.internal_slider_clicked.connect(pydm_slider.internal_slider_pressed)
    signals.internal_slider_clicked.emit()

    signals.internal_slider_clicked.connect(pydm_slider.internal_slider_released)
    signals.internal_slider_clicked.emit()


@pytest.mark.parametrize(
    "new_value, mute_change",
    [
        (100.50, False),
        (-100, True),
    ],
)
def test_internal_slider_value_changed(qtbot, signals, new_value, mute_change):
    """
    Test widget's change of its text value if its internal value has changed.

    Expectations:
    If the `_mute_internal_slider_changes` flag is True, the value will not be propagated to PyDM, and the
    send_value_signal will not emit the new value (avoiding the infinite loop).

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    new_value : int
        The new value from changing the slider widget.
    mute_change : bool
        True if the new slider value is not to be propagated; False otherwise.
    """
    pydm_slider = PyDMSlider()
    qtbot.addWidget(pydm_slider)

    pydm_slider.userDefinedLimits = True
    pydm_slider.userMinimum = 10
    pydm_slider.userMaximum = 100

    pydm_slider.value = 123
    pydm_slider._mute_internal_slider_changes = mute_change

    # If the slider emits the new value, the fixture's receiveValue should get it. This should happen if the slider's
    # internal changes are not muted, and should NOT if it IS muted
    pydm_slider.send_value_signal[float].connect(signals.receiveValue)

    signals.new_value_signal[int].connect(pydm_slider.internal_slider_value_changed)
    signals.new_value_signal[int].emit(int(new_value))

    if not mute_change:
        # The internal_slider_value_changed_slot emitted the send_value_signal
        assert signals.value == pydm_slider.value
    else:
        # The internal_slider_value_changed_slot did NOT emit the send_value_signal. The signals fixture's value remains
        # unchanged
        assert signals.value is None


@pytest.mark.parametrize(
    "show_labels, orientation, tick_position",
    [
        # Test all QSlider.TickPosition values
        # Horizontal
        (True, Qt.Horizontal, QSlider.NoTicks),
        (True, Qt.Horizontal, QSlider.TicksBothSides),
        (True, Qt.Horizontal, QSlider.TicksAbove),
        (True, Qt.Horizontal, QSlider.TicksBelow),
        (False, Qt.Horizontal, QSlider.NoTicks),
        (False, Qt.Horizontal, QSlider.TicksBothSides),
        (False, Qt.Horizontal, QSlider.TicksAbove),
        (False, Qt.Horizontal, QSlider.TicksBelow),
        # Vertical
        (True, Qt.Vertical, QSlider.NoTicks),
        (True, Qt.Vertical, QSlider.TicksBothSides),
        (True, Qt.Vertical, QSlider.TicksLeft),
        (True, Qt.Vertical, QSlider.TicksRight),
        (False, Qt.Vertical, QSlider.NoTicks),
        (False, Qt.Vertical, QSlider.TicksBothSides),
        (False, Qt.Vertical, QSlider.TicksLeft),
        (False, Qt.Vertical, QSlider.TicksRight),
    ],
)
def test_properties_and_setters(qtbot, show_labels, orientation, tick_position):
    """
    Test the widget's various properties and setters.

    Expectations:
    The setters will update the values of the corresponding properties, which will return the up-to-date values.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    show_labels : bool
        True if the labels (min and max values) will be shown; False otherwise
    orientation : QSlider.TickPosition
        The orientation of slider we are testing
    tick_position : int
        The tick position for the slider component.
    """
    pydm_slider = PyDMSlider()
    qtbot.addWidget(pydm_slider)

    assert pydm_slider.orientation == Qt.Horizontal
    pydm_slider.orientation = orientation

    pydm_slider.tickPosition = tick_position
    assert pydm_slider.tickPosition == tick_position
    pydm_slider.num_steps = 5
    assert pydm_slider.num_steps == 5

    pydm_slider.showLimitLabels = show_labels
    assert pydm_slider.showLimitLabels == show_labels

    pydm_slider.showValueLabel = show_labels
    assert pydm_slider.showValueLabel == show_labels

    if show_labels:
        assert pydm_slider.low_lim_label.isVisibleTo(pydm_slider)
        assert pydm_slider.high_lim_label.isVisibleTo(pydm_slider)
        assert pydm_slider.value_label.isVisibleTo(pydm_slider)
    else:
        assert not pydm_slider.low_lim_label.isVisibleTo(pydm_slider)
        assert not pydm_slider.high_lim_label.isVisibleTo(pydm_slider)
        assert not pydm_slider.value_label.isVisibleTo(pydm_slider)


@pytest.mark.parametrize("new_orientation", [Qt.Horizontal, Qt.Vertical])
def test_setup_widgets_for_orientation(qtbot, new_orientation):
    """
    Test setting up the slider's orientation.

    Expectations:
    The widget's box layout and margins are correct for the general orientation of the widget.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    new_orientation : Orientation
        The orientation for the widget.
    """
    pydm_slider = PyDMSlider()
    qtbot.addWidget(pydm_slider)

    pydm_slider.setup_widgets_for_orientation(new_orientation)
    layout = pydm_slider.layout()
    assert layout

    if new_orientation == Qt.Horizontal:
        assert type(layout) == QVBoxLayout
        assert layout.parent() == pydm_slider
        assert layout.contentsMargins() == QMargins(4, 0, 4, 4)
        assert layout.count() == 2

        label_layout = layout.itemAt(0)
        assert type(label_layout) == QHBoxLayout
        assert label_layout.count() == 5
        assert all([label_layout.stretch(i) == 0 for i in range(0, label_layout.count())])
        assert pydm_slider.orientation == new_orientation
    elif new_orientation == Qt.Vertical:
        assert type(layout) == QHBoxLayout
        assert layout.parent() == pydm_slider
        assert layout.contentsMargins() == QMargins(0, 4, 4, 4)
        assert layout.count() == 2

        label_layout = layout.itemAt(0)
        assert type(label_layout) == QVBoxLayout
        assert label_layout.count() == 5
        assert all([label_layout.stretch(i) == 0 for i in range(0, label_layout.count())])
        assert pydm_slider._slider.orientation() == new_orientation


@pytest.mark.parametrize(
    "minimum, maximum",
    [
        (10, 20.5),
        (10, 1),
        (10, 20),
        (-10, 20.5),
    ],
)
def test_update_labels(qtbot, signals, minimum, maximum):
    """
    Test that changes in the user minimum and user maximum update the limit labels.

    Expectations:
    The widget's min and max are reflected correctly on the correponsiding labels.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    minimum : int
        The slider's minimum value as set by the user
    maximum : int
        The slider's maximum value as set by the user
    """

    def validate(value, widget):
        if value is None:
            assert widget.text() == ""
        else:
            assert widget.text() == str(float(value))

    pydm_slider = PyDMSlider()
    qtbot.addWidget(pydm_slider)

    pydm_slider.userDefinedLimits = True
    pydm_slider.userMinimum = minimum
    pydm_slider.userMaximum = maximum

    pydm_slider.update_labels()

    validate(minimum, pydm_slider.low_lim_label)
    validate(maximum, pydm_slider.high_lim_label)


@pytest.mark.parametrize(
    "minimum, maximum, write_access, connected",
    [
        (None, None, True, True),
        (None, 10, True, True),
        (10, None, True, True),
        (10, 20, True, True),
        (20, 20, True, True),
        (20, 30, True, True),
        (-10, 20, True, True),
        (10, 20, True, False),
        (10, 20, False, True),
        (10, 20, False, False),
    ],
)
def test_reset_slider_limits(qtbot, signals, minimum, maximum, write_access, connected):
    """
    Test the updating of the limits when the silder is reset.

    Expectations:
    The minimum and maximum limits, as well as the slider numeric steps, are updated correctly.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    minimum : int
        The user-defined minimum value for the slider
    maximum : int
        The user-defined maximum value for the slider
    write_access : bool
        True if the widget has write access to the data channel; False otherwise
    connected : bool
        True if the widget is connected to the data channel; False otherwise
    """
    pydm_slider = PyDMSlider()
    qtbot.addWidget(pydm_slider)

    pydm_slider.userDefinedLimits = True
    pydm_slider.userMinimum = minimum
    pydm_slider.userMaximum = maximum

    signals.write_access_signal[bool].connect(pydm_slider.writeAccessChanged)
    signals.write_access_signal[bool].emit(write_access)

    signals.connection_state_signal[bool].connect(pydm_slider.connectionStateChanged)
    signals.connection_state_signal[bool].emit(connected)

    pydm_slider.reset_slider_limits()

    if minimum is None or maximum is None:
        assert pydm_slider._needs_limit_info is True
    else:
        assert pydm_slider._needs_limit_info is False
        assert pydm_slider.userMinimum == minimum
        assert pydm_slider.userMaximum == maximum
        assert pydm_slider._slider.minimum() == 0
        assert pydm_slider._slider.maximum() == pydm_slider.num_steps
        assert pydm_slider._slider.singleStep() == 1
        assert pydm_slider._slider.pageStep() == 1
        assert np.array_equal(
            pydm_slider._slider_position_to_value_map,
            np.linspace(pydm_slider.minimum, pydm_slider.maximum, num=pydm_slider._num_steps),
        )
        assert pydm_slider.isEnabled() == (
            pydm_slider._write_access and pydm_slider._connected and not pydm_slider._needs_limit_info
        )


@pytest.mark.parametrize(
    "new_value, minimum, maximum",
    [
        (10, -10, 20),
        (-10, -10, 20),
        (20, -10, 20),
        (-200, -10, 20),
        (200, -10, 20),
        (0, 0, 0),
        (10, 10, 10),
    ],
)
def test_set_slider_to_closest_value(qtbot, new_value, minimum, maximum):
    """
    Test the calculation of the slider's value. Also test set_slider_to_closest_value().

    Expectations:
    Given the user's min and max values, and a value to move the slider to, the new position for the slider must be
    correctly calculated.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    new_value : int
        The new value for the widget
    expected_slider_value : int
        The new calculated widget value
    """
    pydm_slider = PyDMSlider()
    qtbot.addWidget(pydm_slider)

    pydm_slider.userDefinedLimits = True
    pydm_slider.userMinimum = minimum
    pydm_slider.userMaximum = maximum

    pydm_slider._slider.setValue(0)
    assert pydm_slider._slider.value() == 0

    expected_slider_value = np.argmin(abs(pydm_slider._slider_position_to_value_map - float(new_value)))
    pydm_slider.set_slider_to_closest_value(new_value)

    if new_value is None or pydm_slider._needs_limit_info:
        assert pydm_slider._slider.value() == 0
    else:
        assert pydm_slider._mute_internal_slider_changes is False
        assert pydm_slider._slider.value() == expected_slider_value


@pytest.mark.parametrize(
    "channel, alarm_sensitive_content, alarm_sensitive_border, new_alarm_severity",
    [
        (None, False, False, PyDMWidget.ALARM_NONE),
        (None, False, True, PyDMWidget.ALARM_NONE),
        (None, True, False, PyDMWidget.ALARM_NONE),
        (None, True, True, PyDMWidget.ALARM_NONE),
        (None, False, False, PyDMWidget.ALARM_MAJOR),
        (None, False, True, PyDMWidget.ALARM_MAJOR),
        (None, True, False, PyDMWidget.ALARM_MAJOR),
        (None, True, True, PyDMWidget.ALARM_MAJOR),
        ("", False, False, PyDMWidget.ALARM_NONE),
        ("", False, True, PyDMWidget.ALARM_NONE),
        ("", True, False, PyDMWidget.ALARM_NONE),
        ("", True, True, PyDMWidget.ALARM_NONE),
        ("", False, False, PyDMWidget.ALARM_MAJOR),
        ("", False, True, PyDMWidget.ALARM_MAJOR),
        ("", True, False, PyDMWidget.ALARM_MAJOR),
        ("", True, True, PyDMWidget.ALARM_MAJOR),
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
    ],
)
def test_alarm_severity_change(
    qtbot, signals, channel, alarm_sensitive_content, alarm_sensitive_border, new_alarm_severity
):
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
    pydm_slider = PyDMSlider()
    qtbot.addWidget(pydm_slider)

    pydm_slider._channel = channel
    pydm_slider.alarmSensitiveContent = alarm_sensitive_content
    pydm_slider.alarmSensitiveBorder = alarm_sensitive_border

    signals.new_severity_signal.connect(pydm_slider.alarmSeverityChanged)
    signals.new_severity_signal.emit(new_alarm_severity)


@pytest.mark.parametrize(
    "which_limit, new_limit, user_defined_limits",
    [
        ("UPPER", 10.5, True),
        ("UPPER", 10.123, False),
        ("LOWER", -10.5, True),
        ("LOWER", -10.123, False),
    ],
)
def test_ctrl_limit_changed(qtbot, signals, which_limit, new_limit, user_defined_limits):
    """
    Test the widget's handling of the upper and lower limit changes.

    Expectations:
    The correct limit change will be updated correctly.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    which_limit : str
        Indicator whether this limit to be updated an Upper or Lower limit.
    new_limit : float
        The new value of the limit
    user_defined_limits : bool
        True if the limit is to be defined by the user; False if by the channel.
    """
    pydm_slider = PyDMSlider()
    qtbot.addWidget(pydm_slider)

    pydm_slider.userDefinedLimits = user_defined_limits

    if which_limit == "UPPER":
        signals.upper_ctrl_limit_signal[type(new_limit)].connect(pydm_slider.upperCtrlLimitChanged)
        signals.upper_ctrl_limit_signal[type(new_limit)].emit(new_limit)

        assert pydm_slider.get_ctrl_limits()[1] == new_limit
    elif which_limit == "LOWER":
        signals.lower_ctrl_limit_signal[type(new_limit)].connect(pydm_slider.lowerCtrlLimitChanged)
        signals.lower_ctrl_limit_signal[type(new_limit)].emit(new_limit)

        assert pydm_slider.get_ctrl_limits()[0] == new_limit


@pytest.mark.parametrize(
    "value, precision, unit, show_unit, expected_format_string",
    [
        (123, 0, "s", True, "{:.0f} s"),
        (123.456, 3, "mV", True, "{:.3f} mV"),
    ],
)
def test_update_format_string(qtbot, value, precision, unit, show_unit, expected_format_string):
    """
    Test the unit conversion by examining the resulted format string.

    Expectations:

    Provided with the value, precision, unit, and the show unit Boolean flag by the user, this function must provide
    the correct format string to format the displayed value for the widget.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    value : int, float, bin, hex, numpy.array
        The value to be converted
    precision : int
        The
    unit : str
        The unit of the new value
    show_units : bool
        True if the value unit is to be displayed. False otherwise
    expected_format_string : str
        The expected format string that will produce the correct displayed value after the conversion
    """
    pydm_slider = PyDMSlider()
    qtbot.addWidget(pydm_slider)

    pydm_slider.value = value
    pydm_slider._unit = unit
    pydm_slider._prec = precision
    pydm_slider.showUnits = show_unit

    pydm_slider.update_format_string()
    assert pydm_slider.format_string == expected_format_string


# --------------------
# NEGATIVE TEST CASES
# --------------------


@pytest.mark.parametrize(
    "new_orientation",
    [
        -1,
        1000,
        None,
    ],
)
def test_setup_widgets_for_orientation_neg(qtbot, caplog, new_orientation):
    """
    Test the widget's handling of invalid orientation values.

    Expectations:
    An invalid orientation code will cause an error to be logged, and a message informing the user about the invalid
    orientation.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    caplog : fixture
        To capture the log messages
    new_orientation : int
        The invalid orientation value
    """
    pydm_slider = PyDMSlider()
    qtbot.addWidget(pydm_slider)

    pydm_slider.setup_widgets_for_orientation(new_orientation)

    for record in caplog.records:
        assert record.levelno == ERROR
    assert "Invalid orientation" in caplog.text
