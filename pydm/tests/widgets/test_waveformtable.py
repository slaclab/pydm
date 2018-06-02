# Unit Tests for the PyDM Waveform Table Widget


import pytest

from ...PyQt.QtGui import QTableWidgetItem, QApplication
from ...PyQt.QtCore import pyqtProperty, Qt, QEvent
import numpy as np
from ...application import PyDMApplication
from ...widgets.waveformtable import PyDMWaveformTable


def test_construct(qtbot):
    """
    Test the construction of the widget.

    Expectations:
    Correct default values are assigned.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_waveformtable = PyDMWaveformTable()
    qtbot.addWidget(pydm_waveformtable)

    assert pydm_waveformtable._columnHeaders == ["Value"]
    assert pydm_waveformtable._rowHeaders == []
    assert pydm_waveformtable._itemsFlags == (Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
    assert pydm_waveformtable.waveform is None
    assert pydm_waveformtable._valueBeingSet is False
    assert pydm_waveformtable.columnCount() == 1


@pytest.mark.parametrize("new_waveform", [
    np.array([[ -1, 2]]),
    np.array([[ 0, 0]]),
    np.array([[ -1, 2], [-4, -5]]),
    np.array([[ 0, 0], [0, 0]]),
    np.array([[ -1, 2, -3], [-4, -5, 6]]),
    np.array([[0, 0, 0], [0, 0, 0]]),
    np.array([[ -1, 2], [3, 4], [-5, 6]]),
    np.array([[ 0, 0], [0, 0], [0, 0]]),
    np.array([[ -1, 2, -3], [-4, -5, 6], [7, 8, 9]]),
    np.array([[ -10.123, 20.345, -32.789], [-4.0, -52.345, 6.78], [7.12, 8.45, 9.89]]),
    np.array([[ 0, 0, 0], [0, 0, 0], [0, 0, 0]]),
])
def test_value_changed(qtbot, signals, new_waveform):
    """
    Test the widget's handling of the channel value change event.

    Expectations:
    Each cell of the Waveform Table contains the correct data value.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    new_waveform : numpy.array
        The array of waveform data values
    """
    pydm_waveformtable = PyDMWaveformTable()
    qtbot.addWidget(pydm_waveformtable)

    signals.new_value_signal[np.ndarray].connect(pydm_waveformtable.channelValueChanged)
    signals.new_value_signal[np.ndarray].emit(new_waveform)

    assert np.array_equal(pydm_waveformtable.waveform, new_waveform)

    col_count = pydm_waveformtable.columnCount()
    len_wave = len(new_waveform)
    assert pydm_waveformtable.rowCount() == len_wave//col_count + (1 if len_wave % col_count else 0)

    for index, element, in enumerate(new_waveform):
        value_cell = QTableWidgetItem(str(element))
        value_cell.setFlags(pydm_waveformtable._itemsFlags)

        i, j = index // col_count, index % col_count
        assert pydm_waveformtable.item(i, j).text() == value_cell.text()

    assert pydm_waveformtable._valueBeingSet is False


@pytest.mark.parametrize("value_being_set", [
    False,
    True
])
def test_send_waveform(qtbot, signals, value_being_set):
    """
    Test the widget's updating of the channel's value when the cell value is changed.

    Expectations:
    The send_value_signal will emit the waveform containing the new data in a table cell.

    If the value_being_set flag is True, the new data will not be emitted to the channel. If it is False, the new data
    will be emitted.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    value_being_set : bool
        True
    """
    pydm_waveformtable = PyDMWaveformTable()
    qtbot.addWidget(pydm_waveformtable)

    waveform = np.array([1, 2, 3])
    signals.new_value_signal[np.ndarray].connect(pydm_waveformtable.channelValueChanged)
    signals.new_value_signal[np.ndarray].emit(waveform)

    pydm_waveformtable._valueBeingSet = value_being_set

    # Update the value at cell (0, 0) then emit the waveform back to the channel, while intercepting that waveform
    # to confirm
    pydm_waveformtable.send_value_signal[np.ndarray].connect(signals.receiveValue)
    signals.waveform_signal[int, int].connect(pydm_waveformtable.send_waveform)
    signals.waveform_signal[int, int].emit(0, 0)

    if value_being_set:
        assert signals.value is None
    else:
        assert np.array_equal(signals.value, waveform)


@pytest.mark.parametrize("channel_address, connected, write_access, is_app_read_only", [
    ("CA://MA_TEST", True, True, True),
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
    (None, False, False, False),
])
def test_check_enable_state(qtbot, signals, monkeypatch, channel_address, connected, write_access, is_app_read_only):
    """
    Test the widget's ability to make individual cells editable when there is write access.

    Expectations:
    1. If the widget has both write access and is connected to the channel, each cell must be selectable, editable, and
       is enabled.

    2. If the weidget is only connected to the channel, each cell must be selectable and enabled, but not editable.

    3. Otherwise, each cell can only be selectable.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
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
    pydm_waveformtable = PyDMWaveformTable()
    qtbot.addWidget(pydm_waveformtable)

    pydm_waveformtable.channel = channel_address
    pydm_waveformtable._connected = connected
    pydm_waveformtable._write_access = write_access

    monkeypatch.setattr(PyDMApplication, 'is_read_only', lambda *args: is_app_read_only)

    waveform = np.array([1, 2, 3])
    signals.new_value_signal[np.ndarray].connect(pydm_waveformtable.channelValueChanged)
    signals.new_value_signal[np.ndarray].emit(waveform)

    pydm_waveformtable.check_enable_state()
    assert pydm_waveformtable.isEnabled()

    item_flags = pydm_waveformtable._itemsFlags
    if pydm_waveformtable._write_access and pydm_waveformtable._connected:
        assert item_flags == Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
    elif pydm_waveformtable._connected:
        assert item_flags == Qt.ItemIsSelectable | Qt.ItemIsEnabled
    else:
        assert item_flags == Qt.ItemIsSelectable

    for col in range(0, pydm_waveformtable.columnCount()):
        for row in range(0, pydm_waveformtable.rowCount()):
            item = pydm_waveformtable.item(row, col)
            if item is not None:
                # Confirm the cell has the correct edit flags
                assert item.flags() == item_flags


@pytest.mark.parametrize("event_type, connected", [
    # (QEvent.Enter, True) is undefined
    (QEvent.Leave, True),
    (QEvent.Leave, False),
    (QEvent.Enter, False)
])
def test_event_filter(qtbot, monkeypatch, event_type, connected):
    """
    Test the widget's handling of Qt.Enter and Qt.Leave events.

    This is accomplished by generate a mousePress event to trigger evenFilter(), then monkeypatch the event type to test
    the cursor settings, and that's the purpose of this test.

    Expectations:

    1. The mouse cursor will be an arrow if the event type is Qt.Leave, or if the event type is Qt.Enter while the
       widget has the channel connection
    2. The mouse cursor will be the Forbidden cursor if the event tpe is Qt.Enter while the widget doesn't have the
        channel connection.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To simulate the Qt.Enter and Qt.Leave event types.
    event_type : Qt.Event
        The event type to simulate (either Qt.Enter or Qt.Leave)
    connected : bool
        True if the widget is connected to the channel; False otherwise
    """
    pydm_waveformtable = PyDMWaveformTable()
    qtbot.addWidget(pydm_waveformtable)

    pydm_waveformtable._connected = connected

    monkeypatch.setattr(QEvent, "type", lambda *args: event_type)
    qtbot.mousePress(pydm_waveformtable, Qt.LeftButton, delay=3)

    if event_type == QEvent.Leave:
        assert QApplication.overrideCursor().shape() == Qt.ArrowCursor
    elif event_type == QEvent.Enter:
        if not connected:
            assert QApplication.overrideCursor().shape() == Qt.ForbiddenCursor
        else:
            assert QApplication.overrideCursor().shape() == Qt.ArrowCursor


@pytest.mark.parametrize("new_labels", [
    ["Test Label 1"],
    ["Test Label 1", "Test Label 2", "Test Label 3"],
    ["Test Label 1", "", "Test Label 3"],
    ["Test Label 1", None, "Test Label 3"],
    [""],
    ["", "", ""],
    ["", None, ""],
    [None, None, None],
    ["Test Label 1", "Test Label 2", "Test Label 3", "Test Label 4"],
])
def test_properties_and_setters(qtbot, signals, new_labels):
    """
    Test various properties and setters of the widgets.

    Expectations:
    The properties will provide the latest corresponding values, and the setters will update the values correctly.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    new_labels : list
        A list of the label strings (used for testing updating both row and column labels)
    """
    pydm_waveformtable = PyDMWaveformTable()
    qtbot.addWidget(pydm_waveformtable)

    waveform = np.array([[ -10.123, 20.345, -32.789], [-4.0, -52.345, 6.78], [7.12, 8.45, 9.89]])
    signals.new_value_signal[np.ndarray].connect(pydm_waveformtable.channelValueChanged)
    signals.new_value_signal[np.ndarray].emit(waveform)

    assert pydm_waveformtable.columnHeaderLabels == ["Value"]
    pydm_waveformtable.columnHeaderLabels = new_labels

    if new_labels:
        new_labels += (pydm_waveformtable.columnCount() - len(new_labels)) * [""]
    assert pydm_waveformtable.columnHeaderLabels == new_labels

    assert pydm_waveformtable.rowHeaderLabels == []
    pydm_waveformtable.rowHeaderLabels = new_labels

    if new_labels:
        new_labels += (pydm_waveformtable.rowCount() - len(new_labels)) * [""]
    assert pydm_waveformtable.rowHeaderLabels == new_labels






