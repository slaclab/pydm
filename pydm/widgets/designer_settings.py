import os
import json
import functools
import webbrowser

from qtpy import QtWidgets, QtCore, QtDesigner
from ..utilities.iconfont import IconFont


def update_property_for_widget(widget: QtWidgets.QWidget, name: str, value):
    """Update a Property for the given widget in the designer."""
    formWindow = QtDesigner.QDesignerFormWindowInterface.findFormWindow(widget)
    if formWindow:
        formWindow.cursor().setProperty(name, value)
    else:
        setattr(widget, name, value)


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

        if not hasattr(self.widget, "channel"):
            self.channel_widget = None
        else:
            channel_form = QtWidgets.QFormLayout()
            self.channel_widget = QtWidgets.QLineEdit(
                self.widget.channel or ""
            )
            channel_form.addRow("&Channel", self.channel_widget)
            vlayout.addLayout(channel_form)

        if not hasattr(self.widget, "macros"):
            self.macros_widget = None
        else:
            # Ideally macros wouldn't be shown as a line edit; consider a table
            # or something easy to edit and interpret
            macros_form = QtWidgets.QFormLayout()
            self.macros_widget = QtWidgets.QLineEdit(
                self.widget.macros or ""
            )
            macros_form.addRow("&Macros", self.macros_widget)
            vlayout.addLayout(macros_form)

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
            update_property_for_widget(self.widget, "channel", self.channel_widget.text() or "")
        if self.macros_widget is not None:
            update_property_for_widget(self.widget, "macros", self.macros_widget.text() or "")
        self.accept()

    @QtCore.Slot()
    def cancel_changes(self):
        """Abort the changes and close the dialog."""
        self.close()
