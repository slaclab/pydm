from ..PyQt.QtGui import QDoubleSpinBox, QApplication, QColor, QPalette
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QState, QStateMachine, QPropertyAnimation
from .channel import PyDMChannel

class PyDMSpinbox(QDoubleSpinBox):
  __pyqtSignals__ = ("send_value_signal(float)",
                     "connected_signal()",
                     "disconnected_signal()",
                     "no_alarm_signal()",
                     "minor_alarm_signal()",
                     "major_alarm_signal()",
                     "invalid_alarm_signal()")

  #Emitted when the user changes the value.
  send_value_signal = pyqtSignal(float)

  def __init__(self, parent=None, channel=None):
    super(PyDMSpinbox, self).__init__(parent)
    self._channel = channel
    self._connected = False

    self.valueChanged.connect(self.sendValue)
    #self.valueChanged.connect(self.on_valueChanged)

    self._units = None

    self.valueBeingSet = False

  @pyqtSlot(float)
  def receiveValue(self, new_val):
    self.valueBeingSet = True
    self.setValue(new_val)
    self.valueBeingSet = False

    #self.value = new_val # otherwise there is a loop

  @pyqtSlot(float)
  def sendValue(self, value):
    if not self.valueBeingSet:
        self.send_value_signal.emit(value)

  @pyqtSlot(bool)
  def connectionStateChanged(self, connected):
    self._connected = connected
    #self.checkEnableState()

  @pyqtSlot(bool)
  def writeAccessChanged(self, write_access):
    self._write_access = write_access
  #  self.checkEnableState()

  #def checkEnableState(self):
  #  self.setEnabled(self._write_access and self._connected)

  @pyqtSlot(str)
  def receiveUnits(self,unit):
      """
      Accept a unit to display with a channel's value

      The unit may or may not be displayed based on the :attr:`showUnits`
      attribute. Receiving a new value for the unit causes the display to
      reset.
      """
      self._units = str(unit)
      self._scale = 1
      self.setSuffix(" " + self._units)

  @pyqtSlot(int)
  @pyqtSlot(float)
  def receive_upper_limit(self,limit):
    self.setMaximum(limit)

  @pyqtSlot(int)
  @pyqtSlot(float)
  def receive_lower_limit(self,limit):
    self.setMinimum(limit)

  def getChannel(self):
    return str(self._channel)

  def setChannel(self, value):
    if self._channel != value:
      self._channel = str(value)

  def resetChannel(self):
    if self._channel != None:
      self._channel = None

  channel = pyqtProperty(str, getChannel, setChannel, resetChannel)

  def channels(self):
    return [PyDMChannel(address=self.channel,
                        connection_slot=self.connectionStateChanged,
                        value_slot=self.receiveValue,
                        unit_slot = self.receiveUnits,
                        write_access_slot=self.writeAccessChanged,
                        upper_ctrl_limit_slot = self.receive_upper_limit,
                        lower_ctrl_limit_slot = self.receive_lower_limit,
                        value_signal=self.send_value_signal,
                        )]
