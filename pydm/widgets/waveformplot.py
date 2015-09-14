from PyQt4.QtGui import QLabel, QApplication, QColor
from PyQt4.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QString
import pyqtgraph as pg
import numpy as np

class WaveformPlot(pg.PlotWidget):
  send_value_signal = pyqtSignal(str)
  def __init__(self, init_channel=None, parent=None, background='default'):
    super(WaveformPlot, self).__init__(parent, background)
    self._channel = init_channel
    self.showGrid(x=False, y=False)
    self._curveColor=QColor(255,255,255)
    self.curve = pg.PlotCurveItem(pen=self._curveColor)
    self.addItem(self.curve)
    self.plotItem = self.getPlotItem()
    self.plotItem.hideButtons()
  
  @pyqtSlot(np.ndarray)
  def recieveWaveform(self, new_waveform):
    self.curve.setData(new_waveform)
  
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
  
  def getChannel(self):
    return QString.fromAscii(self._channel)
  
  def setChannel(self, value):
    if self._channel != value:
      self._channel = str(value)

  def resetChannel(self):
    if self._channel != None:
      self._channel = None
    
  channel = pyqtProperty("QString", getChannel, setChannel, resetChannel)
  
  def getCurveColor(self):
    return self._curveColor

  def setCurveColor(self, color):
    if self._curveColor != color:
      self._curveColor = color
      self.curve.setPen(self._curveColor)
    
  curveColor = pyqtProperty(QColor, getCurveColor, setCurveColor)