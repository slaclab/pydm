import logging
import numpy as np
from operator import itemgetter
from pydm.widgets.base import PyDMWidget, PyDMWritableWidget
from qtpy import QtCore, QtWidgets

logger = logging.getLogger(__name__)


class PythonTableModel(QtCore.QAbstractTableModel):
    def __init__(self, column_names, initial_list=None, parent=None, edit_method=None, can_edit_method=None):
        super().__init__(parent)
        self.parent = parent
        self._list = None
        self._column_names = column_names
        self.edit_method = edit_method
        self.can_edit_method = can_edit_method
        self.list = initial_list

    @property
    def list(self):
        return self._list

    @list.setter
    def list(self, new_list):
        if new_list is None:
            new_list = []
        self.beginResetModel()
        self._list = list(new_list)
        self.endResetModel()

    # QAbstractItemModel Implementation
    def clear(self):
        self.list = []

    def flags(self, index):
        f = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
        if self.edit_method is not None:
            editable = True
            if self.can_edit_method is not None:
                editable = self.can_edit_method(self._list[index.row()][index.column()])
            if editable:
                f = f | QtCore.Qt.ItemIsEditable
        return f

    def rowCount(self, parent=None):
        if parent is not None and parent.isValid():
            return 0
        return len(self._list)

    def columnCount(self, parent=None):
        return len(self._column_names)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        if index.row() >= self.rowCount():
            return None
        if index.column() >= self.columnCount():
            return None
        if role == QtCore.Qt.DisplayRole:
            try:
                item = str(self._list[index.row()][index.column()])
            except IndexError:
                item = ""
            return item
        else:
            return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if self.edit_method is None:
            return False
        if role != QtCore.Qt.EditRole:
            return False
        if not index.isValid():
            return False
        if index.row() >= self.rowCount():
            return False
        if index.column() >= self.columnCount():
            return False

        success = self.edit_method(self.parent, index.row(), index.column(), value)

        if success:
            self.dataChanged.emit(index, index)
        return success

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return super().headerData(section, orientation, role)
        if orientation == QtCore.Qt.Horizontal and section < self.columnCount():
            return str(self._column_names[section])
        elif orientation == QtCore.Qt.Vertical and section < self.rowCount():
            return section

    def sort(self, col, order=QtCore.Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        sort_reversed = order == QtCore.Qt.AscendingOrder
        self._list.sort(key=itemgetter(col), reverse=sort_reversed)
        self.layoutChanged.emit()

    # End QAbstractItemModel implementation.

    # Python collection implementation.
    def __len__(self):
        return len(self._list)

    def __iter__(self):
        return iter(self._list)

    def __contains__(self, value):
        return value in self._list

    def __getitem__(self, index):
        return self._list[index]

    def __setitem__(self, index, value):
        if len(value) != self.columnCount():
            msg = "Items must have the same length as the column count ({})"
            raise ValueError(msg.format(self.columnCount()))
        self._list[index] = value
        self.dataChanged.emit(index, index)

    def __delitem__(self, index):
        if (index + 1) > len(self):
            raise IndexError("list assignment index out of range")
        self.beginRemoveRows(QtCore.QModelIndex(), index, index)
        del self._list[index]
        self.endRemoveRows()

    def append(self, value):
        self.beginInsertRows(QtCore.QModelIndex(), len(self._list), len(self._list))
        self._list.append(value)
        self.endInsertRows()

    def extend(self, values):
        self.beginInsertRows(QtCore.QModelIndex(), len(self._list), len(self._list) + len(values) - 1)
        self._list.extend(values)
        self.endInsertRows()

    def remove(self, item):
        index = None
        try:
            index = self._list.index(item)
        except ValueError:
            raise ValueError("list.remove(x): x not in list")
        del self[index]

    def pop(self, index=None):
        if len(self._list) < 1:
            raise IndexError("pop from empty list")
        if index is None:
            index = len(self._list) - 1
        del self[index]

    def count(self, item):
        return self._list.count(item)

    def reverse(self):
        self.layoutAboutToBeChanged.emit()
        self._list.reverse()
        self.layoutChanged.emit()


class PyDMNTTable(QtWidgets.QWidget, PyDMWritableWidget):
    """
    The PyDMNTTable is a table widget used to display PVA NTTable data.

    The PyDMNTTable has two ways of filling the table from the data.
    If the incoming data dictionary has a 'labels' and/or a 'value' key.
    Then the list of labels will be set with the data from the 'labels' key.
    While the data from the 'value' key will be used to set the values in the table.
    if neither 'labels' or 'value' key are present in the incoming 'data' dictionary,
    then the keys of the data dictionary are set as the labels
    and all the values stored by the keys will make up the values of the table.

    Parameters
    ----------
    parent : QWidget, optional
        The parent widget for the PyDMNTTable
    init_channel : str, optional
        The channel to be used by the widget.
    """

    def __init__(self, parent=None, init_channel=None):
        self._read_only = True

        super().__init__(parent)
        PyDMWidget.__init__(self, init_channel=init_channel)
        self.setLayout(QtWidgets.QVBoxLayout())
        self._table = QtWidgets.QTableView(self)
        self.layout().addWidget(self._table)
        self._model = None
        self._table_labels = None
        self._table_values = []
        self.edit_method = None

    # On pyside6, we need to expilcity call pydm's base class's eventFilter() call or events
    # will not propagate to the parent classes properly.
    def eventFilter(self, obj, event):
        return PyDMWritableWidget.eventFilter(self, obj, event)

    @QtCore.Property(bool)
    def readOnly(self):
        return self._read_only

    @readOnly.setter
    def readOnly(self, value):
        if self._read_only != value:
            self._read_only = value

    def check_enable_state(self):
        """
        Checks whether or not the widget should be disable.

        """
        PyDMWritableWidget.check_enable_state(self)
        self.setEnabled(True)
        tooltip = self.toolTip()

        if self.readOnly:
            if tooltip != "":
                tooltip += "\n"
            tooltip += "Running PyDMNTTable on Read-Only mode."

        self.setToolTip(tooltip)

    def value_changed(self, data=None):
        """
        Callback invoked when the Channel value is changed.

        Parameters
        ----------
        data : dict
            The new value from the channel.
        """
        if data is None:
            return

        super().value_changed(data)

        labels = data.get("labels", None)
        values = data.get("value", {})

        if not values:
            values = data.values()

        if labels is None or len(labels) == 0:
            labels = data.keys()
            labels = list(labels)

        try:
            values = list(zip(*[v for k, v in data.items() if k != "labels"]))
        except TypeError:
            logger.exception("NTTable value items must be iterables.")

        self._table_values = values

        if labels != self._table_labels:
            if not self.readOnly:
                self.edit_method = PyDMNTTable.send_table
            else:
                self.edit_method = None

            self._table_labels = labels
            self._model = PythonTableModel(labels, initial_list=values, parent=self, edit_method=self.edit_method)
            self._table.setModel(self._model)
        else:
            self._model.list = values

    def send_table(self, row, column, value):
        """
        Update Channel value when cell value is changed.

        Parameters
        ----------
        row : int
            index of row
        column : int
            index of column
        value : str
            new value of cell
        """
        if isinstance(self.value[self._table_labels[column]], np.ndarray):
            self.value[self._table_labels[column]] = self.value[self._table_labels[column]].copy()

        if isinstance(self.value[self._table_labels[column]][row], np.bool_):
            if value == "True":
                self.value[self._table_labels[column]][row] = True
            elif value == "False":
                self.value[self._table_labels[column]][row] = False
        else:
            self.value[self._table_labels[column]][row] = value

        value_to_send = {k: v for k, v in self.value.items() if k != "labels"}

        # dictionary needs to be wrapped in another dictionary with a key 'value'
        # to be passed back to the p4p plugin.
        emit_dict = {"value": value_to_send}

        self.send_value_signal[dict].emit(emit_dict)
        return True
