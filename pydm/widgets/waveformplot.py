# Try PyQt5
try:
    pyqt5 = True
    from PyQt5.QtWidgets import QLabel, QApplication
    from PyQt5.QtGui import QColor
    from PyQt5.QtCore import pyqtSignal, pyqtSlot, pyqtProperty
except ImportError:
    pyqt5 =  False
    # Imports for Pyqt4
    from PyQt4.QtGui import QLabel, QApplication, QColor
    from PyQt4.QtCore import pyqtSignal, pyqtSlot, pyqtProperty
from pyqtgraph import PlotWidget
from pyqtgraph import PlotCurveItem
from baseplot import BasePlot
import numpy as np
from channel import PyDMChannel

class PyDMWaveformPlot(BasePlot):
  def __init__(self, init_x_channel=None, init_y_channel=None, parent=None, background='default'):
    super(PyDMWaveformPlot, self).__init__(parent, background)
    self._ychannel = init_x_channel
    self._xchannel = init_y_channel
    self.x_waveform = None
    self.y_waveform = None
  
  @pyqtSlot(np.ndarray)
  def receiveXWaveform(self, new_waveform):
    self.x_waveform = new_waveform
    self.redrawPlot()
  
  @pyqtSlot(np.ndarray)
  def receiveYWaveform(self, new_waveform):
    self.y_waveform = new_waveform
    self.redrawPlot()

  def updateAxes(self):
    if self.x_waveform is None:
      yspan = float(np.amax(self.y_waveform)) - float(np.amin(self.y_waveform))
      self.plotItem.setLimits(xMin=0, xMax=len(self.y_waveform), yMin=float(np.amin(self.y_waveform)-yspan), yMax=float(np.amax(self.y_waveform)+yspan))
    else:
      self.plotItem.setLimits(xMin=np.amin(self.x_waveform), xMax=np.amax(self.x_waveform), yMin=np.amin(self.y_waveform), yMax=np.amax(self.y_waveform))
  
  def redrawPlot(self):
    self.updateAxes()
    self.curve.setData(x=self.x_waveform, y=self.y_waveform)
  
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
  
  def getYChannel(self):
    return str(self._ychannel)
  
  def setYChannel(self, value):
    if self._ychannel != value:
      self._ychannel = str(value)

  def resetYChannel(self):
    if self._ychannel != None:
      self._ychannel = None
    
  yChannel = pyqtProperty(str, getYChannel, setYChannel, resetYChannel)
  
  def getXChannel(self):
    return str(self._xchannel)
  
  def setXChannel(self, value):
    if self._xchannel != value:
      self._xchannel = str(value)

  def resetXChannel(self):
    if self._xchannel != None:
      self._xchannel = None
    
  xChannel = pyqtProperty(str, getXChannel, setXChannel, resetXChannel)
  
  def channels(self):
    return [PyDMChannel(address=self.yChannel, connection_slot=self.connectionStateChanged, waveform_slot=self.receiveYWaveform, severity_slot=self.alarmSeverityChanged), PyDMChannel(address=self.xChannel, connection_slot=self.connectionStateChanged, waveform_slot=self.receiveXWaveform, severity_slot=self.alarmSeverityChanged)]
