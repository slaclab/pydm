from qtpy.QtCore import QAbstractTableModel, Qt, QModelIndex, QVariant
from qtpy.QtGui import QBrush
from .baseplot import BasePlotCurveItem


class BasePlotCurvesModel(QAbstractTableModel):
    name_for_symbol = {v: k for k, v in BasePlotCurveItem.symbols.items()}
    name_for_line = {v: k for k, v in BasePlotCurveItem.lines.items()}
    """ This is the data model used by the waveform plot curve editor.
    It basically acts as a go-between for the curves in a plot, and
    QTableView items.
    """

    def __init__(self, plot, parent=None):
        super(BasePlotCurvesModel, self).__init__(parent=parent)
        self._plot = plot
        self._column_names = ("Label", "Color", "Line Style", "Line Width",
                              "Symbol", "Symbol Size")

    @property
    def plot(self):
        return self._plot

    @plot.setter
    def plot(self, new_plot):
        self.beginResetModel()
        self._plot = new_plot
        self.endResetModel()

    # QAbstractItemModel Implementation
    def clear(self):
        self.plot.clearCurves()

    def flags(self, index):
        column_name = self._column_names[index.column()]
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
            return self.get_data(column_name, curve)
        elif role == Qt.BackgroundRole and column_name == "Color":
            return QBrush(curve.color)
        else:
            return QVariant()

    def get_data(self, column_name, curve):
        if column_name == "Label":
            if curve.name() is None:
                return QVariant()
            return str(curve.name())
        elif column_name == "Color":
            return curve.color_string
        elif column_name == "Line Style":
            return self.name_for_line[curve.lineStyle]
        elif column_name == "Line Width":
            return int(curve.lineWidth)
        elif column_name == "Symbol":
            return self.name_for_symbol[curve.symbol]
        elif column_name == "Symbol Size":
            return int(curve.symbolSize)

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
            if not self.set_data(column_name, curve, value):
                return False
        else:
            return False
        self.dataChanged.emit(index, index)
        return True

    def set_data(self, column_name, curve, value):
        if column_name == "Label":
            curve.setData(name=str(value))
        elif column_name == "Color":
            curve.color = value
        elif column_name == "Line Style":
            curve.lineStyle = int(value)
        elif column_name == "Line Width":
            curve.lineWidth = int(value)
        elif column_name == "Symbol":
            if value is None:
                curve.symbol = None
            else:
                curve.symbol = str(value)
        elif column_name == "Symbol Size":
            curve.symbolSize = int(value)
        else:
            return False
        return True

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return super(BasePlotCurvesModel, self).headerData(
                section, orientation, role)
        if orientation == Qt.Horizontal and section < self.columnCount():
            return str(self._column_names[section])
        elif orientation == Qt.Vertical and section < self.rowCount():
            return section
    # End QAbstractItemModel implementation.

    def append(self, name=None, color=None):
        pass

    def removeAtIndex(self, index):
        pass

    def needsColorDialog(self, index):
        column_name = self._column_names[index.column()]
        if column_name == "Color":
            return True
        return False
