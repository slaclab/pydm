from qtpy.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableView,
                            QAbstractItemView, QSpacerItem, QSizePolicy,
                            QDialogButtonBox, QPushButton, QTabWidget,
                            QComboBox, QStyledItemDelegate, QColorDialog)
from qtpy.QtCore import Qt, Slot, QModelIndex, QItemSelection
from qtpy.QtDesigner import QDesignerFormWindowInterface
from .baseplot import BasePlotCurveItem
from .baseplot_table_model import BasePlotCurvesModel
from .axis_table_model import BasePlotAxesModel
from collections import OrderedDict


class BasePlotCurveEditorDialog(QDialog):
    """QDialog that is used in Qt Designer to edit the properties of the
    curves in a waveform plot.  This dialog is shown when you double-click
    the plot, or when you right click it and choose 'edit curves'.

    This thing is mostly just a wrapper for a table view, with a couple
    buttons to add and remove curves, and a button to save the changes."""
    TABLE_MODEL_CLASS = BasePlotCurvesModel
    AXIS_MODEL_CLASS = BasePlotAxesModel
    AXIS_MODEL_TAB_INDEX = 1

    def __init__(self, plot, parent=None):
        super(BasePlotCurveEditorDialog, self).__init__(parent)
        self.tab_widget = QTabWidget()
        self.plot = plot
        self.setup_ui()
        self.table_model = self.TABLE_MODEL_CLASS(self.plot)
        self.table_view.setModel(self.table_model)
        self.table_model.plot = plot
        self.axis_model = self.AXIS_MODEL_CLASS(self.plot)
        self.axis_view.setModel(self.axis_model)
        self.axis_model.plot = plot
        # self.table_view.resizeColumnsToContents()
        self.add_button.clicked.connect(self.addCurve)
        self.remove_button.clicked.connect(self.removeSelectedCurve)
        self.remove_button.setEnabled(False)
        self.remove_axis_button.clicked.connect(self.removeSelectedAxis)
        self.remove_axis_button.setEnabled(False)
        self.table_view.selectionModel().selectionChanged.connect(
            self.handleSelectionChange)
        self.axis_view.selectionModel().selectionChanged.connect(
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
        self.table_view.setColumnWidth(0, 160)
        self.table_view.setColumnWidth(1, 160)
        self.table_view.setColumnWidth(2, 160)
        #self.vertical_layout.addWidget(self.table_view)
        self.vertical_layout.addWidget(self.tab_widget)
        self.tab_widget.addTab(self.table_view, "Curves")

        self.axis_view = QTableView(self)
        self.axis_view.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.axis_view.setProperty("showDropIndicator", False)
        self.axis_view.setDragDropOverwriteMode(False)
        self.axis_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.axis_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.axis_view.setSortingEnabled(False)
        self.axis_view.horizontalHeader().setStretchLastSection(True)
        self.axis_view.verticalHeader().setVisible(False)
        self.tab_widget.addTab(self.axis_view, "Axes")

        self.tab_widget.currentChanged.connect(self.fillAxisData)

        self.add_remove_layout = QHBoxLayout()
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding,
                             QSizePolicy.Minimum)
        self.add_remove_layout.addItem(spacer)
        self.add_button = QPushButton("Add Curve", self)
        self.add_remove_layout.addWidget(self.add_button)
        self.remove_button = QPushButton("Remove Curve", self)
        self.add_remove_layout.addWidget(self.remove_button)
        self.remove_axis_button = QPushButton("Remove Axis", self)
        self.add_remove_layout.addWidget(self.remove_axis_button)
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
        self.table_view.setItemDelegateForColumn(index+4, symbol_delegate)
        line_delegate = LineColumnDelegate(self)
        self.table_view.setItemDelegateForColumn(index+2, line_delegate)
        color_delegate = ColorColumnDelegate(self)
        self.table_view.setItemDelegateForColumn(index, color_delegate)
        axis_delegate = AxisColumnDelegate(self)
        self.axis_view.setItemDelegateForColumn(1, axis_delegate)
        #self.table_view.hideColumn(1)

    @Slot()
    def addCurve(self):
        self.table_model.append()

    @Slot()
    def removeSelectedCurve(self):
        self.table_model.removeAtIndex(self.table_view.currentIndex())

    @Slot()
    def removeSelectedAxis(self):
        print(f'Attempting to remove axis row at index: {self.axis_view.currentIndex()}')
        self.axis_model.removeAtIndex(self.axis_view.currentIndex())

    @Slot(QItemSelection, QItemSelection)
    def handleSelectionChange(self, selected, deselected):
        self.remove_button.setEnabled(
            self.table_view.selectionModel().hasSelection())
        self.remove_axis_button.setEnabled(
            self.axis_view.selectionModel().hasSelection())

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
            print(f'About to set axes with? {self.plot.yAxes}')
            formWindow.cursor().setProperty("yAxes", self.plot.yAxes)
            formWindow.cursor().setProperty("curves", self.plot.curves)
        self.accept()

    #def fillAxisData(self, tab_index):
    @Slot(int)
    def fillAxisData(self, tab_index, axis_name_col_index=4):
        """ When the user clicks on the axis tab, prefill it with rows based on the curves they have created """
        print(f'tab changed to tab with index: {tab_index} and we will look for axis name at index: {axis_name_col_index}')
        if tab_index != self.AXIS_MODEL_TAB_INDEX:
            return

        self.plot.plotItem.hideAxis('left')

        curve_axis_names = set(str(self.table_model.index(i, axis_name_col_index).data())
                               for i in range(self.table_model.rowCount()))

        existing_axis_names = set(str(self.axis_model.index(i, 0).data())
                                  for i in range(self.axis_model.rowCount()))

        names_to_add = curve_axis_names - existing_axis_names

        print(f'Set difference was: {names_to_add}')

        for name in names_to_add:
            print(f'Considering name: {name}')
            if name:
                print(f'Adding axis: {name}')
                self.axis_model.append(name)

        print("End fillAxisData")



class ColorColumnDelegate(QStyledItemDelegate):
    """The ColorColumnDelegate is an item delegate that is installed on the
    color column of the table view.  Its only job is to ensure that the default
    editor widget (a line edit) isn't displayed for items in the color column.
    """
    def createEditor(self, parent, option, index):
        return None


class AxisColumnDelegate(QStyledItemDelegate):

    """
    AxisColumnDelegate draws a QComboBox with the allowed values for the axis orientation
    column value, which must map to the values expected by PyQtGraph. Helps ensure that the
    user doesn't have to know what these exact values are, and prevents frustrating typos.
    """
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(BasePlotCurveItem.axis_orientations.keys())
        return editor

    def setEditorData(self, editor, index):
        val = str(index.model().data(index, Qt.EditRole))
        editor.setCurrentText(val)

    def setModelData(self, editor, model, index):
        val = BasePlotCurveItem.axis_orientations[editor.currentText()]
        model.setData(index, val, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


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
