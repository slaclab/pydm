import json
import itertools
from collections import OrderedDict
import numpy as np
from qtpy.QtGui import QColor
from qtpy.QtCore import Slot, Property, Qt
from .baseplot import BasePlot, NoDataError, BasePlotCurveItem
from .channel import PyDMChannel
from ..utilities import remove_protocol

class ScatterPlotCurveItem(BasePlotCurveItem):
    _channels = ('x_channel', 'y_channel')

    def __init__(self, y_addr, x_addr, redraw_mode=None, **kws):
        self.x_channel = None
        self.y_channel = None
        self.x_address = x_addr
        self.y_address = y_addr
        self.x_connected = False
        self.y_connected = False
        # If a name wasn't specified, use the addresses to make one.
        if kws.get('name') is None:
            if y_addr is None and x_addr is None:
                kws['name'] = ""
            else:
                y_name = remove_protocol(y_addr if y_addr is not None else "")
                x_name = remove_protocol(x_addr if x_addr is not None else "")
                kws['name'] = "{y} vs. {x}".format(y=y_name, x=x_name)
        self.redraw_mode = (redraw_mode if redraw_mode is not None
                            else self.REDRAW_ON_EITHER)
        self._bufferSize = 1200
        self.data_buffer = np.zeros((2, self._bufferSize),
                                    order='f', dtype=float)
        self.points_accumulated = 0
        self.latest_x_value = None
        self.latest_y_value = None
        self.needs_new_x = True
        self.needs_new_y = True
        if 'symbol' not in kws.keys():
            kws['symbol'] = 'o'
        if 'lineStyle' not in kws.keys():
            kws['lineStyle'] = Qt.NoPen
        super(ScatterPlotCurveItem, self).__init__(**kws)

    def to_dict(self):
        """
        Returns an OrderedDict representation with values for all properties
        needed to recreate this curve.

        Returns
        -------
        OrderedDict
        """
        dic_ = OrderedDict([("y_channel", self.y_address),
                            ("x_channel", self.x_address)])
        dic_.update(super(ScatterPlotCurveItem, self).to_dict())
        dic_["redraw_mode"] = self.redraw_mode
        dic_['buffer_size'] = self.getBufferSize()
        return dic_

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
        self.x_channel = PyDMChannel(
            address=new_address,
            connection_slot=self.xConnectionStateChanged,
            value_slot=self.receiveXValue)

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
        self.y_channel = PyDMChannel(
            address=new_address,
            connection_slot=self.yConnectionStateChanged,
            value_slot=self.receiveYValue)

    @Slot(bool)
    def xConnectionStateChanged(self, connected):
        self.x_connected = connected

    @Slot(bool)
    def yConnectionStateChanged(self, connected):
        self.y_connected = connected

    @Slot(int)
    @Slot(float)
    def receiveXValue(self, new_x):
        """
        Handler for new x data.
        """
        if new_x is None:
            return
        self.latest_x_value = new_x
        self.needs_new_x = False
        self.update_buffer()

    @Slot(int)
    @Slot(float)
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
        # If we haven't gotten values for X and Y yet, can't redraw.
        if self.latest_y_value is None or self.latest_x_value is None:
            return

        if self.redraw_mode == self.REDRAW_ON_EITHER:
            # no matter which channel updates, add a pair with the two most
            # recent values
            pass
        elif self.redraw_mode == self.REDRAW_ON_X:
            # If we only redraw when X updates, make sure new X data has
            # arrived since the last time we drew the plot.
            if self.needs_new_x:
                return
        elif self.redraw_mode == self.REDRAW_ON_Y:
            # If we only redraw when Y updates, make sure new Y data has
            # arrived since the last time we drew the plot.
            if self.needs_new_y:
                return
        elif self.redraw_mode == self.REDRAW_ON_BOTH:
            # Make sure both X and Y have received new data since the last
            # time we drew the plot.
            if self.needs_new_y or self.needs_new_x:
                return
        # If you get this far, we are OK to add the latest data to the buffer.
        self.data_buffer = np.roll(self.data_buffer, -1)
        self.data_buffer[0, -1] = self.latest_x_value
        self.data_buffer[1, -1] = self.latest_y_value
        if self.points_accumulated < self._bufferSize:
            self.points_accumulated = self.points_accumulated + 1
        self.data_changed.emit()

    def initialize_buffer(self):
        self.points_accumulated = 0
        self.data_buffer = np.zeros((2, self._bufferSize),
                                    order='f', dtype=float)

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
        Called by the curve's parent plot whenever the curve needs to be
        re-drawn with new data.
        """
        self.setData(x=self.data_buffer[0, -self.points_accumulated:].astype(np.float),
                     y=self.data_buffer[1, -self.points_accumulated:].astype(np.float))
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
        return ((float(np.amin(x_data)), float(np.amax(x_data))),
                (float(np.amin(y_data)), float(np.amax(y_data))))

    def channels(self):
        return [self.y_channel, self.x_channel]


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
        init_x_channels can be a string with the address for a channel,
        or a list of strings, each containing an address for a channel.
        If not specified, y-axis waveforms will be plotted against their
        indices.  If a list is specified for both init_x_channels and
        init_y_channels, they both must have the same length.
        If a single x channel was specified, and a list of y channels are
        specified, all y channels will be plotted against the same x channel.
    init_y_channels: optional
        init_y_channels can be a string with the address for a channel,
        or a list of strings, each containing an address for a channel.
        If a list is specified for both init_x_channels and init_y_channels,
        they both must have the same length.
        If a single x channel was specified, and a list of y channels are
        specified, all y channels will be plotted against the same x channel.
    background: optional
        The background color for the plot. Accepts any arguments that
        pyqtgraph.mkColor will accept.
    """
    def __init__(self, parent=None, init_x_channels=[], init_y_channels=[],
                 background='default'):
        super(PyDMScatterPlot, self).__init__(parent, background)
        # If the user supplies a single string instead of a list,
        # wrap it in a list.
        if isinstance(init_x_channels, str):
            init_x_channels = [init_x_channels]
        if isinstance(init_y_channels, str):
            init_y_channels = [init_y_channels]
        if len(init_x_channels) == 0:
            init_x_channels = list(itertools.repeat(None,
                                                    len(init_y_channels)))
        if len(init_x_channels) != len(init_y_channels):
            raise ValueError("If lists are provided for both X and Y " +
                             "channels, they must be the same length.")
        # self.channel_pairs is an ordered dictionary that is keyed on a
        # (x_channel, y_channel) tuple, with ScatterPlotCurveItem values.
        # It gets populated in self.addChannel().
        self.channel_pairs = OrderedDict()
        init_channel_pairs = zip(init_x_channels, init_y_channels)
        for (x_chan, y_chan) in init_channel_pairs:
            self.addChannel(y_channel=y_chan, x_channel=x_chan)
        self._needs_redraw = True

    def initialize_for_designer(self):
        # If we are in Qt Designer, don't update the plot continuously.
        # This function gets called by PyDMTimePlot's designer plugin.
        pass

    def addChannel(self, y_channel=None, x_channel=None, name=None,
                   color=None, lineStyle=None, lineWidth=None,
                   symbol=None, symbolSize=None, redraw_mode=None,
                   buffer_size=None):
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
            ScatterPlotCurveItem.REDRAW_ON_EITHER: (Default)
                Redraw after either X or Y receives new data.
            ScatterPlotCurveItem.REDRAW_ON_X:
                Redraw after X receives new data.
            ScatterPlotCurveItem.REDRAW_ON_Y:
                Redraw after Y receives new data.
            ScatterPlotCurveItem.REDRAW_ON_BOTH:
                Redraw after both X and Y receive new data.
        buffer_size: int, optional
            number of points to keep in the buffer.
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
        if buffer_size is not None:
            curve.setBufferSize(buffer_size)
        self.channel_pairs[(x_channel, y_channel)] = curve
        self.addCurve(curve, curve_color=color)
        curve.data_changed.connect(self.set_needs_redraw)

    def removeChannel(self, curve):
        """
        Remove a curve from the plot.

        Parameters
        ----------
        curve: ScatterPlotCurveItem
            The curve to remove.
        """
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

    @Slot()
    def set_needs_redraw(self):
        self._needs_redraw = True

    @Slot()
    def redrawPlot(self):
        """
        Request a redraw from each curve in the plot.
        Called by curves when they get new data.
        """
        if not self._needs_redraw:
            return
        for curve in self._curves:
            curve.redrawCurve()
        self._needs_redraw = False

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
            self.addChannel(y_channel=d['y_channel'], x_channel=d['x_channel'],
                            name=d.get('name'), color=color,
                            lineStyle=d.get('lineStyle'),
                            lineWidth=d.get('lineWidth'),
                            symbol=d.get('symbol'),
                            symbolSize=d.get('symbolSize'),
                            redraw_mode=d.get('redraw_mode'),
                            buffer_size=d.get('buffer_size'))

    curves = Property("QStringList", getCurves, setCurves)

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

    # The methods for autoRangeX, minXRange, maxXRange, autoRangeY, minYRange,
    # and maxYRange are all defined in BasePlot, but we don't expose them as
    # properties there, because not all plot subclasses necessarily want
    # them to be user-configurable in Designer.
    autoRangeX = Property(bool, BasePlot.getAutoRangeX,
                          BasePlot.setAutoRangeX, BasePlot.resetAutoRangeX,
                          doc="""
Whether or not the X-axis automatically rescales to fit the data.
If true, the values in minXRange and maxXRange are ignored.""")

    minXRange = Property(float, BasePlot.getMinXRange,
                         BasePlot.setMinXRange, doc="""
Minimum X-axis value visible on the plot.""")

    maxXRange = Property(float, BasePlot.getMaxXRange,
                         BasePlot.setMaxXRange, doc="""
Maximum X-axis value visible on the plot.""")

    autoRangeY = Property(bool, BasePlot.getAutoRangeY,
                          BasePlot.setAutoRangeY, BasePlot.resetAutoRangeY,
                          doc="""
Whether or not the Y-axis automatically rescales to fit the data.
If true, the values in minYRange and maxYRange are ignored.""")

    minYRange = Property(float, BasePlot.getMinYRange,
                         BasePlot.setMinYRange, doc="""
Minimum Y-axis value visible on the plot.""")

    maxYRange = Property(float, BasePlot.getMaxYRange,
                         BasePlot.setMaxYRange, doc="""
Maximum Y-axis value visible on the plot.""")
