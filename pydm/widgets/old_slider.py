from ..PyQt.QtGui import QApplication, QColor, QPalette, QSlider
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QState, QStateMachine, QPropertyAnimation
from .channel import PyDMChannel

class PyDMOldSlider(QSlider):
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
    self.sliderMoved.connect(self.sendValue)
    self._step = 1.0
    self._maxrange = 10.0
    self._minrange = -10.0
    #self.setupRange(self._step)

  #accounts for the fact that QSlider only works with integer numbers
  def mapStepSize(self):
      pass

  def setupRange(self,step_size):
    upper_range_int = int((1/float(step_size))*float(self._maxrange))
    lower_range_int = int((1/float(step_size))*float(self._minrange))
    self.setMaximum(upper_range_int)
    self.setMinimum(lower_range_int)
    
  #step size property
  def getSingleStep(self):
    return self._step

  def setSingleStep(self, value):
    self._step = float(value)

  singleStep = pyqtProperty(float, fget=getSingleStep, fset=setSingleStep)

  #max range property
  def getMaximum(self):
    return self._maxrange

  def setMaximum(self, value):
    self._maxrange = float(value)

  maximum = pyqtProperty(float,fget=getMaximum,fset=setMaximum)

  #min range property
  def getMinimum(self):
    return self._minrange

  def setMinimum(self,value):
    self._minrange = float(value)

  minimum = pyqtProperty(float,fget=getMinimum,fset=setMinimum)

  #overwrite wheel event to fire only when slider is in focus
  def wheelEvent(self,event):
    pass
  
  #set slider to new position
  #if the slider is not in focus, dont set slider to new position
  @pyqtSlot(int)
  @pyqtSlot(float)
  def receiveValue(self, new_val):
    if not self.hasFocus():
      self.setSliderPosition(float(new_val))

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
