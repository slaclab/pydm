from qtpy.QtCore import QAbstractTableModel, Qt, QModelIndex, QVariant
from qtpy.QtGui import QBrush
from .baseplot import BasePlotCurveItem


class BasePlotAxesModel(QAbstractTableModel):
    name_for_orientations = {v: k for k, v in BasePlotCurveItem.axis_orientations.items()}
    """ This is the data model used by the waveform plot curve editor.
    It basically acts as a go-between for the curves in a plot, and
    QTableView items.
    """

    def __init__(self, plot, parent=None):
        super(BasePlotAxesModel, self).__init__(parent=parent)
        self._plot = plot
        self._column_names = ("Y-Axis Name", "Y-Axis Location", "Min Y Range",
                              "Max Y Range", "Enable Auto Range")

    @property
    def plot(self):
        return self._plot

    @plot.setter
    def plot(self, new_plot):
        #self.beginResetModel()  # TODO: Remove?
        self._plot = new_plot
        #self.endResetModel()

    # QAbstractItemModel Implementation
    def clear(self):  # TODO: Remove?
        print("A call to clear was ingored")
        #self.plot.clearCurves()

    def flags(self, index):
        column_name = self._column_names[index.column()]
        if column_name == "Color":
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def rowCount(self, parent=None):
        if parent is not None and parent.isValid():
            return 0
        return len(self.plot._axes)

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
        axis = self.plot._axes[index.row()]
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self.get_data(column_name, axis)
        else:
            return QVariant()

    def get_data(self, column_name, axis):
        if column_name == "Y-Axis Name":
            return axis.y_axis_name
        elif column_name == "Y-Axis Location":
            return self.name_for_orientations.get(axis.y_axis_orientation, 'Left')
        elif column_name == "Min Y Range":
            return axis.y_axis_min_range
        elif column_name == "Max Y Range":
            return axis.y_axis_max_range
        elif column_name == "Enable Auto Range":
            return axis.y_axis_auto_range

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        if index.row() >= self.rowCount():
            return False
        if index.column() >= self.columnCount():
            return False
        column_name = self._column_names[index.column()]
        axis = self.plot._axes[index.row()]
        if role == Qt.EditRole:
            if isinstance(value, QVariant):
                value = value.toString()
            if not self.set_data(column_name, axis, value):
                return False
        else:
            return False
        self.dataChanged.emit(index, index)
        return True

    def set_data(self, column_name, curve, value):
        if column_name == "Y-Axis Name":
            curve.y_axis_name = str(value)
        elif column_name == "Y-Axis Location":
            if value is None:
                curve.y_axis_orientation = 'left'  # The PyQtGraph default is the left axis
            else:
                curve.y_axis_orientation = str(value)
        elif column_name == "Min Y Range":
            curve.y_axis_min_range = float(value)
        elif column_name == "Max Y Range":
            curve.y_axis_max_range = float(value)
        elif column_name == "Enable Auto Range":
            curve.y_axis_auto_range = bool(value)  # TODO HIGH: This cannot be correct
        else:
            return False
        return True

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return super(BasePlotAxesModel, self).headerData(
                section, orientation, role)
        if orientation == Qt.Horizontal and section < self.columnCount():
            return str(self._column_names[section])
        elif orientation == Qt.Vertical and section < self.rowCount():
            return section
    # End QAbstractItemModel implementation.

    def append(self, name):
        print('we are appending 1 row for axis table')
        self.beginInsertRows(QModelIndex(), len(self._plot._axes), len(self._plot._axes))
        self._plot.addAxis(plot_data_item=None, name=name, orientation='left')
        self.endInsertRows()

    def removeAtIndex(self, index):
        pass


    # TODO HIGH: Remove
    def needsColorDialog(self, index):
        column_name = self._column_names[index.column()]
        if column_name == "Color":
            return True
        return False
