from ..PyQt.QtGui import QLabel, QApplication, QColor
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty
from pyqtgraph import PlotWidget
from pyqtgraph import PlotCurveItem
import numpy as np
from .baseplot import BasePlot
from .channel import PyDMChannel
import itertools
import json
from collections import OrderedDict
from .. import utilities

class NoDataError(Exception):
	pass

class WaveformCurveItem(PlotCurveItem):
	data_changed = pyqtSignal()
	def __init__(self, y_addr=None, x_addr=None, **kws):
		y_addr = "" if y_addr is None else y_addr
		if kws.get('name') is None:
			y_name = utilities.remove_protocol(y_addr)
			if x_addr is None:
				plot_name = y_name
			else:
				x_name = utilities.remove_protocol(x_addr)
				plot_name = "{y} vs. {x}".format(y=y_name, x=x_name)
			kws['name'] = plot_name
		self.x_channel = None
		self.y_channel = None
		self.x_address = x_addr
		self.y_address = y_addr
		self.x_waveform = None
		self.y_waveform = None
		super(WaveformCurveItem, self).__init__(**kws)
	
	@property
	def color_string(self):
		return str(utilities.colors.svg_color_from_hex(self.color.name(), hex_on_fail=True))
	
	@color_string.setter
	def color_string(self, new_color_string):
		self.setPen(QColor(str(new_color_string)))
	
	@property
	def color(self):
		return self.opts['pen'].color()
	
	@property
	def x_address(self):
		if self.x_channel is None:
			return None
		return self.x_channel.address
	
	@x_address.setter
	def x_address(self, new_address):
		if new_address is None or len(str(new_address)) < 1:
			self.x_channel = None
			return
		self.x_channel = PyDMChannel(address=new_address, connection_slot=self.xConnectionStateChanged, waveform_slot=self.receiveXWaveform)
	
	@property
	def y_address(self):
		if self.y_channel is None:
			return None
		return self.y_channel.address
	
	@y_address.setter
	def y_address(self, new_address):
		if new_address is None or len(str(new_address)) < 1:
			self.y_channel = None
			return
		self.y_channel = PyDMChannel(address=new_address, connection_slot=self.yConnectionStateChanged, waveform_slot=self.receiveYWaveform)
	
	def to_dict(self):
		return OrderedDict([("y_channel", self.y_address), ("x_channel", self.x_address), ("name", self.name()), ("color", self.color_string)])
	
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
		if len(init_x_channels) != len(init_y_channels):
			raise ValueError("If lists are provided for both X and Y channels, they must be the same length.")
		#self.channel_pairs is an ordered dictionary that is keyed on a (x_channel, y_channel) tuple, with WaveformCurveItem values.
		#It gets populated in self.addChannel().
		self.channel_pairs = OrderedDict()
		init_channel_pairs = zip(init_x_channels, init_y_channels)
		for (x_chan, y_chan) in init_channel_pairs:
			self.addChannel(y_chan, x_channel=x_chan)
	
	def addChannel(self, y_channel=None, x_channel=None, name=None, color=None):
		curve = WaveformCurveItem(y_addr=y_channel, x_addr=x_channel, name=name)
		curve.data_changed.connect(self.redrawPlot)
		self.channel_pairs[(y_channel, x_channel)] = curve
		self.addCurve(curve, curve_color=color)
	
	def removeChannel(self, curve):
		curve.data_changed.disconnect(self.redrawPlot)
		self.removeCurve(curve)
	
	def removeChannelAtIndex(self, index):
		curve = self._curves[index]
		self.removeChannel(curve)
		
	def updateAxes(self):
		plot_xmin = None
		plot_xmax = None
		plot_ymin = None
		plot_ymax = None
		for curve in self._curves:
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
		for curve in self._curves:
			curve.redrawCurve()
	
	def clearCurves(self):
		super(PyDMWaveformPlot, self).clear()
	
	def getCurves(self):
		return [json.dumps(curve.to_dict()) for curve in self._curves]
	
	def setCurves(self, new_list):
		new_list = [str(i) for i in new_list]
		#super(PyDMTimePlot, self).clear()
		self.clearCurves()
		for curve_dict in new_list:
			d = json.loads(str(curve_dict))
			color = d.get('color')
			if color:
				color = QColor(color)
			self.addChannel(d['y_channel'], d['x_channel'], name=d.get('name'), color=color)
		
	curves = pyqtProperty("QStringList", getCurves, setCurves)
					
	def channels(self):
		chans = []
		chans.extend([curve.y_channel for curve in self._curves])
		chans.extend([curve.x_channel for curve in self._curves if curve.x_channel is not None])
		return chans
