import json
import logging
import re
from typing import Any, List, Optional

from qtpy import QtCore, QtDesigner, QtWidgets

from pydm.utilities import copy_to_clipboard, get_clipboard_text
from pydm.utilities.macro import parse_macro_string

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
    def __init__(self, dictionary=None, *args, parent=None, **kwargs):
        super().__init__(*args, parent=parent, **kwargs)

        self.setColumnCount(2)
        self.setMinimumSize(300, 150)
        self.setHorizontalHeaderLabels(["Key", "Value"])

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.dictionary = dictionary

    def _context_menu(self, pos):
        self.menu = QtWidgets.QMenu(self)
        item = self.itemAt(pos)
        if item is not None:

            def copy(*_):
                copy_to_clipboard(item.text())

            copy_action = self.menu.addAction(f"&Copy: {item.text()}")
            copy_action.triggered.connect(copy)

            clipboard_text = get_clipboard_text() or ""

            def paste(*_):
                item.setText(clipboard_text)

            paste_action = self.menu.addAction(f"&Paste: {clipboard_text[:100]}")
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
        items = [(self.item(row, 0), self.item(row, 1)) for row in range(self.rowCount())]
        key_value_pairs = [(key.text() if key else "", value.text() if value else "") for key, value in items]
        return {key.strip(): value for key, value in key_value_pairs}

    @dictionary.setter
    def dictionary(self, dct):
        dct = dct or {}
        self.setRowCount(len(dct))
        for row, (key, value) in enumerate(dct.items()):
            self.setItem(row, 0, QtWidgets.QTableWidgetItem(key))
            self.setItem(row, 1, QtWidgets.QTableWidgetItem(value))

        self.resizeColumnsToContents()
        self.resizeRowsToContents()


class StringListTable(QtWidgets.QTableWidget):
    def __init__(self, values=None, *args, parent=None, **kwargs):
        super().__init__(*args, parent=parent, **kwargs)

        self.setColumnCount(1)
        self.setMinimumSize(300, 150)
        self.setHorizontalHeaderLabels(["Value"])

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.values

        # we let user swap points by dragging one on-top of the other
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.drag_source_row = None

    def startDrag(self, event):
        self.drag_source_row = self.currentRow()
        # call super() since we use the default dragging functionality
        super().startDrag(event)

    def dropEvent(self, event):
        # don't call super() here, functionality messes with our swapping!
        source_row = self.drag_source_row
        target_row = self.indexAt(event.pos()).row()
        if target_row >= 0 and source_row != target_row:
            self.swap_rows(source_row, target_row)

    def swap_rows(self, row1, row2):
        item1 = self.takeItem(row1, 0)
        item2 = self.takeItem(row2, 0)
        self.setItem(row1, 0, item2)
        self.setItem(row2, 0, item1)

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

        add_row_action = self.menu.addAction("&Add row...")
        add_row_action.triggered.connect(add_row)
        self.menu.exec_(self.mapToGlobal(pos))

    @property
    def values(self) -> list:
        items = [self.item(row, 0) for row in range(self.rowCount())]
        return [item.text().strip() for item in items if item is not None]

    @values.setter
    def values(self, values):
        values = values or []
        self.setRowCount(len(values))
        for row, value in enumerate(values):
            self.setItem(row, 0, QtWidgets.QTableWidgetItem(str(value)))

        self.resizeColumnsToContents()
        self.resizeRowsToContents()


class _PropertyHelper:
    def __init__(self, *args, property_widget, property_name, **kwargs):
        super().__init__(*args, **kwargs)
        self._property_name = property_name
        self._property_widget = property_widget

        value = None
        try:
            value = self.value_from_widget
            self.set_value_from_widget(
                widget=self._property_widget,
                attr=self._property_name,
                value=value,
            )
        except Exception:
            logger.exception(
                "Failed to set helper widget %s state from %s=%s",
                type(self).__name__,
                self._property_name,
                value,
            )

    def set_value_from_widget(self, widget, attr, value):
        """For subclasses."""
        ...

    @property
    def value_from_widget(self):
        return getattr(self._property_widget, self._property_name, None)

    @property
    def saved_value(self) -> Optional[Any]:
        raise None

    def save_settings(self):
        value = self.saved_value
        if value is not None:
            update_property_for_widget(self._property_widget, self._property_name, value)


class PropertyRuleEditor(_PropertyHelper, QtWidgets.QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAutoDefault(False)
        self.setDefault(False)
        self.clicked.connect(self._open_rules_editor)
        self.setText("&Rules...")

    def _open_rules_editor(self):
        from .rules_editor import RulesEditor

        self._rules_editor = RulesEditor(self._property_widget, parent=self)
        self._rules_editor.exec_()

    @property
    def saved_value(self) -> Optional[str]:
        return None


class PropertyCheckbox(_PropertyHelper, QtWidgets.QCheckBox):
    def set_value_from_widget(self, widget, attr, value):
        self.setChecked(bool(value))

    @property
    def saved_value(self) -> bool:
        return self.isChecked()


class PropertyLineEdit(_PropertyHelper, QtWidgets.QLineEdit):
    def set_value_from_widget(self, widget, attr, value):
        self.setText(value or "")

    @property
    def saved_value(self) -> Optional[str]:
        return self.text().strip()


class PropertyIntSpinBox(_PropertyHelper, QtWidgets.QSpinBox):
    def set_value_from_widget(self, widget, attr, value):
        self.setValue(value)

    @property
    def saved_value(self) -> int:
        return self.value()


class PropertyMacroTable(_PropertyHelper, DictionaryTable):
    def set_value_from_widget(self, widget, attr, value):
        try:
            macros = parse_macro_string(value or "")
        except Exception:
            logger.exception("Failed to parse macro string: %r", value)
        else:
            self.dictionary = macros

    @property
    def saved_value(self) -> Optional[str]:
        return json.dumps(self.dictionary)


class PropertyStringList(_PropertyHelper, StringListTable):
    def set_value_from_widget(self, widget, attr, value):
        self.values = value

    @property
    def saved_value(self) -> Optional[List[str]]:
        return self.values


def get_qt_properties(cls):
    """Yields all QMetaProperty instances from a given class."""
    meta_obj = cls.staticMetaObject
    for prop_idx in range(meta_obj.propertyCount()):
        prop = meta_obj.property(prop_idx)
        if prop is not None and prop.isDesignable():
            yield prop.name()


def get_helper_label_text(attr: str) -> str:
    spaced = re.sub("(PyDM|.)([A-Z])", r"\1 \2", attr)
    return spaced.strip().capitalize()


class BasicSettingsEditor(QtWidgets.QDialog):
    """
    QDialog for user-friendly editing of essential PyDM properties in Designer.

    Parameters
    ----------
    widget : PyDMWidget
        The widget which we want to edit.
    """

    _common_attributes_ = {
        "channel": PropertyLineEdit,
        "display": PropertyLineEdit,
        "macros": PropertyMacroTable,
        "filenames": PropertyStringList,
        "rules": PropertyRuleEditor,
    }

    _type_to_widget_ = {
        str: PropertyLineEdit,
        int: PropertyIntSpinBox,
        bool: PropertyCheckbox,
        "QStringList": PropertyStringList,
    }

    def __init__(self, widget, parent=None):
        super().__init__(parent)

        self.widget = widget

        # PV names can be pretty wide...
        self.setMinimumSize(400, 150)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding,
        )

        self.property_widgets = []
        self.setup_ui()

    def setup_ui(self):
        """
        Create the required UI elements for the form.

        Returns
        -------
        None
        """
        self.setWindowTitle("PyDM Widget Basic Settings Editor")
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.setContentsMargins(5, 5, 5, 5)
        vlayout.setSpacing(5)
        self.setLayout(vlayout)

        settings_form = QtWidgets.QFormLayout()
        settings_form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        vlayout.addLayout(settings_form)

        for helper_widget in self._create_helper_widgets(settings_form):
            self.property_widgets.append(helper_widget)

        buttons_layout = QtWidgets.QHBoxLayout()
        self.save_btn = QtWidgets.QPushButton("&Save", parent=self)
        self.save_btn.setAutoDefault(True)
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.save_changes)
        self.update_btn = QtWidgets.QPushButton("&Update", parent=self)
        self.update_btn.clicked.connect(self.save_changes)
        cancel_btn = QtWidgets.QPushButton("&Cancel", parent=self)
        cancel_btn.clicked.connect(self.cancel_changes)
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(self.update_btn)
        buttons_layout.addWidget(self.save_btn)

        vlayout.addLayout(buttons_layout)

    def _create_helper_widgets(self, settings_form: QtWidgets.QFormLayout):
        other_attrs = []
        for attr in sorted(get_qt_properties(type(self.widget))):
            if attr not in self._common_attributes_ and attr not in other_attrs:
                other_attrs.append(attr)

        for attr in list(self._common_attributes_) + other_attrs:
            prop = getattr(type(self.widget), attr, None)
            if prop is None:
                continue

            prop_type = getattr(prop, "type", None)
            helper_widget_cls = self._common_attributes_.get(attr, self._type_to_widget_.get(prop_type, None))
            if helper_widget_cls is not None:
                helper_widget = helper_widget_cls(
                    property_widget=self.widget,
                    property_name=attr,
                )
                label_text = get_helper_label_text(attr)
                settings_form.addRow(f"&{label_text}", helper_widget)
                yield helper_widget

    @QtCore.Slot()
    def save_changes(self):
        """Save the new settings on the widget properties."""
        for helper in self.property_widgets:
            try:
                helper.save_settings()
            except Exception:
                logger.exception(
                    "Failed to save settings for %s.%s = %r",
                    self.widget.objectName(),
                    helper._property_name,
                    helper.saved_value,
                )

        if self.sender() == self.save_btn:
            self.accept()

    @QtCore.Slot()
    def cancel_changes(self):
        """Abort the changes and close the dialog."""
        self.close()
