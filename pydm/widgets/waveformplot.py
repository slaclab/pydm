from ..PyQt.QtGui import QLabel, QApplication, QColor
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty
from pyqtgraph import PlotWidget
from pyqtgraph import PlotCurveItem
import numpy as np
from .baseplot import BasePlot
from .channel import PyDMChannel
import itertools
from collections import OrderedDict

class NoDataError(Exception):
  pass

class WaveformCurveItem(PlotCurveItem):
  data_changed = pyqtSignal()
  def __init__(self, y_channel, x_channel=None, **kws):
    self.curve_name = kws.pop('name', None)
    if self.curve_name is None:
      try:
        y_name = y_channel.split("://")[1]
      except IndexError:
        y_name = y_channel
      if x_channel is None:
        self.curve_name = y_name
      else:
        try:
          x_name = x_channel.split("://")[1]
        except IndexError:
          x_name = x_channel
        self.curve_name = "{y} vs. {x}".format(y=y_name, x=x_name)
    if x_channel is not None:
      self.x_channel = PyDMChannel(address=x_channel, connection_slot=self.xConnectionStateChanged, waveform_slot=self.receiveXWaveform)
    else:
      self.x_channel = None
    self.y_channel = PyDMChannel(address=y_channel, connection_slot=self.yConnectionStateChanged, waveform_slot=self.receiveYWaveform)
    self.x_waveform = None
    self.y_waveform = None
    super(WaveformCurveItem, self).__init__(**kws)
  
  @pyqtSlot(bool)
  def xConnectionStateChanged(self, connected):
    pass
    
  @pyqtSlot(bool)
  def yConnectionStateChanged(self, connected):
    pass
  
  @pyqtSlot(np.ndarray)
  def receiveXWaveform(self, new_waveform):
    self.x_waveform = new_waveform
    #Don't redraw unless we already have Y data.
    if self.y_waveform is not None:
      self.data_changed.emit()
  
  @pyqtSlot(np.ndarray)
  def receiveYWaveform(self, new_waveform):
    self.y_waveform = new_waveform
    if self.x_channel is None or self.x_waveform is not None:
      self.data_changed.emit()
  
  def redrawCurve(self):
    #We try to be nice: if the X waveform doesn't have the same number of points as the Y waveform,
    #we'll truncate whichever was longer so that they are both the same size.
    if self.x_waveform is None:
      self.setData(y=self.y_waveform)
      return
    if self.x_waveform.shape[0] > self.y_waveform.shape[0]:
        self.x_waveform = self.x_waveform[:self.y_waveform.shape[0]]
    elif self.x_waveform.shape[0] < self.y_waveform.shape[0]:
        self.y_waveform = self.y_waveform[:self.x_waveform.shape[0]]
    self.setData(x=self.x_waveform, y=self.y_waveform)
  
  def limits(self):
    """Returns a nested tuple of limits: ((xmin, xmax), (ymin, ymax))"""
    if self.y_waveform is None:
      raise NoDataError("Curve has no Y data, cannot determine limits.")
    if self.x_waveform is None:
      yspan = float(np.amax(self.y_waveform)) - float(np.amin(self.y_waveform))
      return ((0, len(self.y_waveform)), (float(np.amin(self.y_waveform) - yspan), float(np.amax(self.y_waveform) + yspan)))
    else:
      return ((np.amin(self.x_waveform), np.amax(self.x_waveform)), (np.amin(self.y_waveform), np.amax(self.y_waveform)))
  
class PyDMWaveformPlot(BasePlot):
  def __init__(self, parent=None, init_x_channels=[], init_y_channels=[], background='default'):
    super(PyDMWaveformPlot, self).__init__(parent, background)
    #If the user supplies a single string instead of a list, wrap it in a list.
    if isinstance(init_x_channels, str):
      init_x_channels = [init_x_channels]
    if isinstance(init_y_channels, str):
      init_y_channels = [init_y_channels]
    if len(init_x_channels) == 0:
      init_x_channels = list(itertools.repeat(None, len(init_y_channels)))
    if len(init_x_channels) > 0 and len(init_x_channels) != len(init_y_channels):
      raise ValueError("If lists are provided for both X and Y channels, they must be the same length.")
    #self.channel_pairs is an ordered dictionary that is keyed on a (x_channel, y_channel) tuple, with WaveformCurveItem values.
    #It gets populated in self.addChannel().
    self.channel_pairs = OrderedDict()
    init_channel_pairs = zip(init_x_channels, init_y_channels)
    for (x_chan, y_chan) in init_channel_pairs:
      self.addChannel(y_chan, x_channel=x_chan)
  
  def addChannel(self, y_channel, x_channel=None, name=None):
    curve = WaveformCurveItem(y_channel=y_channel, x_channel=x_channel, name=name)
    curve.data_changed.connect(self.redrawPlot)
    self.channel_pairs[(y_channel, x_channel)] = curve
    self.addCurve(curve.curve_name, plot_item=curve)
  
  def removeChannel(self, y_channel, x_channel=None):
    curve = self.channel_pairs[(y_channel, x_channel)]
    curve.data_changed.disconnect(self.redrawPlot)
    self.removeCurve(curve.curve_name)
    del self.channel_pairs[(y_channel, x_channel)]
    
  def updateAxes(self):
    plot_xmin = None
    plot_xmax = None
    plot_ymin = None
    plot_ymax = None
    for curve in self._curves.values():
      try:
        ((curve_xmin, curve_xmax), (curve_ymin, curve_ymax)) = curve.limits()
      except NoDataError:
        continue
      if plot_xmin is None or curve_xmin < plot_xmin:
        plot_xmin = curve_xmin
      if plot_xmax is None or curve_xmax > plot_xmax:
        plot_xmax = curve_xmax
      if plot_ymin is None or curve_ymin < plot_ymin:
        plot_ymin = curve_ymin
      if plot_ymax is None or curve_ymax > plot_ymax:
        plot_ymax = curve_ymax  
    self.plotItem.setLimits(xMin=plot_xmin, xMax=plot_xmax, yMin=plot_ymin, yMax=plot_ymax)
  
  @pyqtSlot()
  def redrawPlot(self):
    self.updateAxes()
    for curve in self._curves.values():
      curve.redrawCurve()
      
  def getChannelList(self):
    channel_list = []
    for channel_pair in self.channel_pairs:
      if channel_pair[1] is None:
        channel_list.append(channel_pair[0])
      else:
        channel_list.append("{y}, {x}".format(y=channel_pair[0], x=channel_pair[1]))
    return channel_list
  
  def setChannelList(self, new_list):
    old_pairs = set(self.channel_pairs.keys())
    #Turn the new_list from a list of strings into a list of channel pair tuples
    new_pairs = set()
    for item in new_list:
      pair = str(item).split(",")
      if len(pair) > 1:
        pair = tuple(pv.strip() for pv in pair)
      else:
        pair = (pair[0].strip(), None)
      new_pairs.add(pair)
    new_channels = new_pairs - old_pairs
    channels_to_remove = old_pairs - new_pairs
    for pair in new_channels:
      self.addChannel(pair[0], pair[1])
    for pair in channels_to_remove:
      self.removeChannel(pair[0], pair[1])
    
  channelList = pyqtProperty("QStringList", getChannelList, setChannelList)
    
  def channels(self):
    chans = []
    chans.extend([curve.y_channel for curve in self._curves.values()])
    chans.extend([curve.x_channel for curve in self._curves.values() if curve.x_channel is not None])
    return chans
