import os
import json
import functools
import webbrowser

from qtpy import QtWidgets, QtCore, QtDesigner
from ..utilities.iconfont import IconFont


class SymbolEditor(QtWidgets.QDialog):

    def __init__(self, widget, parent=None):
        super(SymbolEditor, self).__init__(parent)
        self.widget = widget


        self.setup_ui()

    def setup_ui(self):



    @QtCore.Slot()
    def saveChanges(self):
        """Save the new rules at the widget `rules` property."""
        # If the form is being edited, we make sure self.rules has all the
        # latest values from the form before we try to validate.  This fixes
        # a problem where the last form item change wouldn't get saved unless
        # the user knew to hit 'enter' or leave the field to end editing before
        # hitting save.
        if self.frm_edit.isEnabled():
            self.expression_changed()
            self.name_changed()
            self.tbl_channels_changed()
        status, message = self.is_data_valid()
        if status:
            data = json.dumps(self.rules)
            formWindow = QtDesigner.QDesignerFormWindowInterface.findFormWindow(self.widget)
            if formWindow:
                formWindow.cursor().setProperty("rules", data)
            self.accept()
        else:
            QtWidgets.QMessageBox.critical(self, "Error Saving", message,
                                           QtWidgets.QMessageBox.Ok)


    @QtCore.Slot()
    def cancelChanges(self):
        """Abort the changes and close the dialog."""
        self.close()
