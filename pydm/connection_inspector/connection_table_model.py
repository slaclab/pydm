from qtpy.QtCore import QAbstractTableModel, Qt, QModelIndex, QVariant, QTimer, Slot
from qtpy.QtGui import QBrush
from operator import attrgetter

class ConnectionTableModel(QAbstractTableModel):
    def __init__(self, connections=[], parent=None):
        super(ConnectionTableModel, self).__init__(parent=parent)
        self._column_names = ("protocol", "address", "connected")
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(1000)
        self.update_timer.timeout.connect(self.update_values)
        self.connections = connections
        
    def sort(self, col, order=Qt.AscendingOrder):
        if self._column_names[col] == "value":
            return
        self.layoutAboutToBeChanged.emit()
        sort_reversed = (order == Qt.AscendingOrder)
        self._connections.sort(key=attrgetter(self._column_names[col]), reverse=sort_reversed)
        self.layoutChanged.emit()

    @property
    def connections(self):
        return self._connections

    @connections.setter
    def connections(self, new_connections):
        self.beginResetModel()
        self._connections = new_connections
        self.endResetModel()
        if len(self._connections) > 0:
            self.update_timer.start()
        else:
            self.update_timer.stop()

    # QAbstractItemModel Implementation
    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def rowCount(self, parent=None):
        if parent is not None and parent.isValid():
            return 0
        return len(self._connections)

    def columnCount(self, parent=None):
        return len(self._column_names)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        if index.row() >= self.rowCount():
            return QVariant()
        if index.column() >= self.columnCount():
            return QVariant()
        column_name = self._column_names[index.column()]
        conn = self.connections[index.row()]
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return str(getattr(conn, column_name))
        else:
            return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return super(ConnectionTableModel, self).headerData(
                                                section, orientation, role)
        if orientation == Qt.Horizontal and section < self.columnCount():
            return str(self._column_names[section]).capitalize()
        elif orientation == Qt.Vertical and section < self.rowCount():
            return section
    # End QAbstractItemModel implementation.

    @Slot()
    def update_values(self):
        self.dataChanged.emit(self.index(0,2), self.index(self.rowCount(),2))