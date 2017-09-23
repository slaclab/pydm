from ..PyQt.QtGui import QTableWidget, QTableWidgetItem
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, Qt
from .channel import PyDMChannel
import numpy as np
from .base import PyDMWritableWidget

class PyDMWaveformTable(QTableWidget, PyDMWritableWidget):
    def __init__(self, parent=None, init_channel=None):
        QTableWidget.__init__(self, parent)
        PyDMWritableWidget.__init__(self, init_channel=init_channel)
        self.setColumnCount(1)
        self.columnHeader = "Value"
        self.waveform = None
        self.setHorizontalHeaderLabels([self.columnHeader])
        
    def value_changed(self, new_waveform):
        PyDMWritableWidget.value_changed(self, new_waveform)
        self.waveform = new_waveform
        self.setRowCount(len(new_waveform))
        #TODO: Fix this hacky crap where I disconnect/reconnect the changed signal whenever the pv updates.
        try:
            self.cellChanged.disconnect()
        except:
            pass
        for i, element in enumerate(new_waveform):
            index_cell = QTableWidgetItem(str(i))
            value_cell = QTableWidgetItem(str(element))
            value_cell.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
            self.setVerticalHeaderItem(i,index_cell)
            self.setItem(i,0,value_cell)
        self.cellChanged.connect(self.send_data_for_cell)
    
    @pyqtSlot(int, int)
    def send_data_for_cell(self, row, column):
        item = self.item(row, column)
        new_val = float(item.text())
        self.waveform[row] = new_val
        self.send_value_signal[np.ndarray].emit(self.waveform)
