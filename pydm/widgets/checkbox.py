from ..PyQt.QtGui import QCheckBox, QApplication, QColor, QPalette
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QState, QStateMachine, QPropertyAnimation
from .channel import PyDMChannel
from .base import PyDMWidget

class PyDMCheckbox(QCheckBox, PyDMWidget):
  __pyqtSignals__ = ("send_value_signal(str)",
                     "connected_signal()",
                     "disconnected_signal()", 
                     "no_alarm_signal()", 
                     "minor_alarm_signal()", 
                     "major_alarm_signal()", 
                     "invalid_alarm_signal()")
                     
  #Emitted when the user changes the value.
  send_value_signal = pyqtSignal(str)
  
  def __init__(self, parent=None, channel=None):
    super(PyDMCheckbox, self).__init__(parent)
    self._write_access = False
    self.checkEnableState()
    self.clicked.connect(self.sendValue)
      
  @pyqtSlot(int)
  @pyqtSlot(float)
  @pyqtSlot(str)
  def receiveValue(self, new_val):
    if new_val > 0:
      self.setChecked(True)
    else:
      self.setChecked(False)
  
  @pyqtSlot(bool)
  def sendValue(self, checked):
    if checked:
      self.send_value_signal.emit(str(1))
    else:
      self.send_value_signal.emit(str(0))
    
  @pyqtSlot(bool)
  def writeAccessChanged(self, write_access):
    self._write_access = write_access
    self.checkEnableState()
  
  def checkEnableState(self):
    self.setEnabled(self._write_access and self._connected)
  
  def channels(self):
    return [PyDMChannel(address=self.channel, connection_slot=self.connectionStateChanged, value_slot=self.receiveValue, write_access_slot=self.writeAccessChanged, value_signal=self.send_value_signal)]
