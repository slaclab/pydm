import pytest

from qtpy.QtCore import Qt, QSize

from ...widgets.enum_button import PyDMEnumButton, WidgetType, class_for_type
from ... import data_plugins


def test_construct(qtbot):
    """
    Test the construction of the widget.

    Expectations:
    All the default values are properly set.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    """
    widget = PyDMEnumButton()
    qtbot.addWidget(widget)

    assert widget._has_enums is False
    assert widget.orientation == Qt.Vertical
    assert widget.widgetType == WidgetType.PushButton
    assert widget.minimumSizeHint() == QSize(50, 100)


@pytest.mark.parametrize("widget_type", [
    WidgetType.PushButton,
    WidgetType.RadioButton
])
def test_widget_type(qtbot, widget_type):
    """
    Test the widget for a change in the widget type.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    widget_type : WidgetType
        The type of widget to use.
    """
    widget = PyDMEnumButton()
    qtbot.addWidget(widget)

    assert widget.widgetType == WidgetType.PushButton
    assert isinstance(widget._widgets[0], class_for_type[WidgetType.PushButton])

    widget.widgetType = widget_type
    assert widget.widgetType == widget_type
    assert isinstance(widget._widgets[0], class_for_type[widget_type])


@pytest.mark.parametrize("orientation", [
    Qt.Horizontal,
    Qt.Vertical
])
def test_widget_orientation(qtbot, orientation):
    """
    Test the widget for a change in the orientation.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    orientation : int
        One of Qt.Vertical or Qt.Horizontal
    """
    widget = PyDMEnumButton()
    qtbot.addWidget(widget)

    assert widget.orientation == Qt.Vertical

    widget.orientation = orientation
    assert widget.orientation == orientation

    if orientation == Qt.Horizontal:
        row = 0
        col = 1
    else:
        row = 1
        col = 0

    item = widget.layout().itemAtPosition(row, col)
    assert item is not None
    w = item.widget()
    assert w is not None
    assert isinstance(w, class_for_type[widget.widgetType])


@pytest.mark.parametrize("connected, write_access, has_enum, is_app_read_only", [
    (True, True, True, True),
    (True, True, True, False),

    (True, True, False, True),
    (True, True, False, False),

    (True, False, False, True),
    (True, False, False, False),

    (True, False, True, True),
    (True, False, True, False),

    (False, True, True, True),
    (False, True, True, False),

    (False, False, True, True),
    (False, False, True, False),

    (False, True, False, True),
    (False, True, False, False),

    (False, False, False, True),
    (False, False, False, False),
])
def test_check_enable_state(qtbot, signals, connected, write_access, has_enum,
                            is_app_read_only):
    """
    Test the tooltip generated depending on the channel connection, write access,
    whether the widget has enum strings,
    and whether the app is read-only.

    Expectations:
    1. If the data channel is disconnected, the widget's tooltip will display "PV is disconnected"
    2. If the data channel is connected, but it has no write access:
        a. If the app is read-only, the tooltip will read  "Running PyDM on Read-Only mode."
        b. If the app is not read-only, the tooltip will read "Access denied by Channel Access Security."
    3. If the widget does not have any enum strings, the tooltip will display "Enums not available".

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    connected : bool
        True if the channel is connected; False otherwise
    write_access : bool
        True if the widget has write access to the channel; False otherwise
    has_enum: bool
        True if the widget has enum strings populated; False if the widget contains no enum strings (empty of choices)
    is_app_read_only : bool
        True if the PyDM app is read-only; False otherwise
    """
    widget = PyDMEnumButton()
    qtbot.addWidget(widget)

    signals.write_access_signal[bool].connect(widget.writeAccessChanged)
    signals.write_access_signal[bool].emit(write_access)

    signals.connection_state_signal[bool].connect(widget.connectionStateChanged)
    signals.connection_state_signal[bool].emit(connected)

    if has_enum:
        signals.enum_strings_signal[tuple].connect(widget.enumStringsChanged)
        signals.enum_strings_signal[tuple].emit(("START", "STOP", "PAUSE"))
        assert widget._has_enums

    data_plugins.set_read_only(is_app_read_only)

    original_tooltip = "Original Tooltip"
    widget.setToolTip(original_tooltip)
    widget.check_enable_state()

    actual_tooltip = widget.toolTip()
    if not widget._connected:
        assert "Channel is disconnected." in actual_tooltip
    elif not write_access:
        if data_plugins.is_read_only():
            assert "Running PyDM on Read-Only mode." in actual_tooltip
        else:
            assert "Access denied by Channel Access Security." in actual_tooltip
    elif not widget._has_enums:
        assert "Enums not available" in actual_tooltip


def test_send_receive_value(qtbot, signals):
    """
    Test the widget for round-trip data transfer.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    """
    widget = PyDMEnumButton()
    qtbot.addWidget(widget)

    signals.write_access_signal[bool].connect(widget.writeAccessChanged)
    signals.connection_state_signal[bool].connect(widget.connectionStateChanged)
    signals.new_value_signal[int].connect(widget.channelValueChanged)
    signals.enum_strings_signal[tuple].connect(widget.enumStringsChanged)

    widget.send_value_signal[int].connect(signals.receiveValue)

    signals.write_access_signal[bool].emit(True)
    signals.connection_state_signal[bool].emit(True)
    signals.enum_strings_signal[tuple].emit(("START", "STOP", "PAUSE"))

    signals.new_value_signal[int].emit(1)
    assert widget.value == 1
    assert widget._widgets[1].isChecked()
    widget._widgets[2].click()
    assert not widget._widgets[1].isChecked()
    assert widget._widgets[2].isChecked()
    assert signals.value == 2
