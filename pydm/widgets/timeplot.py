from PyQt4.QtGui import QLabel, QApplication, QColor
from PyQt4.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QString, QTimer
from pyqtgraph import PlotWidget, ViewBox
from pyqtgraph import PlotCurveItem
import numpy as np
import time
from channel import PyDMChannel

class PyDMTimePlot(PlotWidget):
  SynchronousMode = 1
  AsynchronousMode = 2
  def __init__(self, init_y_channel=None, parent=None, background='default'):
    super(PyDMTimePlot, self).__init__(parent, background)
    self._ychannel = init_y_channel
    self.showGrid(x=False, y=False)
    self._curveColor=QColor(255,255,255)
    self.curve = PlotCurveItem(pen=self._curveColor)
    self.addItem(self.curve)
    self.plotItem = self.getPlotItem()
    self.plotItem.hideButtons()
    self.plotItem.disableAutoRange(ViewBox.XAxis)
    self.y_waveform = None
    self._bufferSize = 1
    self.redraw_timer = QTimer(self)
    self.redraw_timer.setInterval(20)
    self.redraw_timer.timeout.connect(self.redrawPlot)
    self.update_timer = QTimer(self)
    self._time_span = 5.0 #This is in seconds
    self._update_interval = 100
    self._update_mode = PyDMTimePlot.SynchronousMode
  
  def configure_timer(self):
    self.update_timer.stop()
    try:
      self.update_timer.timeout.disconnect()
    except:
      pass
    if self._update_mode == PyDMTimePlot.AsynchronousMode:
      self.latest_value = None
      self.update_timer.setInterval(self._update_interval)
      self.update_timer.timeout.connect(self.asyncUpdate)
    
  def initialize_buffer(self):
    self.points_accumulated = 0
    #If you don't specify dtype=float, you don't have enough resolution for the timestamp data.
    self.data_buffer = np.zeros((2,self._bufferSize), order='f',dtype=float)
    self.data_buffer[1].fill(time.time())
  
  @pyqtSlot(float)
  @pyqtSlot(int)
  def receiveNewValue(self, new_value):
    if self._update_mode == PyDMTimePlot.SynchronousMode:
      self.data_buffer = np.roll(self.data_buffer,-1)
      self.data_buffer[0,self._bufferSize - 1] = new_value
      self.data_buffer[1,self._bufferSize - 1] = time.time()
      if self.points_accumulated < self._bufferSize:
        self.points_accumulated = self.points_accumulated + 1
    elif self._update_mode == PyDMTimePlot.AsynchronousMode:
      self.latest_value = new_value
  
  @pyqtSlot()
  def asyncUpdate(self):
    self.data_buffer = np.roll(self.data_buffer,-1)
    self.data_buffer[0,self._bufferSize - 1] = self.latest_value
    self.data_buffer[1,self._bufferSize - 1] = time.time()
    if self.points_accumulated < self._bufferSize:
      self.points_accumulated = self.points_accumulated + 1
    #self.redrawPlot()
    
  @pyqtSlot()
  def redrawPlot(self):
    if self._update_mode == PyDMTimePlot.SynchronousMode:
      maxrange = self.data_buffer[1, -1]
    else:
      maxrange = time.time()
    minrange = maxrange - self._time_span 
    self.plotItem.setXRange(minrange,maxrange,padding=0.0,update=False)
    self.curve.setData(y=self.data_buffer[0,-self.points_accumulated:],x=self.data_buffer[1,-self.points_accumulated:])
  
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
    if connected:
      self.redraw_timer.start()
      if self._update_mode == PyDMTimePlot.AsynchronousMode:
        self.update_timer.start()
    else:
      self.redraw_timer.stop()
      self.update_timer.stop()
  
  def getYChannel(self):
    return QString.fromAscii(self._ychannel)
  
  def setYChannel(self, value):
    if self._ychannel != value:
      self._ychannel = str(value)

  def resetYChannel(self):
    if self._ychannel != None:
      self._ychannel = None
    
  yChannel = pyqtProperty("QString", getYChannel, setYChannel, resetYChannel)
  
  def getBufferSize(self):
    return int(self._bufferSize)
  
  def setBufferSize(self, value):
    if self._bufferSize != int(value):
      self._bufferSize = max(int(value),1)
      self.initialize_buffer()

  def resetBufferSize(self):
    if self._bufferSize != 1:
      self._bufferSize = 1
      self.initialize_buffer()
    
  bufferSize = pyqtProperty("int", getBufferSize, setBufferSize, resetBufferSize)
  
  def getUpdatesAsynchronously(self):
    return self._update_mode==PyDMTimePlot.AsynchronousMode
  
  def setUpdatesAsynchronously(self, value):
    if value == True:
      self._update_mode = PyDMTimePlot.AsynchronousMode
    else:
      self._update_mode = PyDMTimePlot.SynchronousMode
    self.configure_timer()
    self.initialize_buffer()

  def resetUpdatesAsynchronously(self):
    self._update_mode = PyDMTimePlot.SynchronousMode
    self.configure_timer()
    self.initialize_buffer()
    
  updatesAsynchronously = pyqtProperty("bool", getUpdatesAsynchronously, setUpdatesAsynchronously, resetUpdatesAsynchronously)

  def getTimeSpan(self):
    return float(self._time_span)
  
  def setTimeSpan(self, value):
    value = float(value)
    if self._time_span != value:
      self._time_span = value
      self.setBufferSize(int(self._time_span*1000.0/self._update_interval))

  def resetTimeSpan(self):
    if self._time_span != 5.0:
      self._time_span = 5.0
      self.setBufferSize(int(self._time_span*1000.0/self._update_interval))
    
  timeSpan = pyqtProperty(float, getTimeSpan, setTimeSpan, resetTimeSpan)
  
  def getUpdateInterval(self):
    return float(self._update_interval)/1000.0
  
  def setUpdateInterval(self, value):
    value = abs(int(1000.0*value))
    if self._update_interval != value:
      self._update_interval = value
      self.update_timer.setInterval(self._update_interval)
      self.setBufferSize(int(self._time_span*1000.0/self._update_interval))

  def resetUpdateInterval(self):
    if self._update_interval != 100:
      self._update_interval = 100
      self.update_timer.setInterval(self._update_interval)
      self.setBufferSize(int(self._time_span*1000.0/self._update_interval))
      
  updateInterval = pyqtProperty(float, getUpdateInterval, setUpdateInterval, resetUpdateInterval)
  
  def channels(self):
    return [PyDMChannel(address=self.yChannel, connection_slot=self.connectionStateChanged, value_slot=self.receiveNewValue, severity_slot=self.alarmSeverityChanged)]
  
  def getCurveColor(self):
    return self._curveColor

  def setCurveColor(self, color):
    if self._curveColor != color:
      self._curveColor = color
      self.curve.setPen(self._curveColor)
    
  curveColor = pyqtProperty(QColor, getCurveColor, setCurveColor)