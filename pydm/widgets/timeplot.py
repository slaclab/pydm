from ..PyQt.QtGui import QLabel, QApplication, QColor
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QTimer, QObject
from pyqtgraph import PlotWidget, ViewBox, AxisItem, PlotItem, GraphicsObject, PlotCurveItem
import numpy as np
import time
from .baseplot import BasePlot
from .channel import PyDMChannel

class TimePlotCurveItem(PlotCurveItem):
  def __init__(self, channel, **kws):
    self.curve_name = kws.pop('name', None)
    self._bufferSize = 1
    self._update_mode = PyDMTimePlot.SynchronousMode
    self.data_buffer = np.zeros((2,self._bufferSize), order='f',dtype=float)
    if self.curve_name is None:
      self.curve_name = channel.name
    self.connected = False
    self.points_accumulated = 0
    self.latest_value = None
    self.channel = PyDMChannel(address=channel, connection_slot=self.connectionStateChanged, value_slot=self.receiveNewValue)
    super(TimePlotCurveItem, self).__init__(**kws)
    
  @pyqtSlot(bool)
  def connectionStateChanged(self, connected):
    #Maybe change pen stroke?
    self.connected = connected
  
  @pyqtSlot(float)
  @pyqtSlot(int)
  def receiveNewValue(self, new_value):
    if self._update_mode == PyDMTimePlot.SynchronousMode:
      self.data_buffer = np.roll(self.data_buffer, -1)
      self.data_buffer[0, self._bufferSize - 1] = time.time()
      self.data_buffer[1, self._bufferSize - 1] = new_value
      if self.points_accumulated < self._bufferSize:
        self.points_accumulated = self.points_accumulated + 1
    elif self._update_mode == PyDMTimePlot.AsynchronousMode:
      self.latest_value = new_value
      
  
  @pyqtSlot()
  def asyncUpdate(self):
    if self._update_mode != PyDMTimePlot.AsynchronousMode:
      return
    self.data_buffer = np.roll(self.data_buffer, -1)
    self.data_buffer[0, self._bufferSize - 1] = time.time()
    self.data_buffer[1, self._bufferSize - 1] = self.latest_value
    if self.points_accumulated < self._bufferSize:
      self.points_accumulated = self.points_accumulated + 1    
    
  def initialize_buffer(self):
    self.points_accumulated = 0
    #If you don't specify dtype=float, you don't have enough resolution for the timestamp data.
    self.data_buffer = np.zeros((2,self._bufferSize), order='f',dtype=float)
    self.data_buffer[0].fill(time.time())
    
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
  
  @pyqtSlot()
  def redrawCurve(self):
    if self.connected:
      self.setData(y=self.data_buffer[1, -self.points_accumulated:], x=self.data_buffer[0, -self.points_accumulated:])
  
  def setUpdatesAsynchronously(self, value):
    if value == True:
      self._update_mode = PyDMTimePlot.AsynchronousMode
    else:
      self._update_mode = PyDMTimePlot.SynchronousMode
    self.initialize_buffer()

  def resetUpdatesAsynchronously(self):
    self._update_mode = PyDMTimePlot.SynchronousMode
    self.initialize_buffer()
  
  def max_x(self):
    return self.data_buffer[0, -1]

class PyDMTimePlot(BasePlot):
  SynchronousMode = 1
  AsynchronousMode = 2
  def __init__(self, parent=None, init_y_channels=[], background='default'):
    self._bottom_axis = TimeAxisItem('bottom')
    self._left_axis = AxisItem('left')
    super(PyDMTimePlot, self).__init__(parent=parent, background=background, axisItems={'bottom': self._bottom_axis, 'left': self._left_axis})
    for channel in init_y_channels:
      self.addYChannel(channel)
    self.plotItem.disableAutoRange(ViewBox.XAxis)
    self.y_waveform = None
    self._bufferSize = 1
    self.redraw_timer = QTimer(self)
    self.redraw_timer.setInterval(20)
    self.redraw_timer.timeout.connect(self.redrawPlot)
    self.update_timer = QTimer(self)
    self._time_span = 5.0 #This is in seconds
    self._update_interval = 100
    self.update_timer.setInterval(self._update_interval)
    self._update_mode = PyDMTimePlot.SynchronousMode
    #Due to a bug in pyqtgraph, we have to remove a bunch of leftover garbage axes.
    #It looks like this bug will be fixed in a future version of pyqtgraph.
    #NOTE: I think this was fixed in PyQtGraph 0.10.0, see if removing this is OK.
    for child in self.getPlotItem().childItems():
      if isinstance(child, AxisItem):
        if child not in [self.getPlotItem().axes[k]['item'] for k in self.getPlotItem().axes]:
          child.deleteLater()
  
  # Adds a new curve to the current plot
  def addYChannel(self, ychannel, name=None):
    if name is None:
      try:
        name = ychannel.split('://')[1]
      except IndexError:
        name = ychannel
    if name in self._curves:
      raise ValueError("Channel {chan} is already being plotted.  Cannot add the same channel twice.")
    # Add curve
    new_curve = TimePlotCurveItem(ychannel, name=name)
    new_curve.setUpdatesAsynchronously(self.updatesAsynchronously)
    self.update_timer.timeout.connect(new_curve.asyncUpdate)
    self.addCurve(name, plot_item=new_curve)
    self.redraw_timer.start()
  
  def removeYChannel(self, name):
    curve = self._curves[name]
    self.update_timer.timeout.disconnect(curve.asyncUpdate)
    self.removeCurve(curve)
    if len(self._curves) < 1:
      self.redraw_timer.stop()
  
  @pyqtSlot()
  def redrawPlot(self):
    self.updateXAxis()
    for curve in self._curves.values():
      curve.redrawCurve()

  def updateXAxis(self, update_immediately=False):
    if self._update_mode == PyDMTimePlot.SynchronousMode:
      maxrange = max([curve.max_x() for curve in self._curves.values()])
    else:
      maxrange = time.time()
    minrange = maxrange - self._time_span 
    self.plotItem.setXRange(minrange,maxrange,padding=0.0,update=update_immediately)

  def getChannelList(self):
    return [curve.channel.address for curve in self._curves.values()]
  
  def setChannelList(self, new_list):
    old_list = set(self.getChannelList())
    new_list = set(new_list)
    new_channels = new_list - old_list
    channels_to_remove = old_list - new_list
    for channel in new_channels:
      self.addYChannel(channel)
    for channel in channels_to_remove:
      self.removeYChannel(channel)
    
  channelList = pyqtProperty("QStringList", getChannelList, setChannelList)

  def getBufferSize(self):
    return int(self._bufferSize)
  
  def setBufferSize(self, value):
    if self._bufferSize != int(value):
      self._bufferSize = max(int(value),1)
      for curve in self._curves.values():
        curve.setBufferSize(value)

  def resetBufferSize(self):
    if self._bufferSize != 1:
      self._bufferSize = 1
      for curve in self._curves.values():
        curve.resetBufferSize()
    
  bufferSize = pyqtProperty("int", getBufferSize, setBufferSize, resetBufferSize)
  
  def getUpdatesAsynchronously(self):
    return self._update_mode==PyDMTimePlot.AsynchronousMode
  
  def setUpdatesAsynchronously(self, value):
    for curve in self._curves.values():
      curve.setUpdatesAsynchronously(value)
    if value == True:
      self._update_mode = PyDMTimePlot.AsynchronousMode
      self.update_timer.start()
    else:
      self._update_mode = PyDMTimePlot.SynchronousMode
      self.update_timer.stop()

  def resetUpdatesAsynchronously(self):
    self._update_mode = PyDMTimePlot.SynchronousMode
    self.update_timer.stop()
    for curve in self._curves.values():
      curve.resetUpdatesAsynchronously()
    
  updatesAsynchronously = pyqtProperty("bool", getUpdatesAsynchronously, setUpdatesAsynchronously, resetUpdatesAsynchronously)

  def getTimeSpan(self):
    return float(self._time_span)
  
  def setTimeSpan(self, value):
    value = float(value)
    if self._time_span != value:
      self._time_span = value
      if self.getUpdatesAsynchronously():
        for curve in self._curves.values():
          curve.setBufferSize(int((self._time_span*1000.0)/self._update_interval))
      self.updateXAxis(update_immediately=True)

  def resetTimeSpan(self):
    if self._time_span != 5.0:
      self._time_span = 5.0
      if self.getUpdatesAsynchronously():
        for curve in self._curves.values():
          curve.setBufferSize(int((self._time_span*1000.0)/self._update_interval))
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
        self.setBufferSize(int((self._time_span*1000.0)/self._update_interval))

  def resetUpdateInterval(self):
    if self._update_interval != 100:
      self._update_interval = 100
      self.update_timer.setInterval(self._update_interval)
      if self.getUpdatesAsynchronously():
        self.setBufferSize(int((self._time_span*1000.0)/self._update_interval))
      
  updateInterval = pyqtProperty(float, getUpdateInterval, setUpdateInterval, resetUpdateInterval)
  
  def getAutoRangeX(self):
    return False
  
  def setAutoRangeX(self, value):
    self._auto_range_x = False
    self.plotItem.enableAutoRange(ViewBox.XAxis,enable=self._auto_range_x)
  
  def channels(self):
    return [curve.channel for curve in self._curves.values()]
    
class TimeAxisItem(AxisItem):
  def tickStrings(self, values, scale, spacing):
    strings = []
    for val in values:
      strings.append(time.strftime("%H:%M:%S",time.localtime(val)))
    return strings
