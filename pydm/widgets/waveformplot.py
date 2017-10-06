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
    """NoDataError is raised when a curve tries to perform an operation, but does not
    yet have any data."""
    pass

class WaveformCurveItem(PlotDataItem):
    """
    WaveformCurveItem represents a single curve in a waveform plot.  It can be used
    to plot one waveform vs. its indices, or one waveform vs. another.  In addition
    to the parameters listed below, WaveformCurveItem accepts keyword arguments for
    all plot options that pyqtgraph.PlotDataItem accepts.

    Parameters
    ----------
    y_addr : str, optional
        The address to waveform data for the Y axis.  Curves must have Y data to plot.
    x_addr : str, optional
        The address to waveform data for the X axis.  If None, the curve will plot Y data vs. the Y index.
    color : QColor, optional
        The color used to draw the curve line.  If connect_points is False, this is not used.
    connect_points: bool, optional
        Whether or not to draw a line to connect the data points.
    """
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
        """
        A string representation of the color used for the curve.  This string
        will be a hex color code, like #FF00FF, or an SVG spec color name, if
        a name exists for the color.

        Returns
        -------
        str
        """
        return str(utilities.colors.svg_color_from_hex(self.color.name(), hex_on_fail=True))
    
    @color_string.setter
    def color_string(self, new_color_string):
        """
        A string representation of the color used for the curve.  This string
        will be a hex color code, like #FF00FF, or an SVG spec color name, if
        a name exists for the color.

        Parameters
        -------
        new_color_string: int
            The new string to use for the curve color.
        """
        self.color = QColor(str(new_color_string))
            
    @property
    def color(self):
        """
        The color used for the curve.

        Returns
        -------
        QColor
        """
        return self._color
    
    @color.setter
    def color(self, new_color):
        """
        The color used for the curve.

        Parameters
        -------
        new_color: QColor or str
            The new color to use for the curve.  Strings are passed to WaveformCurveItem.color_string.
        """
        if isinstance(new_color, str):
            self.color_string = new_color
            return
        self._color = new_color
        if self.connect_points:
            self.setPen(self._color)
    
    @property
    def connect_points(self):
        """
        Whether or not the data points are connected with a line.

        Returns
        -------
        bool
        """
        return self._connect_points
    
    @connect_points.setter
    def connect_points(self, connect):
        """
        Whether or not the data points are connected with a line.

        Parameters
        -------
        connect: bool
        """
        self._connect_points = connect
        if self._connect_points:
            self.setPen(self._color)
        else:
            self.setPen(None)
    
    @property
    def symbol(self):
        """
        The single-character code for the symbol drawn at each datapoint.
        See the documentation for pyqtgraph.PlotDataItem for possible values.
        
        Returns
        -------
        str
        """
        return self.opts['symbol']
    
    @symbol.setter
    def symbol(self, new_symbol):
        """
        The single-character code for the symbol drawn at each datapoint.
        See the documentation for pyqtgraph.PlotDataItem for possible values.
        
        Parameters
        -------
        new_symbol: str
        """
        if new_symbol in self.symbols.values():
            self.setSymbol(new_symbol)
        else:
            self.setSymbol(None)
    
    @property
    def x_address(self):
        """
        The address of the channel used to get the x axis waveform data.
        
        Returns
        -------
        str
        """
        if self.x_channel is None:
            return None
        return self.x_channel.address
    
    @x_address.setter
    def x_address(self, new_address):
        """
        The address of the channel used to get the x axis waveform data.
        
        Parameters
        -------
        new_address: str
        """
        if new_address is None or len(str(new_address)) < 1:
            self.x_channel = None
            return
        self.x_channel = PyDMChannel(address=new_address, connection_slot=self.xConnectionStateChanged, value_slot=self.receiveXWaveform)
    
    @property
    def y_address(self):
        """
        The address of the channel used to get the y axis waveform data.
        
        Returns
        -------
        str
        """
        if self.y_channel is None:
            return None
        return self.y_channel.address
    
    @y_address.setter
    def y_address(self, new_address):
        """
        The address of the channel used to get the x axis wavefor data.
        
        Parameters
        -------
        new_address: str
        """
        if new_address is None or len(str(new_address)) < 1:
            self.y_channel = None
            return
        self.y_channel = PyDMChannel(address=new_address, connection_slot=self.yConnectionStateChanged, value_slot=self.receiveYWaveform)
    
    def to_dict(self):
        """
        Returns an OrderedDict representation with values for all properties 
        needed to recreate this curve.
        
        Returns
        -------
        OrderedDict
        """
        return OrderedDict([("y_channel", self.y_address), ("x_channel", self.x_address), ("name", self.name()), ("color", self.color_string), ("connect_points", self.connect_points), ("symbol", self.symbol)])
    
    @pyqtSlot(bool)
    def xConnectionStateChanged(self, connected):
        pass
        
    @pyqtSlot(bool)
    def yConnectionStateChanged(self, connected):
        pass
    
    @pyqtSlot(np.ndarray)
    def receiveXWaveform(self, new_waveform):
        """
        Handler for new x waveform data.
        """
        self.x_waveform = new_waveform
        self.needs_new_x = False
        #Don't redraw unless we already have Y data.
        if not (self.needs_new_x or self.needs_new_y):
            self.data_changed.emit()
    
    @pyqtSlot(np.ndarray)
    def receiveYWaveform(self, new_waveform):
        """
        Handler for new y waveform data.
        """
        self.y_waveform = new_waveform
        self.needs_new_y = False
        if self.x_channel is None or self.x_waveform is not None:
            self.data_changed.emit()
    
    def redrawCurve(self):
        """
        redrawCurve is called by the curve's parent plot whenever the curve needs to be
        re-drawn with new data.
        """
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
        self.needs_new_x = True
        self.needs_new_y = True
    
    def limits(self):
        """
        Limits of the data for this curve.
        Returns a nested tuple of limits: ((xmin, xmax), (ymin, ymax))
        
        Returns
        -------
        tuple
        """
        if self.y_waveform is None:
            raise NoDataError("Curve has no Y data, cannot determine limits.")
        if self.x_waveform is None:
            yspan = float(np.amax(self.y_waveform)) - float(np.amin(self.y_waveform))
            return ((0, len(self.y_waveform)), (float(np.amin(self.y_waveform) - yspan), float(np.amax(self.y_waveform) + yspan)))
        else:
            return ((np.amin(self.x_waveform), np.amax(self.x_waveform)), (np.amin(self.y_waveform), np.amax(self.y_waveform)))
    
class PyDMWaveformPlot(BasePlot):
    """
    PyDMWaveformPlot is a widget to plot one or more waveforms.  Each curve can plot
    either a Y-axis waveform vs. its indices, or a Y-axis waveform against an X-axis
    waveform.

    Parameters
    ----------
    parent : optional
        The parent of this widget.
    init_x_channels: optional
        init_x_channels can be a string with the address for a channel, or a list of
        strings, each containing an address for a channel.  If not specified, y-axis
        waveforms will be plotted against their indices.  If a list is specified for
        both init_x_channels and init_y_channels, they both must have the same length.
        If a single x channel was specified, and a list of y channels are specified, all
        y channels will be plotted against the same x channel.
    init_y_channels: optional
        init_y_channels can be a string with the address for a channel, or a list of
        strings, each containing an address for a channel.  If a list is specified for
        both init_x_channels and init_y_channels, they both must have the same length.
        If a single x channel was specified, and a list of y channels are specified, all
        y channels will be plotted against the same x channel.
    background: optional
        The background color for the plot.  Accepts any arguments that pyqtgraph.mkColor
        will accept.
    """
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
        """
        Add a new curve to the plot.  In addition to the arguments below,
        all other keyword arguments are passed to the underlying 
        pyqtgraph.PlotDataItem used to draw the curve.
        
        Parameters
        ----------
        y_channel: str
            The address for the y channel for the curve.
        x_channel: str, optional
            The address for the x channel for the curve.
        name: str, optional
            A name for this curve.  The name will be used in the plot legend.
        color: str or QColor, optional
            A color for the line of the curve.  If not specified, the plot will
            automatically assign a unique color from a set of default colors.
        connect_points: bool, optional
            Whether or not to connect the datapoints with a line.  If you want
            to make a scatter plot, set this to False.  Defaults to True.
        """
        plot_opts = {}
        if symbol is not None:
            plot_opts['symbol'] = symbol
        curve = WaveformCurveItem(y_addr=y_channel, x_addr=x_channel, name=name, color=color, connect_points=connect_points, **plot_opts)
        curve.data_changed.connect(self.redrawPlot)
        self.channel_pairs[(y_channel, x_channel)] = curve
        self.addCurve(curve, curve_color=color)
    
    def removeChannel(self, curve):
        """
        Remove a curve from the plot.
        
        Parameters
        ----------
        curve: WaveformCurveItem
            The curve to remove.
        """
        curve.data_changed.disconnect(self.redrawPlot)
        self.removeCurve(curve)
    
    def removeChannelAtIndex(self, index):
        """
        Remove a curve from the plot, given an index
        for a curve.
        
        Parameters
        ----------
        index: int
            Index for the curve to remove.
        """
        curve = self._curves[index]
        self.removeChannel(curve)
        
    def updateAxes(self):
        """
        Update the X and Y axes for the plot to fit all data in
        all curves for the plot.
        """
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
        """
        Request a redraw from each curve in the plot.
        Called by curves when they get new data.
        """
        self.updateAxes()
        for curve in self._curves:
            curve.redrawCurve()
    
    def clearCurves(self):
        """
        Remove all curves from the plot.
        """
        super(PyDMWaveformPlot, self).clear()
    
    def getCurves(self):
        """
        Get a list of json representations for each curve.
        """
        return [json.dumps(curve.to_dict()) for curve in self._curves]
     
    def setCurves(self, new_list):
        """
        Replace all existing curves with new ones.  This function
        is mostly used as a way to load curves from a .ui file, and
        almost all users will want to add curves through addChannel,
        not this method.
        
        Parameters
        ----------
        new_list: list
            A list of json strings representing each curve in the plot.
        """
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
        """
        Returns the list of channels used by all curves in the plot.
        
        Returns
        -------
        list
        """
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
