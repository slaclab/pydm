from qtpy.QtCore import QAbstractTableModel, Qt, QModelIndex, QVariant
from .baseplot import BasePlotAxisItem


class BasePlotAxesModel(QAbstractTableModel):
    """ The data model for the axes tab in the plot curve editor.
        Acts as a go-between for the axes in a plot, and QTableView items. """

    name_for_orientations = {v: k for k, v in BasePlotAxisItem.axis_orientations.items()}

    def __init__(self, plot, parent=None):
        super(BasePlotAxesModel, self).__init__(parent=parent)
        self._plot = plot
        self._column_names = ("Y-Axis Name", "Y-Axis Orientation", "Min Y Range",
                              "Max Y Range", "Enable Auto Range")

    @property
    def plot(self):
        return self._plot

    @plot.setter
    def plot(self, new_plot):
        self._plot = new_plot

    def flags(self, index):
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
            return axis.name
        elif column_name == "Y-Axis Orientation":
            return self.name_for_orientations.get(axis.orientation, 'Left')
        elif column_name == "Min Y Range":
            return axis.min_range
        elif column_name == "Max Y Range":
            return axis.max_range
        elif column_name == "Enable Auto Range":
            return axis.auto_range

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

    def set_data(self, column_name, axis, value):
        if column_name == "Y-Axis Name":
            axis.name = str(value)
        elif column_name == "Y-Axis Orientation":
            if value is None:
                axis.orientation = 'left'  # The PyQtGraph default is the left axis
            else:
                axis.orientation = str(value)
        elif column_name == "Min Y Range":
            axis.min_range = float(value)
        elif column_name == "Max Y Range":
            axis.max_range = float(value)
        elif column_name == "Enable Auto Range":
            axis.auto_range = bool(value)
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
        """ Append a row to the table """
        self.beginInsertRows(QModelIndex(), len(self._plot._axes), len(self._plot._axes))
        self._plot.addAxis(plot_data_item=None, name=name, orientation='left')
        self.endInsertRows()

    def removeAtIndex(self, index):
        """ Removes the axis at the given index on the plot, along with its row in the view """
        self.beginRemoveRows(QModelIndex(), index.row(), index.row())
        self._plot.removeAxisAtIndex(index.row())
        self.endRemoveRows()
