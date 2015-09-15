from PyQt4.QtGui import QLabel, QApplication, QColor
from PyQt4.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QString
import pyqtgraph as pg
import numpy as np
from channel import PyDMChannel

class WaveformPlot(pg.PlotWidget):
  send_value_signal = pyqtSignal(str)
  def __init__(self, init_x_channel=None, init_y_channel=None, parent=None, background='default'):
    super(WaveformPlot, self).__init__(parent, background)
    self._ychannel = init_x_channel
    self._xchannel = init_y_channel
    self.showGrid(x=False, y=False)
    self._curveColor=QColor(255,255,255)
    self.curve = pg.PlotCurveItem(pen=self._curveColor)
    self.addItem(self.curve)
    self.plotItem = self.getPlotItem()
    self.plotItem.hideButtons()
    self.x_waveform = None
    self.y_waveform = None
  
  @pyqtSlot(np.ndarray)
  def recieveXWaveform(self, new_waveform):
    self.x_waveform = new_waveform
    self.redrawPlot()
  
  @pyqtSlot(np.ndarray)
  def recieveYWaveform(self, new_waveform):
    self.y_waveform = new_waveform
    self.redrawPlot()
  
  def redrawPlot(self):
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
    return QString.fromAscii(self._ychannel)
  
  def setYChannel(self, value):
    if self._ychannel != value:
      self._ychannel = str(value)

  def resetYChannel(self):
    if self._ychannel != None:
      self._ychannel = None
    
  yChannel = pyqtProperty("QString", getYChannel, setYChannel, resetYChannel)
  
  def getXChannel(self):
    return QString.fromAscii(self._xchannel)
  
  def setXChannel(self, value):
    if self._xchannel != value:
      self._xchannel = str(value)

  def resetXChannel(self):
    if self._xchannel != None:
      self._xchannel = None
    
  xChannel = pyqtProperty("QString", getXChannel, setXChannel, resetXChannel)
  
  def channels(self):
    return [PyDMChannel(address=self.xChannel, connection_slot=self.connectionStateChanged, waveform_slot=self.recieveXWaveform, severity_slot=self.alarmSeverityChanged),
            PyDMChannel(address=self.yChannel, connection_slot=self.connectionStateChanged, waveform_slot=self.recieveYWaveform, severity_slot=self.alarmSeverityChanged)]
  
  def getCurveColor(self):
    return self._curveColor

  def setCurveColor(self, color):
    if self._curveColor != color:
      self._curveColor = color
      self.curve.setPen(self._curveColor)
    
  curveColor = pyqtProperty(QColor, getCurveColor, setCurveColor)