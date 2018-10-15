# Unit Tests for the Enum Combo Box

import pytest
from logging import ERROR

from qtpy.QtCore import Slot, Qt

from ...widgets.enum_combo_box import PyDMEnumComboBox
from ... import data_plugins


# --------------------
# POSITIVE TEST CASES
# --------------------

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
    pydm_enumcombobox = PyDMEnumComboBox()
    qtbot.addWidget(pydm_enumcombobox)

    assert pydm_enumcombobox._has_enums is False
    assert pydm_enumcombobox.contextMenuPolicy() == Qt.DefaultContextMenu
    assert pydm_enumcombobox.contextMenuEvent == pydm_enumcombobox.open_context_menu


@pytest.mark.parametrize("enums", [
    ("spam", "eggs", "ham"),
    ("spam",),
    ("",),
])
def test_set_items(qtbot, enums):
    """
    Test the populating of enum string (choices) to the widget.

    Expectations:
    All enum strings are populated to the widget, and the _has_enum flag is set to True if the enum string list is not
    empty.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    enums : tuple
        A list of enum strings to be populated as choices to the widget.
    """
    pydm_enumcombobox = PyDMEnumComboBox()
    qtbot.addWidget(pydm_enumcombobox)

    assert pydm_enumcombobox.count() == 0
    pydm_enumcombobox.set_items(enums)
    assert pydm_enumcombobox.count() == len(enums)

    assert all([enums[i] == pydm_enumcombobox.itemText(i) for i in range(0, len(enums))])
    assert pydm_enumcombobox._has_enums is True if len(enums) else pydm_enumcombobox._has_enums is False


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
def test_check_enable_state(qtbot, signals, connected, write_access, has_enum, is_app_read_only):
    """
    Test the tooltip generated depending on the channel connection, write access, whether the widget has enum strings,
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
    pydm_enumcombobox = PyDMEnumComboBox()
    qtbot.addWidget(pydm_enumcombobox)

    signals.write_access_signal[bool].connect(pydm_enumcombobox.writeAccessChanged)
    signals.write_access_signal[bool].emit(write_access)

    signals.connection_state_signal[bool].connect(pydm_enumcombobox.connectionStateChanged)
    signals.connection_state_signal[bool].emit(connected)

    if has_enum:
        signals.enum_strings_signal[tuple].connect(pydm_enumcombobox.enumStringsChanged)
        signals.enum_strings_signal[tuple].emit(("START", "STOP", "PAUSE"))
        assert pydm_enumcombobox._has_enums

    data_plugins.set_read_only(is_app_read_only)

    original_tooltip = "Original Tooltip"
    pydm_enumcombobox.setToolTip(original_tooltip)
    pydm_enumcombobox.check_enable_state()

    actual_tooltip = pydm_enumcombobox.toolTip()
    if not pydm_enumcombobox._connected:
        assert "PV is disconnected." in actual_tooltip
    elif not write_access:
        if data_plugins.is_read_only():
            assert "Running PyDM on Read-Only mode." in actual_tooltip
        else:
            assert "Access denied by Channel Access Security." in actual_tooltip
    elif not pydm_enumcombobox._has_enums:
        assert "Enums not available" in actual_tooltip


@pytest.mark.parametrize("values, selected_index, expected", [
    (("RUN", "STOP"), 0, "RUN"),
    (("RUN", "STOP"), 1, "STOP"),
    (("RUN", "STOP"), "RUN", "RUN"),
    (("RUN", "STOP"), "STOP", "STOP"),
])
def test_enum_strings_changed(qtbot, signals, values, selected_index, expected):
    """
    Test the widget's handling of enum strings, which are choices presented to the user, and the widget's ability to
    update the selected enum string when the user provides a choice index.

    This test will also cover value_changed() testing.

    Expectations:
    The widget displays the correct enum string whose index from the enum string tuple is selected by the user.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    values : tuple
        A set of enum strings for the user to choose from
    selected_index : int
        The index from the enum string tuple chosen by the user
    expected : str
        The expected enum string displayed by the widget after receiving the user's choice index
    """
    pydm_enumcombobox = PyDMEnumComboBox()
    qtbot.addWidget(pydm_enumcombobox)

    signals.enum_strings_signal.connect(pydm_enumcombobox.enumStringsChanged)
    signals.enum_strings_signal.emit(values)

    signals.new_value_signal[type(selected_index)].connect(pydm_enumcombobox.channelValueChanged)
    signals.new_value_signal[type(selected_index)].emit(selected_index)

    assert pydm_enumcombobox.value == selected_index
    assert pydm_enumcombobox.currentText() == expected


@pytest.mark.parametrize("index", [
    0,
    1,
    -1,
])
def test_internal_combo_box_activated_int(qtbot, signals, index):
    """
    Test the the capability of the widget's activated slot in sending out a new enum string index value.

    Expectations:
    The value sent out from the "activated" slot reflects the correct new index value.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    index : int
        The new enum string index value
    """
    pydm_enumcombobox = PyDMEnumComboBox()
    qtbot.addWidget(pydm_enumcombobox)

    # Connect the send_value_signal also to the conftest's receiveValue slot to intercept and verify that the correct
    # new index value is sent out
    pydm_enumcombobox.send_value_signal[int].connect(signals.receiveValue)
    pydm_enumcombobox.activated[int].emit(index)

    assert signals.value == index


# --------------------
# NEGATIVE TEST CASES
# --------------------

@pytest.mark.parametrize("enums, expected_error_message", [
    (None, "Invalid enum value '{0}'. The value is expected to be a valid list of string values.".format(None)),
    ((None, "abc"), "Invalid enum type '{0}'. The expected type is 'string'.".format(type(None))),
    ((None, 123.456), "Invalid enum type '{0}'. The expected type is 'string'".format(type(None))),
    ((None, None, None), "Invalid enum type '{0}'. The expected type is 'string'".format(type(None))),
    ((123,),  "Invalid enum type '{0}'. The expected type is 'string'".format(type(123))),
    ((123.45,),  "Invalid enum type '{0}'. The expected type is 'string'".format(type(123.45))),
    ((123, 456), "Invalid enum type '{0}'. The expected type is 'string'".format(type(123))),
    ((123.456, None), "Invalid enum type '{0}'. The expected type is 'string'".format(type(123.456))),
    (("spam", 123, "eggs", "ham"), "Invalid enum type '{0}'. The expected type is 'string'".format(type(123))),
])
def test_set_items_neg(qtbot, caplog, enums, expected_error_message):
    """
    Test sending setting the widget with an undefined list of enum strings.

    Expectations:
    The correct error message is logged.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    caplog : fixture
        To capture the log messages
    enums : tuple
        A list of strings as enum strings (choices) to populate to the widget.
    """
    pydm_enumcombobox = PyDMEnumComboBox()
    qtbot.addWidget(pydm_enumcombobox)

    pydm_enumcombobox.set_items(enums)

    for record in caplog.records:
        assert record.levelno == ERROR
    assert expected_error_message in caplog.text


@pytest.mark.parametrize("values, selected_index, expected", [
    (("ON", "OFF"), 3, ""),
    (("ON", "OFF"), -1, ""),
])
def test_enum_strings_changed_incorrect_index(qtbot, signals, values, selected_index, expected):
    """
    Test the widget's handling of incorrectly provided enum string index.

    Expectations:
    The widget will display an empty string.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    value : tuple
        A set of enum strings for the user to choose from
    selected_index : int
        The incorrect (out-of-bound) index from the enum string tuple chosen by the user
    expected : int
        The expected text displayed by the widget to notify the user of the incorrect choice index
    """
    pydm_enumcombobox = PyDMEnumComboBox()
    qtbot.addWidget(pydm_enumcombobox)

    signals.enum_strings_signal.connect(pydm_enumcombobox.enumStringsChanged)
    signals.enum_strings_signal.emit(values)

    signals.new_value_signal[type(selected_index)].connect(pydm_enumcombobox.channelValueChanged)
    signals.new_value_signal[type(selected_index)].emit(selected_index)

    assert pydm_enumcombobox.value == selected_index
    assert pydm_enumcombobox.currentText() == expected
