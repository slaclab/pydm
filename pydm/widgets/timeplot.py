from ..PyQt.QtGui import QLabel, QApplication, QColor
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QTimer
from pyqtgraph import PlotWidget, ViewBox, AxisItem, PlotItem
from pyqtgraph import PlotCurveItem
from baseplot import BasePlot
import numpy as np
import time
from channel import PyDMChannel

class PyDMTimePlot(BasePlot):
  SynchronousMode = 1
  AsynchronousMode = 2
  def __init__(self, init_y_channel=None, parent=None, background='default'):
    self._bottom_axis = TimeAxisItem('bottom')
    self._left_axis = AxisItem('left')
    super(PyDMTimePlot, self).__init__(parent=parent, background=background, axisItems={'bottom': self._bottom_axis, 'left': self._left_axis})
    self._ychannel = init_y_channel
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
    #Due to a bug in pyqtgraph, we have to remove a bunch of leftover garbage axes.
    #It looks like this bug will be fixed in a future version of pyqtgraph.
    for child in self.getPlotItem().childItems():
      if isinstance(child, AxisItem):
        if child not in [self.getPlotItem().axes[k]['item'] for k in self.getPlotItem().axes]:
          child.deleteLater()
    
  
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
    self.updateXAxis()
    self.curve.setData(y=self.data_buffer[0,-self.points_accumulated:],x=self.data_buffer[1,-self.points_accumulated:])
  
  def updateXAxis(self, update_immediately=False):
    if self._update_mode == PyDMTimePlot.SynchronousMode:
      maxrange = self.data_buffer[1, -1]
    else:
      maxrange = time.time()
    minrange = maxrange - self._time_span 
    self.plotItem.setXRange(minrange,maxrange,padding=0.0,update=update_immediately)
  
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
  
  @pyqtSlot(str)
  def unitsChanged(self, units):
    self._left_axis.enableAutoSIPrefix(enable=False)
    self._left_axis.setLabel(units=units)
    self._left_axis.showLabel()
  
  def getYChannel(self):
    return str(self._ychannel)
  
  def setYChannel(self, value):
    if self._ychannel != value:
      self._ychannel = str(value)

  def resetYChannel(self):
    if self._ychannel != None:
      self._ychannel = None
    
  yChannel = pyqtProperty(str, getYChannel, setYChannel, resetYChannel)
  
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
      if self.getUpdatesAsynchronously():
        self.setBufferSize(int(self._time_span*1000.0/self._update_interval))
      self.updateXAxis(update_immediately=True)

  def resetTimeSpan(self):
    if self._time_span != 5.0:
      self._time_span = 5.0
      if self.getUpdatesAsynchronously():
        self.setBufferSize(int(self._time_span*1000.0/self._update_interval))
      self.updateXAxis(update_immediately=True)
    
  timeSpan = pyqtProperty(float, getTimeSpan, setTimeSpan, resetTimeSpan)
  
  def getUpdateInterval(self):
    return float(self._update_interval)/1000.0
  
  def setUpdateInterval(self, value):
    value = abs(int(1000.0*value))
    if self._update_interval != value:
      self._update_interval = value
      self.update_timer.setInterval(self._update_interval)
      if self.getUpdatesAsynchronously():
        self.setBufferSize(int(self._time_span*1000.0/self._update_interval))

  def resetUpdateInterval(self):
    if self._update_interval != 100:
      self._update_interval = 100
      self.update_timer.setInterval(self._update_interval)
      if self.getUpdatesAsynchronously():
        self.setBufferSize(int(self._time_span*1000.0/self._update_interval))
      
  updateInterval = pyqtProperty(float, getUpdateInterval, setUpdateInterval, resetUpdateInterval)
  
  def getAutoRangeX(self):
    return False
  
  def setAutoRangeX(self, value):
    self._auto_range_x = False
    self.plotItem.enableAutoRange(ViewBox.XAxis,enable=self._auto_range_x)
  
  def channels(self):
    return [PyDMChannel(address=self.yChannel, connection_slot=self.connectionStateChanged, value_slot=self.receiveNewValue, severity_slot=self.alarmSeverityChanged, unit_slot=self.unitsChanged)]
    
class TimeAxisItem(AxisItem):
  def tickStrings(self, values, scale, spacing):
    strings = []
    for val in values:
      strings.append(time.strftime("%H:%M:%S",time.localtime(val)))
    return strings