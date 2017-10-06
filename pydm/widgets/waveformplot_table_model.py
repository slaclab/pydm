from ..PyQt.QtCore import QAbstractTableModel, Qt, QModelIndex, QVariant
from ..PyQt.QtGui import QBrush, QColor
from operator import itemgetter
from .. import utilities
from .waveformplot import WaveformCurveItem

class PyDMWaveformPlotCurvesModel(QAbstractTableModel):
    name_for_symbol = {v: k for k, v in WaveformCurveItem.symbols.items()}
    """ This is the data model used by the waveform plot curve editor.
    It basically acts as a go-between for the curves in a plot, and
    QTableView items.
    """
    def __init__(self, plot, parent=None):
        super(PyDMWaveformPlotCurvesModel, self).__init__(parent=parent)
        self._plot = plot
        self._column_names = ("Y Channel", "X Channel", "Label", "Color", "Connect Points", "Data Point Symbol", "Redraw Mode")

    @property
    def plot(self):
        return self._plot

    @plot.setter
    def plot(self, new_plot):
        self.beginResetModel()
        self._plot = new_plot
        self.endResetModel()

    #QAbstractItemModel Implementation
    def clear(self):
        self.plot.clearCurves()

    def flags(self, index):
        column_name = self._column_names[index.column()]
        if column_name == "Connect Points":
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
        if column_name == "Color":
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def rowCount(self, parent=None):
        if parent is not None and parent.isValid():
            return 0
        return len(self.plot._curves)

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
        curve = self.plot._curves[index.row()]
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if column_name == "Y Channel":
                if curve.y_address is None:
                    return QVariant()
                return str(curve.y_address)
            elif column_name == "X Channel":
                if curve.x_address is None:
                    return QVariant()
                return str(curve.x_address)
            elif column_name == "Label":
                if curve.name() is None:
                    return QVariant()
                return str(curve.name())
            elif column_name == "Color":
                return curve.color_string
            elif column_name == "Connect Points":
                return QVariant()
            elif column_name == "Data Point Symbol":
                if curve.symbol is None:
                    return "None"
                return self.name_for_symbol[curve.symbol]
            elif column_name == "Redraw Mode":
                return curve.redraw_mode
        elif role == Qt.BackgroundRole and column_name == "Color":
            return QBrush(curve.color)
        elif role == Qt.CheckStateRole and column_name == "Connect Points":
            if curve.connect_points:
                return Qt.Checked
            else:
                return Qt.Unchecked
        else:
            return QVariant()

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        if index.row() >= self.rowCount():
            return False
        if index.column() >= self.columnCount():
            return False
        column_name = self._column_names[index.column()]
        curve = self.plot._curves[index.row()]
        if role == Qt.EditRole:
            if isinstance(value, QVariant):
                value = value.toString()
            if column_name == "Y Channel":
                curve.y_address = str(value)
            elif column_name == "X Channel":
                curve.x_address = str(value)
            elif column_name == "Label":
                curve.setData(name=str(value))
            elif column_name == "Color":
                curve.color = value
            elif column_name == "Data Point Symbol":
                curve.symbol = str(value)
            elif column_name == "Redraw Mode":
                curve.redraw_mode = int(value)
            else:
                return False
        elif role == Qt.CheckStateRole and column_name == "Connect Points":
            curve.connect_points = bool(value)
        else:
            return False
        self.dataChanged.emit(index, index)
        return True

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return super(PyDMWaveformPlotCurvesModel, self).headerData(section, orientation, role)
        if orientation == Qt.Horizontal and section < self.columnCount():
            return str(self._column_names[section])
        elif orientation == Qt.Vertical and section < self.rowCount():
            return section
    #End QAbstractItemModel implementation.

    def append(self, y_address=None, x_address=None, name=None, color=None):
        self.beginInsertRows(QModelIndex(), len(self._plot._curves), len(self._plot._curves))
        self._plot.addChannel(y_address, x_address, name, color)
        self.endInsertRows()

    def removeAtIndex(self, index):
        self.beginRemoveRows(QModelIndex(), index.row(), index.row())
        self._plot.removeChannelAtIndex(index.row())
        self.endRemoveRows()
    
    def needsColorDialog(self, index):
        column_name = self._column_names[index.column()]
        if column_name == "Color":
            return True
        return False