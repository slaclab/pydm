from ..PyQt.QtGui import QColor
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty
from pyqtgraph import PlotDataItem
import numpy as np
from .baseplot import BasePlot
from .channel import PyDMChannel
import itertools
import json
from collections import OrderedDict
from .. import utilities

class NoDataError(Exception):
    pass

class WaveformCurveItem(PlotDataItem):
    symbols = OrderedDict([('None', None), ('Circle', 'o'), ('Square', 's'), ('Triangle', 't'), ('Diamond', 'd'), ('Plus', '+')])
    data_changed = pyqtSignal()
    def __init__(self, y_addr=None, x_addr=None, color=None, connect_points=True, **kws):
        y_addr = "" if y_addr is None else y_addr
        if kws.get('name') is None:
            y_name = utilities.remove_protocol(y_addr)
            if x_addr is None:
                plot_name = y_name
            else:
                x_name = utilities.remove_protocol(x_addr)
                plot_name = "{y} vs. {x}".format(y=y_name, x=x_name)
            kws['name'] = plot_name
        self.needs_new_x = True
        self.needs_new_y = True
        self.x_channel = None
        self.y_channel = None
        self.x_address = x_addr
        self.y_address = y_addr
        self.x_waveform = None
        self.y_waveform = None
        self._color = QColor('white')
        if color is not None:
            self._color = color
        super(WaveformCurveItem, self).__init__(**kws)
        self.connect_points = connect_points
    
    @property
    def color_string(self):
        return str(utilities.colors.svg_color_from_hex(self.color.name(), hex_on_fail=True))
    
    @color_string.setter
    def color_string(self, new_color_string):
        self.color = QColor(str(new_color_string))
            
    @property
    def color(self):
        return self._color
    
    @color.setter
    def color(self, new_color):
        if isinstance(new_color, str):
            self.color_string = new_color
            return
        print("Curve is settings its color to: {}".format(new_color.name()))
        self._color = new_color
        if self.connect_points:
            self.setPen(self._color)
    
    @property
    def connect_points(self):
        return self._connect_points
    
    @connect_points.setter
    def connect_points(self, connect):
        self._connect_points = connect
        if self._connect_points:
            self.setPen(self._color)
        else:
            self.setPen(None)
    
    def setPen(self, pen):
        super(WaveformCurveItem, self).setPen(pen)
    
    @property
    def symbol(self):
        return self.opts['symbol']
    
    @symbol.setter
    def symbol(self, new_symbol):
        if new_symbol in self.symbols.values():
            self.setSymbol(new_symbol)
        else:
            self.setSymbol(None)
    
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
        self.x_channel = PyDMChannel(address=new_address, connection_slot=self.xConnectionStateChanged, value_slot=self.receiveXWaveform)
    
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
        self.y_channel = PyDMChannel(address=new_address, connection_slot=self.yConnectionStateChanged, value_slot=self.receiveYWaveform)
    
    def to_dict(self):
        return OrderedDict([("y_channel", self.y_address), ("x_channel", self.x_address), ("name", self.name()), ("color", self.color_string), ("connect_points", self.connect_points), ("symbol", self.symbol)])
    
    @pyqtSlot(bool)
    def xConnectionStateChanged(self, connected):
        pass
        
    @pyqtSlot(bool)
    def yConnectionStateChanged(self, connected):
        pass
    
    @pyqtSlot(np.ndarray)
    def receiveXWaveform(self, new_waveform):
        self.x_waveform = new_waveform
        self.needs_new_x = False
        #Don't redraw unless we already have Y data.
        if not (self.needs_new_x or self.needs_new_y):
            self.data_changed.emit()
    
    @pyqtSlot(np.ndarray)
    def receiveYWaveform(self, new_waveform):
        self.y_waveform = new_waveform
        self.needs_new_y = False
        if self.x_channel is None or not (self.needs_new_x or self.needs_new_y):
            self.data_changed.emit()
    
    def redrawCurve(self):
        #We try to be nice: if the X waveform doesn't have the same number of points as the Y waveform,
        #we'll truncate whichever was longer so that they are both the same size.
        if self.x_waveform is None:
            self.setData(y=self.y_waveform)
            return
        #if self.x_waveform.shape[0] > self.y_waveform.shape[0]:
        #    self.x_waveform = self.x_waveform[:self.y_waveform.shape[0]]
        #elif self.x_waveform.shape[0] < self.y_waveform.shape[0]:
        #    self.y_waveform = self.y_waveform[:self.x_waveform.shape[0]]
        self.setData(x=self.x_waveform, y=self.y_waveform)
        self.needs_new_x = True
        self.needs_new_y = True
    
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
    
    def addChannel(self, y_channel=None, x_channel=None, name=None, color=None, connect_points=True, symbol=None):
        plot_opts = {}
        if symbol is not None:
            plot_opts['symbol'] = symbol
        curve = WaveformCurveItem(y_addr=y_channel, x_addr=x_channel, name=name, color=color, connect_points=connect_points, **plot_opts)
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
        try:
            new_list = [json.loads(str(i)) for i in new_list]
        except ValueError as e:
            print("Error parsing curve json data: {}".format(e))
            return
        self.clearCurves()
        for d in new_list:
            color = d.get('color')
            if color:
                color = QColor(color)
            self.addChannel(d['y_channel'], d['x_channel'], name=d.get('name'), color=color, connect_points=d.get('connect_points', True), symbol=d.get('symbol'))
        
    curves = pyqtProperty("QStringList", getCurves, setCurves)
                    
    def channels(self):
        chans = []
        chans.extend([curve.y_channel for curve in self._curves])
        chans.extend([curve.x_channel for curve in self._curves if curve.x_channel is not None])
        return chans
    
    # The methods for autoRangeX, minXRange, maxXRange, autoRangeY, minYRange, and maxYRange are
    # all defined in BasePlot, but we don't expose them as properties there, because not all plot
    # subclasses necessarily want them to be user-configurable in Designer.
    autoRangeX = pyqtProperty(bool, BasePlot.getAutoRangeX, BasePlot.setAutoRangeX, BasePlot.resetAutoRangeX, doc="""
    Whether or not the X-axis automatically rescales to fit the data.  If true, the
    values in minXRange and maxXRange are ignored.
    """)   
    
    minXRange = pyqtProperty(float, BasePlot.getMinXRange, BasePlot.setMinXRange, doc="""
    Minimum X-axis value visible on the plot.
    """)
    
    maxXRange = pyqtProperty(float, BasePlot.getMaxXRange, BasePlot.setMaxXRange, doc="""
    Maximum X-axis value visible on the plot.
    """)
    
    autoRangeY = pyqtProperty(bool, BasePlot.getAutoRangeY, BasePlot.setAutoRangeY, BasePlot.resetAutoRangeY, doc="""
    Whether or not the Y-axis automatically rescales to fit the data.  If true, the
    values in minYRange and maxYRange are ignored.
    """)
    
    minYRange = pyqtProperty(float, BasePlot.getMinYRange, BasePlot.setMinYRange, doc="""
    Minimum Y-axis value visible on the plot.
    """)
    
    maxYRange = pyqtProperty(float, BasePlot.getMaxYRange, BasePlot.setMaxYRange, doc="""
    Maximum Y-axis value visible on the plot.
    """)
