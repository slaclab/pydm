from PyQt4.QtGui import QLineEdit, QApplication, QColor, QPalette, QSlider
from PyQt4.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QState, QStateMachine, QPropertyAnimation
from channel import PyDMChannel

class PyDMSlider(QSlider):
  __pyqtSignals__ = ("send_value_signal(str)",
                     "connected_signal()",
                     "disconnected_signal()", 
                     "no_alarm_signal()", 
                     "minor_alarm_signal()", 
                     "major_alarm_signal()", 
                     "invalid_alarm_signal()")
                     
  #Emitted when the user changes the value.
  send_value_signal = pyqtSignal(str)
  
  def __init__(self, channel=None, parent=None):
    super(PyDMSlider, self).__init__(parent)
    self._channel = channel
    self.valueChanged.connect(self.sendValue)
    self._des_max = None
    self._des_min = None
    self._step = '1'
    self._maxrange = '10'
    self._minrange = '-10'
    self.setupRange(self._step)

  #accounts for the fact that the silider only works with integer numbers
  def mapStepSize(self):
      pass

  def setupRange(self,step_size):
    upper_range_int = int((1/float(step_size))*float(self._maxrange))
    lower_range_int = int((1/float(step_size))*float(self._minrange))
    self.setMaximum(upper_range_int)
    self.setMinimum(lower_range_int)
    
  #step size property
  def getStep(self):
    return str(self._step)

  def setStep(self,value):
    self._step = str(value)

  step = pyqtProperty(str,fget=getStep,fset=setStep)

  #max range property
  def getMaxrange(self):
    return str(self._maxrange)

  def setMaxrange(self,value):
    self._maxrange = str(value)

  maxrange = pyqtProperty(str,fget=getMaxrange,fset=setMaxrange)

  #min range property
  def getMinrange(self):
    return str(self._minrange)

  def setMinrange(self,value):
    self._minrange = str(value)

  minrange = pyqtProperty(str,fget=getMinrange,fset=setMinrange)

  #overwrite wheel event to fire only when slider is in focus
  def wheelEvent(self,event):
    pass
  
  #set slider to new position
  #if the slider is not in focus, dont set slider to new position
  @pyqtSlot(str)
  def receiveValue(self, new_val):
    if not self.hasFocus():
      self.setSliderPosition(int(float(new_val)))

  #send out new value to channel 
  @pyqtSlot()
  def sendValue(self):
    if self.hasFocus():
      val = str(float(self.value())*float(self._step))
      self.send_value_signal.emit(val)

  #false = disconnected, true = connected
  @pyqtSlot(bool)
  def connectionStateChanged(self, connected):
    self.setEnabled(connected)
    if connected:
      self.setupRange(self._step)
    
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
    return [PyDMChannel(address=self.channel, connection_slot=self.connectionStateChanged, value_slot=self.receiveValue, value_signal=self.send_value_signal)]
