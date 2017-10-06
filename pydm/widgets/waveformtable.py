from ..PyQt.QtGui import QTableWidget, QTableWidgetItem
from ..PyQt.QtCore import pyqtSlot, pyqtProperty, Qt
import numpy as np
from .base import PyDMWritableWidget


class PyDMWaveformTable(QTableWidget, PyDMWritableWidget):
    """
    A QTableWidget with support for Channels and more from PyDM.

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

    @pyqtSlot(int, int)
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
        new_val = self.subtype(item.text())
        ind = row*self.columnCount() + column
        self.waveform[ind] = new_val
        self.send_value_signal[np.ndarray].emit(self.waveform)

    @pyqtProperty("QStringList")
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
        self._columnHeaders = new_labels
        self.setHorizontalHeaderLabels(self._columnHeaders)

    @pyqtProperty("QStringList")
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
        self._rowHeaders = new_labels
        self.setVerticalHeaderLabels(self._rowHeaders)

    @pyqtProperty(Qt.ItemFlags)
    def itemsFlags(self):
        """
        Return the flags used in the TableWidgetItems.

        Returns
        -------
        Qt.ItemFlags
        """
        return Qt.ItemFlags(self._itemsFlags)

    @itemsFlags.setter
    def itemsFlags(self, new_flags):
        """
        Set the flags to be used in the TableWidgetItems.

        Parameters
        ----------
        new_flags : Qt.ItemFlags
        """
        self._itemsFlags = Qt.ItemFlags(new_flags)
