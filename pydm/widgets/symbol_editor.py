import os
import json

from qtpy import QtWidgets, QtCore, QtDesigner
from qtpy.QtWidgets import QApplication, QWidget, QStyle, QStyleOption
from qtpy.QtGui import QPainter, QPixmap
from qtpy.QtCore import Property, Qt, QSize, QSizeF, QRectF, qInstallMessageHandler
from qtpy.QtSvg import QSvgRenderer
from ..utilities import is_pydm_app, is_qt_designer, find_file
from .base import PyDMWidget


class SymbolEditor(QtWidgets.QDialog):
    """
    QDialog for user-friendly editing of the symbols in a widget inside the Qt
    Designer.

    Parameters
    ----------
    widget : PyDMWidget
        The widget which we want to edit the 'imageFiles' property.
    """

    def __init__(self, widget, parent=None):
        super(SymbolEditor, self).__init__(parent)
        
        self.widget = widget
        self.lst_file_item = None
        self.lst_state_item = None
        self.preview = False
        self.preview_file = None
        self.setup_ui()

        try:
            self.symbols = json.loads(widget.imageFiles)
        except:
            self.symbols = {}

        for state, filename in self.symbols.items():
            row = self.tbl_symbols.rowCount()
            self.tbl_symbols.insertRow(row)
            self.tbl_symbols.setItem(row, 0, QtWidgets.QTableWidgetItem(state))
            self.tbl_symbols.setItem(row, 1, QtWidgets.QTableWidgetItem(filename))

    def setup_ui(self):
        """
        Create the required UI elements for the form.

        Returns
        -------
        None
        """

        self.setWindowTitle("PyDM Symbol Widget Editor")
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.setContentsMargins(5, 5, 5, 5)
        vlayout.setSpacing(5)
        self.setLayout(vlayout)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.setSpacing(5)
        vlayout.addLayout(hlayout)

        # Creating the widgets for the buttons to add and
        # remove symbols
        list_frame = QtWidgets.QFrame(parent=self)
        list_frame.setMinimumHeight(300)
        list_frame.setMinimumWidth(300)
        list_frame.setLineWidth(1)
        list_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        list_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        lf_layout = QtWidgets.QVBoxLayout()
        list_frame.setLayout(lf_layout)

        lf_btn_layout = QtWidgets.QHBoxLayout()
        lf_btn_layout.setContentsMargins(0, 0, 0, 0)
        lf_btn_layout.setSpacing(5)

        self.btn_add_symbol = QtWidgets.QPushButton(parent=self)
        self.btn_add_symbol.setAutoDefault(False)
        self.btn_add_symbol.setDefault(False)
        self.btn_add_symbol.setText("Add Symbol")
        self.btn_add_symbol.clicked.connect(self.add_symbol)

        self.btn_del_symbol = QtWidgets.QPushButton(parent=self)
        self.btn_del_symbol.setAutoDefault(False)
        self.btn_del_symbol.setDefault(False)
        self.btn_del_symbol.setText("Remove Symbol")
        self.btn_del_symbol.clicked.connect(self.del_symbol)

        lf_btn_layout.addWidget(self.btn_add_symbol)
        lf_btn_layout.addWidget(self.btn_del_symbol)

        lf_layout.addLayout(lf_btn_layout)

        # Table containing the state/filename pairs which
        # will display the different symbols
        self.tbl_symbols = QtWidgets.QTableWidget()
        self.tbl_symbols.setShowGrid(True)
        self.tbl_symbols.setCornerButtonEnabled(False)
        headers = ["State", "File"]
        self.tbl_symbols.setColumnCount(len(headers))
        self.tbl_symbols.setHorizontalHeaderLabels(headers)
        header = self.tbl_symbols.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.tbl_symbols.itemSelectionChanged.connect(self.load_from_list)
        self.tbl_symbols.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tbl_symbols.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tbl_symbols.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tbl_symbols.verticalHeader().setVisible(False)
        lf_layout.addWidget(self.tbl_symbols)

        hlayout.addWidget(list_frame)

        # Buttons to save or cancel changes made
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
        self.txt_file.textEdited.connect(self.file_changed)
        self.txt_file.returnPressed.connect(self.file_changed)
        edit_name_layout.addRow(lbl_file, self.txt_file)

        self.lbl_image = QtWidgets.QLabel()
        self.lbl_image.setWordWrap(True)
        self.lbl_image.setAlignment(Qt.AlignCenter)
        edit_name_layout.addRow(self.lbl_image)

        frm_edit_layout.addLayout(edit_name_layout)

    def clear_form(self):
        """Clear the form and reset the fields."""
        self.lst_state_item = None
        self.lst_file_item = None
        self.txt_state.setText("")
        self.txt_file.setText("")
        self.lbl_image.setText("")
        self.frm_edit.setEnabled(False)
        self.tbl_symbols.clearSelection()
        self.preview = False

    def load_from_list(self):
        """
        Load an entry from the list into the editing form.

        Returns
        -------
        None
        """
        if not self.tbl_symbols.selectedRanges():
            return

        row = self.tbl_symbols.currentRow()
        self.lst_state_item = self.tbl_symbols.item(row, 0)
        self.lst_file_item = self.tbl_symbols.item(row, 1)
        self.txt_state.setText(self.lst_state_item.text())
        self.txt_file.setText(self.lst_file_item.text())
        self.frm_edit.setEnabled(True)

        filename = self.lst_file_item.text()
        error, self.preview_file = self.check_image(filename)
        if not error:
            self.lbl_image.setText("")
            self.preview = True
        else:
            self.lbl_image.setText(error)
        self.update()

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
        if not self.tbl_symbols.selectedRanges():
            return

        confirm_message = "Delete the selected symbol?"
        reply = QtWidgets.QMessageBox().question(self, 'Message',
                                                 confirm_message,
                                                 QtWidgets.QMessageBox.Yes,
                                                 QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            row = self.tbl_symbols.currentRow()
            state_item = self.tbl_symbols.item(row, 0)
            state = state_item.text()
            self.symbols.pop(state, None)
            self.tbl_symbols.removeRow(row)
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

        error, self.preview_file = self.check_image(new_filename)
        if not error:
            self.lbl_image.setText("")
            self.preview = True
        else:
            self.lbl_image.setText(error)
        self.update()

    def paintEvent(self, event):
        """
        Paint events are sent to widgets that need to update themselves,
        for instance when part of a widget is exposed because a covering
        widget was moved.

        At PyDMSymbolEditor this method handles the image preview.

        Parameters
        ----------
        event : QPaintEvent
        """
        if not self.preview:
            return
        size = QSize(140, 140)
        _painter = QPainter()
        _painter.begin(self)
        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, _painter, self)
        image_to_draw = self.preview_file
        if isinstance(image_to_draw, QPixmap):
            w = float(image_to_draw.width())
            h = float(image_to_draw.height())
            sf = min(size.width() / w, size.height() / h)
            scale = (sf, sf)
            _painter.scale(scale[0], scale[1])
            _painter.drawPixmap(335/sf, 120/sf, image_to_draw)
        elif isinstance(image_to_draw, QSvgRenderer):
            draw_size = QSizeF(image_to_draw.defaultSize())
            draw_size.scale(QSizeF(size), Qt.KeepAspectRatio)
            image_to_draw.render(_painter, QRectF(335, 120, draw_size.width(), draw_size.height()))
        _painter.end()
        self.preview = False

    def check_image(self, filename):
        """
        Checks a filename to see if the image can be loaded.
        Parameters
        ----------
        filename : (str)
            Inputted filename by user

        Returns
        -------
        tuple : (str, misc)
            Error message and None if an error is present or None and a
            QSvgRenderer/QPixmap (depending on file type).

        """
        error = None
        file_type = None

        abs_path = os.path.expanduser(os.path.expandvars(filename))

        if not os.path.isabs(abs_path):
            try:
                if is_qt_designer():
                    p = self.get_designer_window()
                    if p is not None:
                        ui_dir = p.absoluteDir().absolutePath()
                        abs_path = os.path.join(ui_dir, abs_path)
                else:
                    parent_display = self.widget.find_parent_display()
                    base_path = None
                    if parent_display:
                        base_path = os.path.dirname(
                            parent_display.loaded_file())
                    abs_path = find_file(abs_path, base_path=base_path)
            except Exception as ex:
                print("Exception: ", ex)
                error = "Unable to find full filepath for {}".format(filename)
                abs_path = filename
        # First, lets try SVG.  We have to try SVG first, otherwise
        # QPixmap will happily load the SVG and turn it into a raster image.
        # Really annoying: We have to try to load the file as SVG,
        # and we expect it will fail often (because many images aren't SVG).
        # Qt prints a warning message to stdout any time SVG loading fails.
        # So we have to temporarily silence Qt warning messages here.
        qInstallMessageHandler(self.qt_message_handler)
        svg = QSvgRenderer()
        if svg.load(abs_path):
            file_type = svg
            qInstallMessageHandler(None)
            return error, file_type
        qInstallMessageHandler(None)
        # SVG didn't work, lets try QPixmap
        image = QPixmap(abs_path)
        if not image.isNull():
            file_type = image
            return error, file_type
        # If we get this far, the file specified could not be loaded at all.
        if error is None:
            error = "Could not load image \n{}".format(filename)
        return error, file_type

    def get_designer_window(self):  # pragma: no cover
        # Internal function to find the designer window that owns this widget.
        p = self.widget.parent()
        while p is not None:
            if isinstance(p, QtDesigner.QDesignerFormWindowInterface):
                return p
            p = p.parent()
        return None

    def is_data_valid(self):
        """
        Sanity check the form data.

        Returns
        -------
        tuple : (bool, str)
            True and "" in case there is no error or False and the error message
            otherwise.
        """
        errors = []
        for state, filename in self.symbols.items():
            if state is None or state == "":
                errors.append("Image {} has no state".format(filename))
            error, file_type = self.check_image(filename)
            if error:
                errors.append(error)

        if len(errors) > 0:
            error_msg = os.linesep.join(errors)
            return False, error_msg

        return True, ""

    def qt_message_handler(self, msg_type, *args):
        # Intentionally suppress all qt messages.  Make sure not to leave this handler installed.
        pass

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
