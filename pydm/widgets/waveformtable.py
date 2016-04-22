from PyQt4.QtGui import QTableWidget, QTableWidgetItem, QApplication, QColor, QPalette
from PyQt4.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QString, Qt
from channel import PyDMChannel
import numpy as np

class PyDMWaveformTable(QTableWidget):
  #Tell Designer what signals are available.
  __pyqtSignals__ = ("send_value_signal(np.ndarray)",
                     "connected_signal()",
                     "disconnected_signal()", 
                     "no_alarm_signal()", 
                     "minor_alarm_signal()", 
                     "major_alarm_signal()", 
                     "invalid_alarm_signal()")
  send_value_signal = pyqtSignal(np.ndarray)
  def __init__(self, parent=None, init_channel=None):
    super(PyDMWaveformTable, self).__init__(parent=parent)
    self._waveformchannel = init_channel
    self.setColumnCount(1)
    self.columnHeader = "Value"
    self.waveform = None
    self.setHorizontalHeaderLabels([self.columnHeader])
    
    
  @pyqtSlot(np.ndarray)
  def receiveWaveform(self, new_waveform):
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
    print("Cell changed!")
    item = self.item(row, column)
    new_val = float(item.text())
    self.waveform[row] = new_val
    self.send_value_signal.emit(self.waveform)
    
  # -2 to +2, -2 is LOLO, -1 is LOW, 0 is OK, etc.  
  @pyqtSlot(int)
  def alarmStatusChanged(self, new_alarm_state):
    pass
  
  #0 = NO_ALARM, 1 = MINOR, 2 = MAJOR, 3 = INVALID  
  @pyqtSlot(int)
  def alarmSeverityChanged(self, new_alarm_severity):
    pass
    
  #false = disconnected, true = connected
  @pyqtSlot(bool)
  def connectionStateChanged(self, connected):
    pass
  
  def getWaveformChannel(self):
    return QString.fromAscii(self._waveformchannel)
  
  def setWaveformChannel(self, value):
    if self._waveformchannel != value:
      self._waveformchannel = str(value)

  def resetWaveformChannel(self):
    if self._waveformchannel != None:
      self._waveformchannel = None
    
  waveformChannel = pyqtProperty("QString", getWaveformChannel, setWaveformChannel, resetWaveformChannel)
  
  def channels(self):
    return [PyDMChannel(address=self.waveformChannel, connection_slot=self.connectionStateChanged, waveform_slot=self.receiveWaveform, severity_slot=self.alarmSeverityChanged, value_signal=self.send_value_signal)]