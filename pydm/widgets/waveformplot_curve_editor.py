from ..PyQt.QtGui import QDialog, QVBoxLayout, QHBoxLayout, QTableView, QAbstractItemView, QSpacerItem, QSizePolicy, QDialogButtonBox, QPushButton, QItemSelection, QComboBox, QStyledItemDelegate
from ..PyQt.QtCore import Qt, pyqtSlot
from ..PyQt.QtDesigner import QDesignerFormWindowInterface
from .waveformplot_table_model import PyDMWaveformPlotCurvesModel
from .waveformplot import WaveformCurveItem
from collections import OrderedDict

class WaveformPlotCurveEditorDialog(QDialog):
    """WaveformPlotCurveEditorDialog is a QDialog that is used in Qt Designer to
    edit the properties of the curves in a waveform plot.  This dialog is shown
    when you double-click the plot, or when you right click it and choose 'edit curves'.
    
    This thing is mostly just a wrapper for a table view, with a couple buttons to add and
    remove curves, and a button to save the changes.
    """
    def __init__(self, plot, parent=None):
        super(WaveformPlotCurveEditorDialog, self).__init__(parent)
        self.plot = plot
        self.setup_ui()
        self.column_names = ("Y Channel", "X Channel", "Label", "Color", "Connect Points", "Data Point Symbol")
        self.table_model = PyDMWaveformPlotCurvesModel(self.plot)
        self.table_view.setModel(self.table_model)
        self.table_model.plot = plot
        #self.table_view.resizeColumnsToContents()
        self.add_button.clicked.connect(self.addCurve)
        self.remove_button.clicked.connect(self.removeSelectedCurve)
        self.remove_button.setEnabled(False)
        symbol_delegate = SymbolColumnDelegate(self)
        self.table_view.setItemDelegateForColumn(5, symbol_delegate)
        self.table_view.selectionModel().selectionChanged.connect(self.handleSelectionChange)
        
    def setup_ui(self):
        self.resize(800, 300)
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
        self.table_view.setColumnWidth(3, 20)
        self.vertical_layout.addWidget(self.table_view)
        self.add_remove_layout = QHBoxLayout()
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
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
    
    @pyqtSlot()
    def addCurve(self):
        self.table_model.append()
    
    @pyqtSlot()
    def removeSelectedCurve(self):
        self.table_model.removeAtIndex(self.table_view.currentIndex())
        
    @pyqtSlot(QItemSelection, QItemSelection)
    def handleSelectionChange(self, selected, deselected):
        self.remove_button.setEnabled(self.table_view.selectionModel().hasSelection())
    
    @pyqtSlot()
    def saveChanges(self):
        formWindow = QDesignerFormWindowInterface.findFormWindow(self.plot)
        if formWindow:
            formWindow.cursor().setProperty("curves", self.plot.curves)
        self.accept()

class SymbolColumnDelegate(QStyledItemDelegate):
    #reverse_symbols = {v: k for k, v in WaveformCurveItem.symbols.items()}
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(WaveformCurveItem.symbols.keys())
        return editor
    
    def setEditorData(self, editor, index):
        val = str(index.model().data(index, Qt.EditRole))
        editor.setCurrentText(val)
    
    def setModelData(self, editor, model, index):
        val = WaveformCurveItem.symbols[editor.currentText()]
        model.setData(index, val, Qt.EditRole)
    
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
