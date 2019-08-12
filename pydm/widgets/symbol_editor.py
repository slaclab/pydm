import os
import json
import functools
import webbrowser

from qtpy import QtWidgets, QtCore, QtDesigner
from ..utilities.iconfont import IconFont


import logging
from qtpy.QtWidgets import QApplication, QWidget, QStyle, QStyleOption
from qtpy.QtGui import QPainter, QPixmap
from qtpy.QtCore import Property, Qt, QSize, QSizeF, QRectF, qInstallMessageHandler
from qtpy.QtSvg import QSvgRenderer
from ..utilities import is_pydm_app
from .base import PyDMWidget

class SymbolEditor(QtWidgets.QDialog):

    def __init__(self, widget, parent=None):
        super(SymbolEditor, self).__init__(parent)
        
        self.widget = widget
        self.lst_symbol_item = None
        self.loading_data = True

        self.setup_ui()

        try:
            self.symbols = json.loads(widget.imageFiles)
        except:
            self.symbols = {}

        for state, filename in self.symbols:
            row = self.tbl_symbols.rowCount()
            self.tbl_symbols.insertRow(row)
            self.tbl_symbols.setItem(row, 0, QtWidgets.QTableWidgetItem(state))
            self.tbl_symbols.setItem(row, 1, QtWidgets.QTableWidgetItem(filename))

        self._painter = QPainter()
            
    def setup_ui(self):
        """
        Create the required UI elements for the form.

        Returns
        -------
        None
        """
        iconfont = IconFont()

        self.setWindowTitle("PyDM Symbol Widget Editor")
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.setContentsMargins(5, 5, 5, 5)
        vlayout.setSpacing(5)
        self.setLayout(vlayout)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.setSpacing(5)
        vlayout.addLayout(hlayout)

        # Creating the widgets for the String List and
        # buttons to add and remove actions
        list_frame = QtWidgets.QFrame(parent=self)
        list_frame.setMinimumHeight(300)
        list_frame.setMinimumWidth(240)
        list_frame.setLineWidth(1)
        list_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        list_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        lf_layout = QtWidgets.QVBoxLayout()
        list_frame.setLayout(lf_layout)

        lf_btn_layout = QtWidgets.QHBoxLayout()
        lf_btn_layout.setContentsMargins(0, 0, 0, 0)
        lf_btn_layout.setSpacing(5)

        btn_add_symbol = QtWidgets.QPushButton(parent=self)
        btn_add_symbol.setAutoDefault(False)
        btn_add_symbol.setDefault(False)
        btn_add_symbol.setText("Add Symbol")
        btn_add_symbol.clicked.connect(self.add_symbol)

        btn_del_symbol = QtWidgets.QPushButton(parent=self)
        btn_del_symbol.setAutoDefault(False)
        btn_del_symbol.setDefault(False)
        btn_del_symbol.setText("Remove symbol")
        btn_del_symbol.clicked.connect(self.del_symbol)

        lf_btn_layout.addWidget(btn_add_symbol)
        lf_btn_layout.addWidget(btn_del_symbol)

        lf_layout.addLayout(lf_btn_layout)

        self.tbl_symbols = QtWidgets.QTableWidget()
        self.tbl_symbols.setMinimumWidth(350)
        self.tbl_symbols.setShowGrid(True)
        self.tbl_symbols.setCornerButtonEnabled(False)
        headers = ["State", "File"]
        self.tbl_symbols.setColumnCount(len(headers))
        self.tbl_symbols.setHorizontalHeaderLabels(headers)
        header = self.tbl_symbols.horizontalHeader()
        header.setResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.tbl_symbols.itemSelectionChanged.connect(self.load_from_list)
        self.tbl_symbols.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tbl_symbols.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tbl_symbols.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        lf_layout.addWidget(self.tbl_symbols)

        hlayout.addWidget(list_frame)

        buttons_layout = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton("Save", parent=self)
        save_btn.setAutoDefault(False)
        save_btn.setDefault(False)
        save_btn.clicked.connect(self.saveChanges)
        cancel_btn = QtWidgets.QPushButton("Cancel", parent=self)
        cancel_btn.setAutoDefault(False)
        cancel_btn.setDefault(False)
        cancel_btn.clicked.connect(self.cancelChanges)
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)

        vlayout.addLayout(buttons_layout)

        # Creating the widgets that we will use to compose the
        # symbol parameters
        self.frm_edit = QtWidgets.QFrame()
        self.frm_edit.setEnabled(False)
        self.frm_edit.setLineWidth(1)
        self.frm_edit.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frm_edit.setFrameShape(QtWidgets.QFrame.StyledPanel)

        frm_edit_layout = QtWidgets.QVBoxLayout()
        self.frm_edit.setLayout(frm_edit_layout)

        hlayout.addWidget(self.frm_edit)

        edit_name_layout = QtWidgets.QFormLayout()
        edit_name_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        lbl_state = QtWidgets.QLabel("State:")
        self.txt_state = QtWidgets.QLineEdit()
        self.txt_state.editingFinished.connect(self.state_changed)
        edit_name_layout.addRow(lbl_state, self.txt_state)
        lbl_file = QtWidgets.QLabel("File:")
        self.txt_file = QtWidgets.QLineEdit()
        self.txt_file.editingFinished.connect(self.file_changed)
        edit_name_layout.addRow(lbl_file, self.txt_file)

        frm_edit_layout.addLayout(edit_name_layout)

        preview_btn = QtWidgets.QPushButton("Preview Image", parent=self)
        preview_btn.setAutoDefault(False)
        preview_btn.setDefault(False)
        preview_btn.clicked.connect(self.preview_image)
        frm_edit_layout.addWidget(preview_btn)

        self.lbl_image = QtWidgets.QLabel()
        frm_edit_layout.addWidget(frm_edit_layout)

    def clear_form(self):
        """Clear the form and reset the fields."""
        self.lst_state_item = None
        self.lst_file_item = None
        self.txt_state.setText("")
        self.txt_file.setText("")
        self.frm_edit.setEnabled(False)

    def load_from_list(self):
        """
        Load an entry from the list into the editing form.

        Returns
        -------
        None
        """
        item = self.tbl_symbols.currentItem()
        idx = self.tbl_symbols.indexFromItem(item).row()

        if idx < 0:
            return

        row = self.tbl_symbols.currentRow()
        self.tbl_symbols.selectRow(row)
        self.lst_state_item = self.tbl_symbols.item(row, 0)
        self.lst_file_item = self.tbl_symbols.item(row, 1)
        self.txt_state.setText(self.lst_state_item.text())
        self.txt_file.setText(self.lst_file_item.text())

        self.frm_edit.setEnabled(True)

    def add_symbol(self):
        """Add a new rule to the list of rules."""
        default_state = "New State"
        default_file = "New File"

        row = self.tbl_symbols.rowCount()
        self.tbl_symbols.insertRow(row)
        self.lst_state_item = QtWidgets.QTableWidgetItem(default_state)
        self.tbl_symbols.setItem(row, 0, self.lst_state_item)
        self.lst_file_item = QtWidgets.QTableWidgetItem(default_file)
        self.tbl_symbols.setItem(row, 1, self.lst_file_item)

        self.symbols[default_state] = default_file
        self.tbl_symbols.setCurrentItem(self.lst_file_item)
        self.load_from_list()
        self.txt_state.setFocus()

    def del_symbol(self):
        """Delete the selected symbol at the table."""
        items = self.tbl_symbols.selectedIndexes()
        if len(items) == 0:
            return

        s = "symbol(s)"
        confirm_message = "Delete the selected {}?".format(s)
        reply = QtWidgets.QMessageBox().question(self, 'Message',
                                                 confirm_message,
                                                 QtWidgets.QMessageBox.Yes,
                                                 QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            for itm in reversed(items):
                row = itm.row()
                state = self.tbl_symbols.item(row, 0).text()
                self.symbols.pop(state, None) # troubleshoot by taking out None?
                self.tbl_symbols.removeRow(row)
                self.tbl_symbols.clearSelection()
                self.clear_form()

    def state_changed(self):
        """Callback executed when the state line edit is changed."""
        if not self.lst_state_item:
            return
        prev_state = self.lst_state_item.text()
        self.symbols.pop(prev_state)

        new_state = self.txt_state.text()
        filename = self.txt_file.text()
        self.lst_state_item.setText(new_state)
        self.symbols[new_state] = filename

    def file_changed(self):
        """Callback executed when the file line edit is changed."""
        if not self.lst_file_item:
            return
        state = self.txt_state.text()
        new_filename = self.txt_file.text()
        self.lst_file_item.setText(new_filename)
        self.symbols[state] = new_filename

    def preview_image(self):
        #TODO: POPULATE THIS
        pass

    def is_data_valid(self):
        #TODO: FIGURE OUT MESSAGE HANDLER
        """
        Sanity check the form data.

        Returns
        -------
        tuple : (bool, str)
            True and "" in case there is no error or False and the error message
            otherwise.
        """
        '''errors = []
        for state, filename in self.symbols:
            if is_pydm_app():
                try:
                    file_path = self.app.get_path(filename)
                except Exception as e:
                    errors.append("Couldn't get file with path %s", filename)
                    file_path = filename
            else:
                file_path = filename
            # First, lets try SVG.  We have to try SVG first, otherwise
            # QPixmap will happily load the SVG and turn it into a raster image.
            # Really annoying: We have to try to load the file as SVG,
            # and we expect it will fail often (because many images aren't SVG).
            # Qt prints a warning message to stdout any time SVG loading fails.
            # So we have to temporarily silence Qt warning messages here.
            qInstallMessageHandler(self.qt_message_handler)
            svg = QSvgRenderer()
            svg.repaintNeeded.connect(self.update)
            if svg.load(file_path):
                self._state_images[int(state)] = (filename, svg)
                self._sizeHint = self._sizeHint.expandedTo(svg.defaultSize())
                qInstallMessageHandler(None)
                continue
            qInstallMessageHandler(None)
            # SVG didn't work, lets try QPixmap
            image = QPixmap(file_path)
            if not image.isNull():
                self._state_images[int(state)] = (filename, image)
                self._sizeHint = self._sizeHint.expandedTo(image.size())
                continue
            # If we get this far, the file specified could not be loaded at all.
            errors.append("Could not load image: {}".format(filename))
            self._state_images[int(state)] = (filename, None)

        if len(errors) > 0:
            error_msg = os.linesep.join(errors)
            return False, error_msg'''

        return True, ""

    @QtCore.Slot()
    def saveChanges(self):
        """Save the new symbols at the widget `symbols` property."""
        # If the form is being edited, we make sure self.symbols has all the
        # latest values from the form before we try to validate.  This fixes
        # a problem where the last form item change wouldn't get saved unless
        # the user knew to hit 'enter' or leave the field to end editing before
        # hitting save.
        if self.frm_edit.isEnabled():
            self.state_changed()
        status, message = self.is_data_valid()
        if status:
            data = json.dumps(self.symbols)
            formWindow = QtDesigner.QDesignerFormWindowInterface.findFormWindow(self.widget)
            if formWindow:
                formWindow.cursor().setProperty("imageFiles", data)
            self.accept()
        else:
            QtWidgets.QMessageBox.critical(self, "Error Saving", message,
                                           QtWidgets.QMessageBox.Ok)

    @QtCore.Slot()
    def cancelChanges(self):
        """Abort the changes and close the dialog."""
        self.close()
