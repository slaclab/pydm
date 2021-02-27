import os
import pytest
import logging
import json
import copy
import webbrowser

from qtpy import QtCore
from qtpy.QtWidgets import QMessageBox, QTableWidgetSelectionRange

from ...widgets.symbol import PyDMSymbol
from ...widgets.symbol_editor import SymbolEditor


def test_symbol_editor(qtbot, monkeypatch):
    """
    Test the rules editor in general.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    monkeypatch : fixture
        To override dialog behaviors
    """
    # Create the base widget
    widget = PyDMSymbol()
    qtbot.addWidget(widget)

    # Ensure that no rules are set
    assert len(widget._state_images) == 0

    # Create a rule editor for this widget
    empty = SymbolEditor(widget)
    qtbot.addWidget(empty)

    empty.show()

    # Abort the changes
    empty.cancelChanges()

    # Create the rules data for the widget
    symbol_dict = {"1":"goodbye.jpg"}

    # Add the rules to the widget
    widget.imageFiles = json.dumps(symbol_dict)

    # Create a new Editor Window
    se = SymbolEditor(widget)
    qtbot.addWidget(se)
    se.show()

    assert se.tbl_symbols.rowCount() == 1
    assert not se.frm_edit.isEnabled()

    se.tbl_symbols.setCurrentCell(0, 0)
    assert se.frm_edit.isEnabled()
    assert se.txt_state.text() == "1"
    assert se.txt_file.text() == "goodbye.jpg"

    qtbot.mouseClick(se.btn_add_symbol, QtCore.Qt.LeftButton)
    assert se.txt_state.text() == "New State"
    assert se.txt_file.text() == "New File"
    assert se.lbl_image.text() == "Could not load image \nNew File"
    assert se.frm_edit.isEnabled()

    qtbot.keyClicks(se.txt_state, "-Test")
    qtbot.keyClick(se.txt_state, QtCore.Qt.Key_Return)
    assert se.txt_state.text() == "New State-Test"
    assert "New State-Test" in se.symbols
    assert se.symbols["New State-Test"] == "New File"

    qtbot.keyClick(se.txt_file, "!")
    assert se.txt_file.text() == "New File!"
    assert se.symbols["New State-Test"] == "New File!"

    # Test Delete Symbol with Confirm - NO
    assert se.tbl_symbols.rowCount() == 2
    se.tbl_symbols.setRangeSelected(QTableWidgetSelectionRange(1, 0, 1, 1), True)
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.No)
    qtbot.mouseClick(se.btn_del_symbol, QtCore.Qt.LeftButton)
    assert se.tbl_symbols.rowCount() == 2
    assert se.frm_edit.isEnabled()

    # Test Delete Symbol with Confirm - YES
    se.tbl_symbols.setRangeSelected(QTableWidgetSelectionRange(1, 0, 1, 1), True)
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Yes)
    qtbot.mouseClick(se.btn_del_symbol, QtCore.Qt.LeftButton)
    assert se.tbl_symbols.rowCount() == 1
    assert len(se.symbols) == 1
    assert se.frm_edit.isEnabled() is False

    # Test Delete Symbol with No Selection
    se.tbl_symbols.clearSelection()
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Yes)
    qtbot.mouseClick(se.btn_del_symbol, QtCore.Qt.LeftButton)
    assert se.tbl_symbols.rowCount() == 1
    assert len(se.symbols) == 1
    assert se.frm_edit.isEnabled() is False

def test_symbol_editor_data_valid(qtbot):
    """
    Test the rules form validation.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    """
    def validate(expected_status, expected_msg):
        status, msg = se.is_data_valid()
        assert status == expected_status
        assert expected_msg in msg

    # Create the base widget
    widget = PyDMSymbol()
    qtbot.addWidget(widget)

    # Create the rules data for the widget
    symbol_dict = {"1":"goodbye.jpg"}

    # Add the rules to the widget
    widget.imageFiles = json.dumps(symbol_dict)

    # Ensure that no rules are set
    assert widget.imageFiles is not None

    # Create a rule editor for this widget
    se = SymbolEditor(widget)
    qtbot.addWidget(se)

    # can use this when have images set up
    # validate(True, '')

    symbols_original = copy.deepcopy(se.symbols)

    se.symbols[""] = "goodbye.jpg"
    validate(False, "has no state")

    se.symbols = copy.deepcopy(symbols_original)
    se.symbols["1"] = "goodbye.jpg!!!"
    validate(False, "Could not load image")
