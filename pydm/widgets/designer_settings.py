import os
import json
import logging
import functools
import webbrowser

from qtpy import QtWidgets, QtCore, QtDesigner
from ..utilities.iconfont import IconFont
from ..utilities.macro import parse_macro_string
from ..utilities import copy_to_clipboard, get_clipboard_text


logger = logging.getLogger(__name__)


def update_property_for_widget(widget: QtWidgets.QWidget, name: str, value):
    """Update a Property for the given widget in the designer."""
    formWindow = QtDesigner.QDesignerFormWindowInterface.findFormWindow(widget)
    logger.info("Updating %s.%s = %s", widget.objectName(), name, value)
    if formWindow:
        formWindow.cursor().setProperty(name, value)
    else:
        setattr(widget, name, value)


class DictionaryTable(QtWidgets.QTableWidget):
    def __init__(self, dct=None, parent=None):
        super().__init__(parent=parent)

        self.setColumnCount(2)
        self.setMinimumSize(300, 200)
        self.setHorizontalHeaderLabels(["Key", "Value"])

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.dictionary = dct

    def _context_menu(self, pos):
        self.menu = QtWidgets.QMenu(self)
        item = self.itemAt(pos)
        if item is not None:
            def copy(*_):
                copy_to_clipboard(item.text())

            copy_action = self.menu.addAction(f"&Copy: {item.text()}")
            copy_action.triggered.connect(copy)

            clipboard_text = get_clipboard_text()

            def paste(*_):
                item.setText(clipboard_text)

            paste_action = self.menu.addAction(f"&Paste: {clipboard_text}")
            paste_action.triggered.connect(paste)

            def delete_row(*_):
                self.removeRow(item.row())

            delete_row_action = self.menu.addAction("&Delete row...")
            delete_row_action.triggered.connect(delete_row)

        self.menu.addSeparator()

        def add_row(*_):
            row = self.rowCount()
            self.setRowCount(row + 1)
            self.setItem(row, 0, QtWidgets.QTableWidgetItem(""))
            self.setItem(row, 1, QtWidgets.QTableWidgetItem(""))

        add_row_action = self.menu.addAction("&Add row...")
        add_row_action.triggered.connect(add_row)
        self.menu.exec_(self.mapToGlobal(pos))

    @property
    def dictionary(self) -> dict:
        items = [
            (self.item(row, 0), self.item(row, 1))
            for row in range(self.rowCount())
        ]
        key_value_pairs = [
            (key.text() if key else "", value.text() if value else "")
            for key, value in items
        ]
        return {
            key.strip(): value
            for key, value in key_value_pairs
        }


    @dictionary.setter
    def dictionary(self, dct):
        self.setRowCount(len(dct))
        for row, (key, value) in enumerate(dct.items()):
            self.setItem(row, 0, QtWidgets.QTableWidgetItem(key))
            self.setItem(row, 1, QtWidgets.QTableWidgetItem(value))

        self.resizeColumnsToContents()
        self.resizeRowsToContents()


class BasicSettingsEditor(QtWidgets.QDialog):
    """
    QDialog for user-friendly editing of essential PyDM properties in Designer.

    Parameters
    ----------
    widget : PyDMWidget
        The widget which we want to edit.
    """

    def __init__(self, widget, parent=None):
        super(BasicSettingsEditor, self).__init__(parent)

        self.widget = widget

        # PV names can be pretty wide...
        self.setMinimumSize(400, 200)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding,
        )

        self.setup_ui()

    def setup_ui(self):
        """
        Create the required UI elements for the form.

        Returns
        -------
        None
        """
        iconfont = IconFont()

        self.setWindowTitle("PyDM Widget Basic Settings Editor")
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.setContentsMargins(5, 5, 5, 5)
        vlayout.setSpacing(5)
        self.setLayout(vlayout)

        settings_form = QtWidgets.QFormLayout()
        vlayout.addLayout(settings_form)

        if not hasattr(self.widget, "channel"):
            self.channel_widget = None
        else:
            self.channel_widget = QtWidgets.QLineEdit(
                self.widget.channel or ""
            )
            settings_form.addRow("&Channel", self.channel_widget)

        if not hasattr(self.widget, "filename"):
            self.filename_widget = None
        else:
            self.filename_widget = QtWidgets.QLineEdit(
                self.widget.filename or ""
            )
            settings_form.addRow("&Filename", self.filename_widget)

        if not hasattr(self.widget, "macros"):
            self.macros_widget = None
        else:
            # Ideally macros wouldn't be shown as a line edit; consider a table
            # or something easy to edit and interpret
            self.macros_widget = DictionaryTable(
                parse_macro_string(self.widget.macros or "")
            )
            settings_form.addRow("&Macros", self.macros_widget)

        def open_rules_editor():
            from .rules_editor import RulesEditor
            self._rules_editor = RulesEditor(self.widget, parent=self)
            self._rules_editor.exec_()

        rules_button = QtWidgets.QPushButton("&Rule editor...")
        rules_button.setAutoDefault(False)
        rules_button.setDefault(False)
        rules_button.clicked.connect(open_rules_editor)
        vlayout.addWidget(rules_button)

        buttons_layout = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton("&Save", parent=self)
        save_btn.setAutoDefault(True)
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.save_changes)
        cancel_btn = QtWidgets.QPushButton("&Cancel", parent=self)
        cancel_btn.clicked.connect(self.cancel_changes)
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)

        vlayout.addLayout(buttons_layout)

    @QtCore.Slot()
    def save_changes(self):
        """Save the new settings on the widget properties."""
        if self.channel_widget is not None:
            channel = (self.channel_widget.text() or "").strip()
            update_property_for_widget(self.widget, "channel", channel)
        if self.macros_widget is not None:
            macros = json.dumps(self.macros_widget.dictionary)
            update_property_for_widget(self.widget, "macros", macros)
        if self.filename_widget is not None:
            filename = self.filename_widget.text().strip()
            update_property_for_widget(self.widget, "filename", filename)
        self.accept()

    @QtCore.Slot()
    def cancel_changes(self):
        """Abort the changes and close the dialog."""
        self.close()
