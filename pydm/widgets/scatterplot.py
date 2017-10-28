from ..PyQt.QtGui import QColor
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, Qt
from pyqtgraph import ViewBox, AxisItem, PlotDataItem, mkPen
import numpy as np
import json
import itertools
from collections import OrderedDict
from .baseplot import BasePlot
from .channel import PyDMChannel
from .. import utilities
from .base import PyDMPrimitiveWidget

class ScatterPlotCurveItem(PlotDataItem):
    REDRAW_ON_X, REDRAW_ON_Y, REDRAW_ON_EITHER, REDRAW_ON_BOTH = range(4)
    symbols = OrderedDict([('None', None),
                           ('Circle', 'o'),
                           ('Square', 's'),
                           ('Triangle', 't'),
                           ('Star', 'star'),
                           ('Pentagon', 'p'),
                           ('Hexagon', 'h'),
                           ('X', 'x'),
                           ('Diamond', 'd'),
                           ('Plus', '+')])
    lines = OrderedDict([('NoLine', Qt.NoPen),
                         ('Solid', Qt.SolidLine),
                         ('Dash', Qt.DashLine),
                         ('Dot', Qt.DotLine),
                         ('DashDot', Qt.DashDotLine),
                         ('DashDotDot', Qt.DashDotDotLine)])
    data_changed = pyqtSignal()
    def __init__(self, y_addr, x_addr, color=None, lineStyle=Qt.NoPen,
                 lineWidth=None, redraw_mode=REDRAW_ON_EITHER, **kws):
        self.x_channel = None
        self.y_channel = None
        self.x_address = x_addr
        self.y_address = y_addr
        self.x_connected = False
        self.y_connected = False
        #If a name wasn't specified, use the addresses to make one.
        if kws.get('name') is None:
            if y_addr is None and x_addr is None:
                kws['name'] = ""
            else:
                y_name = utilities.remove_protocol(y_addr if y_addr is not None else "")
                x_name = utilities.remove_protocol(x_addr if x_addr is not None else "")
                kws['name'] = "{y} vs. {x}".format(y=y_name, x=x_name)
        self.redraw_mode = redraw_mode
        self._bufferSize = 1200
        self.data_buffer = np.zeros((2, self._bufferSize), order='f', dtype=float)
        self.points_accumulated = 0
        self.latest_x_value = None
        self.latest_y_value = None
        self._color = QColor('white')
        self._pen = mkPen(self._color)
        if lineWidth is not None:
            self._pen.setWidth(lineWidth)
        if lineStyle is not None:
            self._pen.setStyle(lineStyle)
        kws['pen'] = self._pen
        super(ScatterPlotCurveItem, self).__init__(**kws)
        self.setSymbolBrush(None)
        self.setSymbol('o')
        if color is not None:
            self.color = color

    def to_dict(self):
        """
        Returns an OrderedDict representation with values for all properties
        needed to recreate this curve.

        Returns
        -------
        OrderedDict
        """
        return OrderedDict([("y_channel", self.y_address),
                            ("x_channel", self.x_address),
                            ("name", self.name()),
                            ("color", self.color_string),
                            ("lineStyle", self.lineStyle),
                            ("lineWidth", self.lineWidth),
                            ("symbol", self.symbol),
                            ("symbolSize", self.symbolSize),
                            ("redraw_mode", self.redraw_mode)])

    @property
    def x_address(self):
        """
        The address of the channel used to get the x axis data.

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
        The address of the channel used to get the x axis data.

        Parameters
        -------
        new_address: str
        """
        if new_address is None or len(str(new_address)) < 1:
            self.x_channel = None
            return
        self.x_channel = PyDMChannel(address=new_address, connection_slot=self.xConnectionStateChanged, value_slot=self.receiveXValue)

    @property
    def y_address(self):
        """
        The address of the channel used to get the y axis data.

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
        The address of the channel used to get the y axis data.

        Parameters
        ----------
        new_address: str
        """
        if new_address is None or len(str(new_address)) < 1:
            self.y_channel = None
            return
        self.y_channel = PyDMChannel(address=new_address, connection_slot=self.yConnectionStateChanged, value_slot=self.receiveYValue)

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
            The new color to use for the curve.
            Strings are passed to ScatterPlotCurveItem.color_string.
        """
        if isinstance(new_color, str):
            self.color_string = new_color
            return
        self._color = new_color
        self._pen.setColor(self._color)
        self.setPen(self._pen)
        self.setSymbolPen(self._color)

    @property
    def symbol(self):
        """
        The single-character code for the symbol drawn at each datapoint.

        See the documentation for pyqtgraph.PlotDataItem for possible values.

        Returns
        -------
        str or None
        """
        return self.opts['symbol']

    @symbol.setter
    def symbol(self, new_symbol):
        """
        The single-character code for the symbol drawn at each datapoint.

        See the documentation for pyqtgraph.PlotDataItem for possible values.

        Parameters
        -------
        new_symbol: str or None
        """
        if new_symbol in self.symbols.values():
            self.setSymbol(new_symbol)
            self.setSymbolPen(self._color)

    @property
    def symbolSize(self):
        """
        Return the size of the symbol to represent the data.

        Returns
        -------
        int
        """
        return self.opts['symbolSize']

    @symbolSize.setter
    def symbolSize(self, new_size):
        """
        Set the size of the symbol to represent the data.

        Parameters
        -------
        new_size: int
        """
        self.setSymbolSize(int(new_size))

    @property
    def lineWidth(self):
        """
        Return the width of the line connecting the data points.

        Returns
        -------
        int
        """
        return self._pen.width()

    @lineWidth.setter
    def lineWidth(self, new_width):
        """
        Set the width of the line connecting the data points.

        Parameters
        -------
        new_width: int
        """
        self._pen.setWidth(int(new_width))
        self.setPen(self._pen)
        
    @property
    def lineStyle(self):
        """
        Return the style of the line connecting the data points.
        Must be a value from the Qt::PenStyle enum (see http://doc.qt.io/qt-5/qt.html#PenStyle-enum).

        Returns
        -------
        int
        """
        return self._pen.style()

    @lineStyle.setter
    def lineStyle(self, new_style):
        """
        Set the style of the line connecting the data points.
        Must be a value from the Qt::PenStyle enum (see http://doc.qt.io/qt-5/qt.html#PenStyle-enum).

        Parameters
        -------
        new_style: int
        """
        if new_style in self.lines.values():
            self._pen.setStyle(new_style)
            self.setPen(self._pen)
    
    @pyqtSlot(bool)
    def xConnectionStateChanged(self, connected):
        self.x_connected = connected

    @pyqtSlot(bool)
    def yConnectionStateChanged(self, connected):
        self.y_connected = connected

    @pyqtSlot(int)
    @pyqtSlot(float)
    def receiveXValue(self, new_x):
        """
        Handler for new x data.
        """
        if new_x is None:
            return
        self.latest_x_value = new_x
        self.needs_new_x = False
        self.update_buffer()

    @pyqtSlot(int)
    @pyqtSlot(float)
    def receiveYValue(self, new_y):
        """
        Handler for new y data.
        """
        if new_y is None:
            return
        self.latest_y_value = new_y
        self.needs_new_y = False
        self.update_buffer()

    def update_buffer(self):
        """
        This is called whenever new data is received for X or Y.
        Based on the value of the redraw_mode attribute, it decides whether
        we are ready to shift the data buffer by one and add the latest data.
        """
        #If we haven't gotten values for X and Y yet, can't redraw.
        if self.latest_y_value is None or self.latest_x_value is None:
            return
    
        if self.redraw_mode == self.REDRAW_ON_EITHER:
            #no matter which channel updates, add a pair with the two most recent values
            pass 
        elif self.redraw_mode == self.REDRAW_ON_X:
            #If we only redraw when X updates, make sure new X data has arrived since the last time we drew the plot.
            if self.needs_new_x:
                return
        elif self.redraw_mode == self.REDRAW_ON_Y:
            #If we only redraw when Y updates, make sure new Y data has arrived since the last time we drew the plot.
            if self.needs_new_y:
                return
        elif self.redraw_mode == self.REDRAW_ON_BOTH:
            #Make sure both X and Y have received new data since the last time we drew the plot.
            if self.needs_new_y or self.needs_new_x:
                return
        #If you get this far, we are OK to add the latest data to the buffer.
        self.data_buffer = np.roll(self.data_buffer, -1)
        self.data_buffer[0, -1] = self.latest_x_value
        self.data_buffer[1, -1] = self.latest_y_value
        if self.points_accumulated < self._bufferSize:
            self.points_accumulated = self.points_accumulated + 1
        self.data_changed.emit()

    def initialize_buffer(self):
        self.points_accumulated = 0
        self.data_buffer = np.zeros((2, self._bufferSize), order='f', dtype=float)

    def getBufferSize(self):
        return int(self._bufferSize)

    def setBufferSize(self, value):
        if self._bufferSize != int(value):
            self._bufferSize = max(int(value), 1)
            self.initialize_buffer()

    def resetBufferSize(self):
        if self._bufferSize != 1200:
            self._bufferSize = 1200
            self.initialize_buffer()

    def redrawCurve(self):
        """
        redrawCurve is called by the curve's parent plot whenever the curve needs to be
        re-drawn with new data.
        """
        self.setData(x=self.data_buffer[1, -self.points_accumulated:], y=self.data_buffer[0, -self.points_accumulated:])
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
        if self.points_accumulated == 0:
            raise NoDataError("Curve has no data, cannot determine limits.")
        x_data = self.data_buffer[0, -self.points_accumulated:]
        y_data = self.data_buffer[1, -self.points_accumulated:]
        return ((np.amin(x_data), np.amax(x_data)), (np.amin(y_data), np.amax(y_data)))
        
class PyDMScatterPlot(BasePlot):
    """
    PyDMScatterPlot is a widget to plot one scalar value against another.
    Multiple scalar pairs can be plotted on the same plot.  Each pair has
    a buffer which stores previous values.  All values in the buffer are
    drawn.  The buffer size for each pair is user configurable.

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
        super(PyDMScatterPlot, self).__init__(parent, background)
        #If the user supplies a single string instead of a list, wrap it in a list.
        if isinstance(init_x_channels, str):
            init_x_channels = [init_x_channels]
        if isinstance(init_y_channels, str):
            init_y_channels = [init_y_channels]
        if len(init_x_channels) == 0:
            init_x_channels = list(itertools.repeat(None, len(init_y_channels)))
        if len(init_x_channels) != len(init_y_channels):
            raise ValueError("If lists are provided for both X and Y channels, they must be the same length.")
        #self.channel_pairs is an ordered dictionary that is keyed on a (x_channel, y_channel) tuple, with ScatterPlotCurveItem values.
        #It gets populated in self.addChannel().
        self.channel_pairs = OrderedDict()
        init_channel_pairs = zip(init_x_channels, init_y_channels)
        for (x_chan, y_chan) in init_channel_pairs:
            self.addChannel(y_chan, x_channel=x_chan)

    def addChannel(self, y_channel=None, x_channel=None, name=None,
                   color=None, lineStyle=None, lineWidth=None,
                   symbol=None, symbolSize=None, redraw_mode=None):
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
        lineStyle: int, optional
            Style of the line connecting the data points.
            0 means no line (scatter plot).
        lineWidth: int, optional
            Width of the line connecting the data points.
        redraw_mode: int, optional
            Must be one four values:
            ScatterPlotCurveItem.REDRAW_ON_EITHER: (Default) The curve will be redrawn after either X or Y receives new data.
            ScatterPlotCurveItem.REDRAW_ON_X: The curve will only be redrawn after X receives new data.
            ScatterPlotCurveItem.REDRAW_ON_Y: The curve will only be redrawn after Y receives new data.
            ScatterPlotCurveItem.REDRAW_ON_BOTH: The curve will only be redrawn after both X and Y receive new data.
        symbol: str or None, optional
            Which symbol to use to represent the data.
        symbol: int, optional
            Size of the symbol.
        """
        plot_opts = {}
        plot_opts['symbol'] = symbol
        if symbolSize is not None:
            plot_opts['symbolSize'] = symbolSize
        if lineStyle is not None:
            plot_opts['lineStyle'] = lineStyle
        if lineWidth is not None:
            plot_opts['lineWidth'] = lineWidth
        if redraw_mode is not None:
            plot_opts['redraw_mode'] = redraw_mode
        curve = ScatterPlotCurveItem(y_addr=y_channel,
                                  x_addr=x_channel,
                                  name=name,
                                  color=color,
                                  **plot_opts)
        curve.data_changed.connect(self.redrawPlot)
        self.channel_pairs[(y_channel, x_channel)] = curve
        self.addCurve(curve, curve_color=color)

    def removeChannel(self, curve):
        """
        Remove a curve from the plot.

        Parameters
        ----------
        curve: ScatterPlotCurveItem
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
        super(PyDMScatterPlot, self).clear()

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
            self.addChannel(d['y_channel'], d['x_channel'],
                            name=d.get('name'), color=color,
                            lineStyle=d.get('lineStyle'),
                            lineWidth=d.get('lineWidth'),
                            symbol=d.get('symbol'),
                            symbolSize=d.get('symbolSize'),
                            redraw_mode=d.get('redraw_mode'))

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
        chans.extend([curve.x_channel for curve in self._curves])
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
