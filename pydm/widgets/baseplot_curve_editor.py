from functools import partial
from collections import OrderedDict

from qtpy.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableView,
                            QAbstractItemView, QSpacerItem, QSizePolicy,
                            QDialogButtonBox, QPushButton,
                            QComboBox, QStyledItemDelegate, QColorDialog,
                            QLineEdit, QFrame)
from qtpy.QtCore import Qt, Slot, QModelIndex, QItemSelection
from qtpy.QtDesigner import QDesignerFormWindowInterface
from .baseplot import BasePlotCurveItem
from .baseplot_table_model import BasePlotCurvesModel
from .channel_editor import ChannelEditor
from ..utilities.iconfont import IconFont

class BasePlotCurveEditorDialog(QDialog):
    """QDialog that is used in Qt Designer to edit the properties of the
    curves in a waveform plot.  This dialog is shown when you double-click
    the plot, or when you right click it and choose 'edit curves'.

    This thing is mostly just a wrapper for a table view, with a couple
    buttons to add and remove curves, and a button to save the changes."""
    TABLE_MODEL_CLASS = BasePlotCurvesModel

    def __init__(self, plot, parent=None):
        super(BasePlotCurveEditorDialog, self).__init__(parent)
        self.plot = plot
        self.setup_ui()
        self.table_model = self.TABLE_MODEL_CLASS(self.plot)
        self.table_view.setModel(self.table_model)
        self.table_model.plot = plot
        # self.table_view.resizeColumnsToContents()
        self.add_button.clicked.connect(self.addCurve)
        self.remove_button.clicked.connect(self.removeSelectedCurve)
        self.remove_button.setEnabled(False)
        self.table_view.selectionModel().selectionChanged.connect(
            self.handleSelectionChange)
        self.table_view.doubleClicked.connect(self.handleDoubleClick)
        self.resize(800, 300)

    def setup_ui(self):
        self.vertical_layout = QVBoxLayout(self)
        self.table_view = QTableView(self)
        self.table_view.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.table_view.setProperty("showDropIndicator", False)
        self.table_view.setDragDropOverwriteMode(False)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSortingEnabled(False)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setColumnWidth(0, 200)
        self.table_view.setColumnWidth(1, 200)
        self.table_view.setColumnWidth(2, 200)
        self.vertical_layout.addWidget(self.table_view)
        self.add_remove_layout = QHBoxLayout()
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding,
                             QSizePolicy.Minimum)
        self.add_remove_layout.addItem(spacer)
        self.add_button = QPushButton("Add Curve", self)
        self.add_remove_layout.addWidget(self.add_button)
        self.remove_button = QPushButton("Remove Curve", self)
        self.add_remove_layout.addWidget(self.remove_button)
        self.vertical_layout.addLayout(self.add_remove_layout)
        self.button_box = QDialogButtonBox(self)
        self.button_box.setOrientation(Qt.Horizontal)
        self.button_box.addButton("Done", QDialogButtonBox.AcceptRole)
        self.vertical_layout.addWidget(self.button_box)
        self.button_box.accepted.connect(self.saveChanges)
        self.button_box.rejected.connect(self.reject)
        self.setWindowTitle("Waveform Curve Editor")

    def setup_delegate_columns(self, index=2):
        symbol_delegate = SymbolColumnDelegate(self)
        self.table_view.setItemDelegateForColumn(index+3, symbol_delegate)
        line_delegate = LineColumnDelegate(self)
        self.table_view.setItemDelegateForColumn(index+1, line_delegate)
        color_delegate = ColorColumnDelegate(self)
        self.table_view.setItemDelegateForColumn(index, color_delegate)

    @Slot()
    def addCurve(self):
        self.table_model.append()

    @Slot()
    def removeSelectedCurve(self):
        self.table_model.removeAtIndex(self.table_view.currentIndex())

    @Slot(QItemSelection, QItemSelection)
    def handleSelectionChange(self, selected, deselected):
        self.remove_button.setEnabled(
            self.table_view.selectionModel().hasSelection())

    @Slot(QModelIndex)
    def handleDoubleClick(self, index):
        if self.table_model.needsColorDialog(index):
            # The table model returns a QBrush for BackgroundRole, not a QColor
            init_color = self.table_model.data(index,
                                               Qt.BackgroundRole).color()
            color = QColorDialog.getColor(init_color, self)
            if color.isValid():
                self.table_model.setData(index, color, role=Qt.EditRole)

    @Slot()
    def saveChanges(self):
        formWindow = QDesignerFormWindowInterface.findFormWindow(self.plot)
        if formWindow:
            formWindow.cursor().setProperty("curves", self.plot.curves)
        self.accept()


class ColorColumnDelegate(QStyledItemDelegate):
    """The ColorColumnDelegate is an item delegate that is installed on the
    color column of the table view.  Its only job is to ensure that the default
    editor widget (a line edit) isn't displayed for items in the color column.
    """
    def createEditor(self, parent, option, index):
        return None


class LineColumnDelegate(QStyledItemDelegate):
    """LineColumnDelegate draws a QComboBox in the Line Style column, so that users
    can pick the styles they want to display from a list, instead of needing to
    remember the PyQtGraph character codes."""
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(BasePlotCurveItem.lines.keys())
        return editor

    def setEditorData(self, editor, index):
        val = str(index.model().data(index, Qt.EditRole))
        editor.setCurrentText(val)

    def setModelData(self, editor, model, index):
        val = BasePlotCurveItem.lines[editor.currentText()]
        model.setData(index, val, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class SymbolColumnDelegate(QStyledItemDelegate):
    """SymbolColumnDelegate draws a QComboBox in the Symbol column, so that users
    can pick the symbol they want to display from a list, instead of needing to
    remember the PyQtGraph character codes."""
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(BasePlotCurveItem.symbols.keys())
        return editor

    def setEditorData(self, editor, index):
        val = str(index.model().data(index, Qt.EditRole))
        editor.setCurrentText(val)

    def setModelData(self, editor, model, index):
        val = BasePlotCurveItem.symbols[editor.currentText()]
        model.setData(index, val, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class RedrawModeColumnDelegate(QStyledItemDelegate):
    """RedrawModeColumnDelegate draws a QComboBox in the Redraw Mode column, so
    that users can pick the redraw mode from a list."""
    choices = OrderedDict([
        ('X or Y updates', BasePlotCurveItem.REDRAW_ON_EITHER),
        ('Y updates', BasePlotCurveItem.REDRAW_ON_Y),
        ('X updates', BasePlotCurveItem.REDRAW_ON_X),
        ('Both update', BasePlotCurveItem.REDRAW_ON_BOTH)])
    text_for_choices = {v: k for k, v in choices.items()}

    def displayText(self, value, locale):
        return self.text_for_choices[value]

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.choices.keys())
        return editor

    def setEditorData(self, editor, index):
        val = self.text_for_choices[index.model().data(index, Qt.EditRole)]
        editor.setCurrentText(val)

    def setModelData(self, editor, model, index):
        val = self.choices[editor.currentText()]
        model.setData(index, val, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class ChannelColumnDelegate(QStyledItemDelegate):
    """ChannelColumnDelegate draws a LineEdit and a button for the channel
    editor interface so that users can easily configure a new channel."""

    @staticmethod
    def _get_channel_edit(editor):
        channel_edit = editor.findChild(QLineEdit, 'channel_edit')
        return channel_edit

    def edit_channel(self, editor, index):
        channel_edit = self._get_channel_edit(editor)
        config = [['channel', 'Channel', channel_edit.text()]]
        ch_editor = ChannelEditor(config, parent=editor.parent())
        ch_editor.exec_()

        if len(ch_editor.return_value) > 0:
            prop, _, value = ch_editor.return_value[0]
            channel_edit.setText(value)
            index.model().setData(index, str(value), Qt.EditRole)

    def createEditor(self, parent, option, index):
        editor = QFrame(parent)
        editor.setLayout(QHBoxLayout())
        editor.layout().setSpacing(0)
        editor.layout().setContentsMargins(0, 0, 0, 0)

        channel_edit = QLineEdit(parent)
        channel_edit.setObjectName('channel_edit')
        channel_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        btn = QPushButton(parent)
        btn.setIcon(IconFont().icon('edit'))
        btn.clicked.connect(partial(self.edit_channel, editor, index))
        btn.setMaximumWidth(32)
        btn.setMaximumHeight(32)

        editor.layout().addWidget(channel_edit)
        editor.layout().addWidget(btn)

        return editor

    def setEditorData(self, editor, index):
        val = str(index.model().data(index, Qt.EditRole))
        channel_edit = self._get_channel_edit(editor)
        if channel_edit:
            channel_edit.setText(val)

    def setModelData(self, editor, model, index):
        channel_edit = self._get_channel_edit(editor)
        if channel_edit:
            val = channel_edit.text()
            model.setData(index, val, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
