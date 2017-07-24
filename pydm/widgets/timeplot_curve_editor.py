from ..PyQt.QtGui import QDialog, QVBoxLayout, QHBoxLayout, QTableView, QAbstractItemView, QSpacerItem, QSizePolicy, QDialogButtonBox, QPushButton, QItemSelection
from ..PyQt.QtCore import Qt, pyqtSlot
from ..PyQt.QtDesigner import QDesignerFormWindowInterface
from .timeplot_table_model import PyDMTimePlotCurvesModel

class TimePlotCurveEditorDialog(QDialog):
  def __init__(self, plot, parent=None):
    super(TimePlotCurveEditorDialog, self).__init__(parent)
    self.plot = plot
    self.setup_ui()
    self.column_names = ("Channel", "Label", "Color")
    self.table_model = PyDMTimePlotCurvesModel(self.plot)
    self.table_view.setModel(self.table_model)
    self.table_model.plot = plot
    #self.table_view.resizeColumnsToContents()
    self.add_button.clicked.connect(self.addCurve)
    self.remove_button.clicked.connect(self.removeSelectedCurve)
    self.remove_button.setEnabled(False)
    self.table_view.selectionModel().selectionChanged.connect(self.handleSelectionChange)
    
  def setup_ui(self):
    self.resize(500, 300)
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
    self.table_view.setColumnWidth(0, 166)
    self.table_view.setColumnWidth(1, 166)
    self.table_view.setColumnWidth(2, 166)
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
    self.setWindowTitle("Timeplot Curve Editor")
  
  @pyqtSlot()
  def addCurve(self):
    self.table_model.append("")
  
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
    