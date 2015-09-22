from PyQt4.QtGui import QLineEdit, QApplication, QColor, QPalette
from PyQt4.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QState, QStateMachine, QPropertyAnimation, QString
from channel import PyDMChannel

class PyDMLineEdit(QLineEdit):
  __pyqtSignals__ = ("send_value_signal(QString)",
                     "connected_signal()",
                     "disconnected_signal()", 
                     "no_alarm_signal()", 
                     "minor_alarm_signal()", 
                     "major_alarm_signal()", 
                     "invalid_alarm_signal()")
                     
  #Emitted when the user changes the value.
  send_value_signal = pyqtSignal(QString)
  
  def __init__(self, channel=None, parent=None):
    super(PyDMLineEdit, self).__init__(parent)
    self._channel = channel
    self.value = None
    self.returnPressed.connect(self.sendValue)
  
  def focusOutEvent(self, event):
    self.setText(self.value)
    super(PyDMLineEdit, self).focusOutEvent(event)
    
  @pyqtSlot(str)
  def recieveValue(self, new_val):
    self.value = new_val
    if not self.hasFocus():
      self.setText(self.value)
  
  @pyqtSlot()
  def sendValue(self):
    self.send_value_signal.emit(self.text())
    
  #false = disconnected, true = connected
  @pyqtSlot(bool)
  def connectionStateChanged(self, connected):
    self.setEnabled(connected)
  
  @pyqtSlot(bool)
  def writeAccessChanged(self, write_access):
    self.setReadOnly(not write_access)
  
  def getChannel(self):
    return QString.fromAscii(self._channel)
  
  def setChannel(self, value):
    if self._channel != value:
      self._channel = str(value)

  def resetChannel(self):
    if self._channel != None:
      self._channel = None
    
  channel = pyqtProperty("QString", getChannel, setChannel, resetChannel)

  def channels(self):
    return [PyDMChannel(address=self.channel, connection_slot=self.connectionStateChanged, value_slot=self.recieveValue, write_access_slot=self.writeAccessChanged, value_signal=self.send_value_signal)]