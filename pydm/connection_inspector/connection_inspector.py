from ..PyQt.QtGui import QWidget, QTableView, QAbstractItemView, QVBoxLayout, QAbstractScrollArea
from ..PyQt.QtCore import Qt, QSize
from .connection_table_model import ConnectionTableModel

class ConnectionInspector(QWidget):
    def __init__(self, connections=[], parent=None):
        super(ConnectionInspector, self).__init__(parent, Qt.Window)
        self.table_view = ConnectionTableView(connections, self)
        self.setLayout(QVBoxLayout(self))
        self.layout().addWidget(self.table_view)
    
class ConnectionTableView(QTableView):
    def __init__(self, connections=[], parent=None):
        super(ConnectionTableView, self).__init__(parent)
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(True)
        self.setModel(ConnectionTableModel(connections, self))
        self.resizeColumnsToContents()
        