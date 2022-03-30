from qtpy.QtWidgets import QTableWidget, QTableWidgetItem, QApplication
from qtpy.QtGui import QCursor
from qtpy.QtCore import Slot, Property, Qt, QEvent
import numpy as np
from .base import PyDMWritableWidget


class PyDMWaveformTable(QTableWidget, PyDMWritableWidget):
    """
    A QTableWidget with support for Channels and more from PyDM.

    Values of the array are displayed in the selected number of columns.
    The number of rows is determined by the size of the waveform.
    It is possible to define the labels of each row and column.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

    def __init__(self, parent=None, init_channel=None):
        QTableWidget.__init__(self, parent)
        PyDMWritableWidget.__init__(self, init_channel=init_channel)
        self._columnHeaders = ["Value"]
        self._rowHeaders = []
        self._itemsFlags = (Qt.ItemIsSelectable |
                            Qt.ItemIsEditable |
                            Qt.ItemIsEnabled)
        self.waveform = None
        self._valueBeingSet = False
        self.setColumnCount(1)
        self.cellChanged.connect(self.send_waveform)

    def value_changed(self, new_waveform):
        """
        Callback invoked when the Channel value is changed.

        Parameters
        ----------
        new_waveform : np.ndarray
            The new waveform value from the channel.
        """
        PyDMWritableWidget.value_changed(self, new_waveform)
        self._valueBeingSet = True
        self.waveform = new_waveform
        col_count = self.columnCount()
        len_wave = len(new_waveform)
        row_count = len_wave//col_count + (1 if len_wave % col_count else 0)
        self.setRowCount(row_count)
        for ind, element in enumerate(new_waveform):
            i, j = ind//col_count, ind % col_count
            value_cell = QTableWidgetItem(str(element))
            value_cell.setFlags(self._itemsFlags)
            self.setItem(i, j, value_cell)

        self.setVerticalHeaderLabels(self._rowHeaders)
        self.setHorizontalHeaderLabels(self._columnHeaders)
        self._valueBeingSet = False

    @Slot(int, int)
    def send_waveform(self, row, column):
        """Update Channel value when cell value is changed.

        Parameters
        ----------
        row : int
            Row of the changed cell.
        column : int
            Column of the changed cell.
        """
        if self._valueBeingSet:
            return
        item = self.item(row, column)
        if item and self.subtype:
            new_val = self.subtype(item.text())
            ind = row*self.columnCount() + column
            self.waveform[ind] = new_val
            self.send_value_signal[np.ndarray].emit(self.waveform)

    def check_enable_state(self):
        """
        For PyDMWaveformTable, we want to make the individual cells
        editable when we have write access.
        """
        PyDMWritableWidget.check_enable_state(self)
        self.setEnabled(True)
        if self._write_access and self._connected:
            self._itemsFlags = Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsEnabled
        elif self._connected:
            self._itemsFlags = Qt.ItemIsSelectable|Qt.ItemIsEnabled
        else:
            self._itemsFlags = Qt.ItemIsSelectable
        for col in range(0, self.columnCount()):
            for row in range(0, self.rowCount()):
                item = self.item(row, col)
                if item is not None:
                    item.setFlags(self._itemsFlags)

    def eventFilter(self, obj, event):
        status = self._connected
        if event.type() == QEvent.Leave:
            QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
        elif event.type() == QEvent.Enter and not status:
            QApplication.setOverrideCursor(QCursor(Qt.ForbiddenCursor))
        return False

    @Property("QStringList")
    def columnHeaderLabels(self):
        """
        Return the list of labels for the columns of the Table.

        Returns
        -------
        list of strings
        """
        return self._columnHeaders

    @columnHeaderLabels.setter
    def columnHeaderLabels(self, new_labels):
        """
        Set the list of labels for the columns of the Table.

        If new_labels is empty the column numbers will be used.

        Parameters
        ----------
        new_labels : list of strings
        """
        if new_labels:
            new_labels += (self.columnCount() - len(new_labels)) * [""]
        self._columnHeaders = new_labels
        self.setHorizontalHeaderLabels(self._columnHeaders)

    @Property("QStringList")
    def rowHeaderLabels(self):
        """
        Return the list of labels for the rows of the Table.

        Returns
        -------
        list of strings
        """
        return self._rowHeaders

    @rowHeaderLabels.setter
    def rowHeaderLabels(self, new_labels):
        """
        Set the list of labels for the rows of the Table.

        If new_labels is empty the row numbers will be used.

        Parameters
        ----------
        new_labels : list of strings
        """
        if new_labels:
            new_labels += (self.rowCount() - len(new_labels)) * [""]
        self._rowHeaders = new_labels
        self.setVerticalHeaderLabels(self._rowHeaders)
