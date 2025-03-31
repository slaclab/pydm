import json
import itertools
from collections import OrderedDict
import numpy as np
from qtpy.QtGui import QColor
from qtpy.QtCore import Slot, Property, Qt
from .baseplot import BasePlot, NoDataError, BasePlotCurveItem
from .channel import PyDMChannel


DEFAULT_BUFFER_SIZE = 1200
MINIMUM_BUFFER_SIZE = 2


class EventPlotCurveItem(BasePlotCurveItem):
    _channels = "channel"

    def __init__(self, addr, y_idx, x_idx, bufferSizeChannelAddress=None, **kws):
        self.channel = None
        self.address = addr
        self.x_idx = x_idx
        self.y_idx = y_idx
        self.connected = False
        if kws.get("name") is None:
            kws["name"] = ""
        self.bufferSizeChannel = None
        self.bufferSizeChannel_connected = False
        self._bufferSize = DEFAULT_BUFFER_SIZE
        self.data_buffer = np.zeros((2, self._bufferSize), order="f", dtype=float)
        self.points_accumulated = 0
        if "symbol" not in kws.keys():
            kws["symbol"] = "o"
        if "lineStyle" not in kws.keys():
            kws["lineStyle"] = Qt.NoPen
        super().__init__(**kws)
        self.bufferSizeChannelAddress = bufferSizeChannelAddress

    def to_dict(self):
        """
        Serialize this curve into a dictionary.

        Returns
        -------
        OrderedDict
            Representation with values for all properties
            needed to recreate this curve.
        """
        dic_ = OrderedDict([("channel", self.address), ("y_idx", self.y_idx), ("x_idx", self.x_idx)])
        dic_.update(super().to_dict())
        dic_["buffer_size"] = self.getBufferSize()
        dic_["bufferSizeChannelAddress"] = self.bufferSizeChannelAddress
        return dic_

    @property
    def address(self):
        """
        The address of the channel used to get the data.

        Returns
        -------
        str
            The address of the channel used to get the x axis data.
        """
        if self.channel is None:
            return None
        return self.channel.address

    @address.setter
    def address(self, new_address):
        """
        The address of the channel used to get the x axis data.

        Parameters
        -------
        new_address: str
        """
        if new_address is None or len(str(new_address)) < 1:
            self.channel = None
            return
        self.channel = PyDMChannel(
            address=new_address, connection_slot=self.connectionStateChanged, value_slot=self.receiveValue
        )

    @Slot(bool)
    def connectionStateChanged(self, connected):
        self.connected = connected

    @Slot(np.ndarray)
    def receiveValue(self, new_data):
        """
        Handler for new data.  This method is usually called by a PyDMChannel
        when it updates.  You can call this yourself to inject data into the curve.

        Parameters
        ----------
        new_data: numpy.ndarray
            A new array of values.
        """
        if new_data is None:
            return
        if self.x_idx is None or self.y_idx is None:
            return
        if not isinstance(self.x_idx, int) or not isinstance(self.y_idx, int):
            """The x_idx and y_idx typing is made this late so that macros can
            can be used alongside regular indexing."""
            self.x_idx = int(self.x_idx)
            self.y_idx = int(self.y_idx)
        if len(new_data) <= self.x_idx or len(new_data) <= self.y_idx:
            return
        self.data_buffer = np.roll(self.data_buffer, -1)
        self.data_buffer[0, -1] = new_data[self.x_idx]
        self.data_buffer[1, -1] = new_data[self.y_idx]
        if self.points_accumulated < self._bufferSize:
            self.points_accumulated = self.points_accumulated + 1
        self.data_changed.emit()

    def initialize_buffer(self):
        self.points_accumulated = 0
        self.data_buffer = np.zeros((2, self._bufferSize), order="f", dtype=float)

    def getBufferSize(self):
        return int(self._bufferSize)

    def setBufferSize(self, value):
        if self._bufferSize != int(value):
            self._bufferSize = max(int(value), MINIMUM_BUFFER_SIZE)
            self.initialize_buffer()

    def resetBufferSize(self):
        if self._bufferSize != DEFAULT_BUFFER_SIZE:
            self._bufferSize = DEFAULT_BUFFER_SIZE
            self.initialize_buffer()

    @property
    def bufferSizeChannelAddress(self):
        """
        The address of the channel used to get the buffer size.

        Returns
        -------
        str
            The address of the channel used to get the buffer size.
        """
        if self.bufferSizeChannel is None:
            return None
        return self.bufferSizeChannel.address

    @bufferSizeChannelAddress.setter
    def bufferSizeChannelAddress(self, new_address):
        """
        The address of the channel used to get the buffer size.

        Parameters
        ----------
        new_address: str
        """
        if new_address is None or len(str(new_address)) < 1:
            self.bufferSizeChannel = None
            return
        if self.bufferSizeChannel is not None and self.bufferSizeChannel.address == new_address:
            return
        self.bufferSizeChannel = PyDMChannel(
            address=new_address,
            connection_slot=self.bufferSizeConnectionStateChanged,
            value_slot=self.bufferSizeChannelValueReceiver,
        )
        self.bufferSizeChannel.connect()

    @Slot(bool)
    def bufferSizeConnectionStateChanged(self, connected):
        self.bufferSizeChannel_connected = connected

    @Slot(int)
    def bufferSizeChannelValueReceiver(self, value):
        """
        Handler for change in buffer size.  This method is usually called by a PyDMChannel
        when it updates.  You can call this yourself to set or change the buffer size.

        Parameters
        ----------
        value: int
            A new value for the buffer size.
        """
        if value is None:
            return
        self.setBufferSize(value)
        self.update_buffer()

    def redrawCurve(self):
        """
        Called by the curve's parent plot whenever the curve needs to be
        re-drawn with new data.
        """
        self.setData(
            x=self.data_buffer[0, -self.points_accumulated :].astype(float),
            y=self.data_buffer[1, -self.points_accumulated :].astype(float),
        )

    def limits(self):
        """
        Get the limits of the data for this curve.

        Returns
        -------
        tuple
            A nested tuple of limits: ((xmin, xmax), (ymin, ymax))
        """
        if self.points_accumulated == 0:
            raise NoDataError("Curve has no data, cannot determine limits.")
        x_data = self.data_buffer[0, -self.points_accumulated :]
        y_data = self.data_buffer[1, -self.points_accumulated :]
        return ((float(np.amin(x_data)), float(np.amax(x_data))), (float(np.amin(y_data)), float(np.amax(y_data))))

    def channels(self):
        return [self.channel]


class PyDMEventPlot(BasePlot):
    """
    PyDMEventPlot is a widget to plot one scalar value against another.
    All of the values arrive in a single event-built array, and indices are
    used to identify which values to plot.  Multiple scalar pairs can be
    plotted on the same plot.  Each pair has a buffer which stores previous
    values.  All values in the buffer are drawn.  The buffer size for each
    pair is user configurable.

    Parameters
    ----------
    parent : optional
        The parent of this widget.
    channel : optional
        A string with the address for a channel.  This channel should produce
        an array of data for each event.  The index parameters are used to
        select data from this array to be plotted.
    init_x_indices: optional
        init_x_indices can be None, an integer, or a list of integers possibly
        containing None.  These indices are used to select values from the
        data array provided by channel to be plotted.  In the event that
        an index is None, the curve will be created, but no plotting will
        occur until an integer index is set.  If lists are specified for
        both init_x_indices and init_y_indices, they both must have the same
        length. If a single x index was specified, and a list of y indices is
        specified, all of the selected y data will be plotted against the same x.
    init_y_indices: optional
        init_y_indices can be None, an integer, or a list of integers possibly
        containing None.  These indices are used to select values from the
        data array provided by channel to be plotted.  In the event that
        an index is None, the curve will be created, but no plotting will
        occur until an integer index is set.  If lists are specified for
        both init_x_indices and init_y_indices, they both must have the same
        length. If a single x index was specified, and a list of y indices is
        specified, all of the selected y data will be plotted against the same x.
    background: optional
        The background color for the plot. Accepts any arguments that
        pyqtgraph.mkColor will accept.
    """

    def __init__(self, parent=None, channel=None, init_x_indices=[], init_y_indices=[], background="default"):
        super().__init__(parent, background)
        # If the user supplies a single integer instead of a list,
        # wrap it in a list.
        if isinstance(init_x_indices, int):
            init_x_indices = [init_x_indices]
        if isinstance(init_y_indices, int):
            init_y_indices = [init_y_indices]
        if init_y_indices is None:
            init_y_indices = []
        if init_x_indices is None or len(init_x_indices) == 0:
            init_x_indices = list(itertools.repeat(None, len(init_y_indices)))
        if len(init_x_indices) == 1:
            init_x_indices = init_x_indices * len(init_y_indices)
        if len(init_x_indices) != len(init_y_indices):
            raise ValueError("If lists are provided for both X and Y " + "indices, they must be the same length.")
        # self.index_pairs is an ordered dictionary that is keyed on a
        # (x_idx, y_idx) tuple, with EventPlotCurveItem values.
        # It gets populated in self.addChannel().
        self.index_pairs = OrderedDict()
        init_index_pairs = zip(init_x_indices, init_y_indices)
        for x_idx, y_idx in init_index_pairs:
            self.addChannel(channel=channel, y_idx=y_idx, x_idx=x_idx)
        self._needs_redraw = True

    def initialize_for_designer(self):
        # If we are in Qt Designer, don't update the plot continuously.
        # This function gets called by PyDMTimePlot's designer plugin.
        pass

    def updateLabel(self, x_val: float, y_val: float) -> None:
        # Do nothing — disabling labels for this class. method would need to be implemented if labels are desired.
        pass

    def addChannel(
        self,
        channel=None,
        y_idx=None,
        x_idx=None,
        name=None,
        color=None,
        lineStyle=None,
        lineWidth=None,
        symbol="o",
        symbolSize=5,
        buffer_size=None,
        yAxisName=None,
        bufferSizeChannelAddress=None,
    ):
        """
        Add a new curve to the plot.  In addition to the arguments below,
        all other keyword arguments are passed to the underlying
        pyqtgraph.PlotDataItem used to draw the curve.

        Parameters
        ----------
        channel: str
            The channel for the curve data.
        y_idx: int
            The index for the y data for the curve.
        x_idx: int, optional
            The index for the x data for the curve.
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
        buffer_size: int, optional
            number of points to keep in the buffer.
        bufferSizeChannelAddress : str, optional
            The name of a channel that defines the buffer size (int).
        symbol: str or None, optional
            Which symbol to use to represent the data.
        symbol: int, optional
            Size of the symbol.
        yAxisName : str, optional
            The name of the y axis to associate with this curve. Will be created if it
            doesn't yet exist
        """
        plot_opts = {}
        plot_opts["symbol"] = symbol
        if symbolSize is not None:
            plot_opts["symbolSize"] = symbolSize
        if lineStyle is not None:
            plot_opts["lineStyle"] = lineStyle
        if lineWidth is not None:
            plot_opts["lineWidth"] = lineWidth
        curve = self.createCurveItem(
            addr=channel,
            y_idx=y_idx,
            x_idx=x_idx,
            name=name,
            color=color,
            yAxisName=yAxisName,
            bufferSizeChannelAddress=bufferSizeChannelAddress,
            **plot_opts,
        )
        if buffer_size is not None:
            curve.setBufferSize(buffer_size)
        self.index_pairs[(x_idx, y_idx)] = curve
        self.addCurve(curve, curve_color=color, y_axis_name=yAxisName)
        curve.data_changed.connect(self.set_needs_redraw)

    def createCurveItem(self, *args, **kwargs):
        return EventPlotCurveItem(*args, **kwargs)

    def removeChannel(self, curve):
        """
        Remove a curve from the plot.

        Parameters
        ----------
        curve: EventPlotCurveItem
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
        super().clear()

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
            color = d.get("color")
            if color:
                color = QColor(color)
            self.addChannel(
                channel=d["channel"],
                y_idx=d["y_idx"],
                x_idx=d["x_idx"],
                name=d.get("name"),
                color=color,
                lineStyle=d.get("lineStyle"),
                lineWidth=d.get("lineWidth"),
                symbol=d.get("symbol"),
                symbolSize=d.get("symbolSize"),
                buffer_size=d.get("buffer_size"),
                bufferSizeChannelAddress=d.get("bufferSizeChannelAddress"),
                yAxisName=d.get("yAxisName"),
            )

    curves = Property("QStringList", getCurves, setCurves, designable=False)

    def channels(self):
        """
        Returns the list of channels used by all curves in the plot.

        Returns
        -------
        list
        """
        chans = []
        chans.extend([curve.channel for curve in self._curves])
        chans.extend([curve.bufferSizeChannel for curve in self._curves if curve.bufferSizeChannel is not None])
        return chans

    # The methods for autoRangeX, minXRange, maxXRange, autoRangeY, minYRange,
    # and maxYRange are all defined in BasePlot, but we don't expose them as
    # properties there, because not all plot subclasses necessarily want
    # them to be user-configurable in Designer.
    autoRangeX = Property(
        bool,
        BasePlot.getAutoRangeX,
        BasePlot.setAutoRangeX,
        BasePlot.resetAutoRangeX,
        doc="""
Whether or not the X-axis automatically rescales to fit the data.
If true, the values in minXRange and maxXRange are ignored.""",
    )

    minXRange = Property(
        float,
        BasePlot.getMinXRange,
        BasePlot.setMinXRange,
        doc="""
Minimum X-axis value visible on the plot.""",
    )

    maxXRange = Property(
        float,
        BasePlot.getMaxXRange,
        BasePlot.setMaxXRange,
        doc="""
Maximum X-axis value visible on the plot.""",
    )

    autoRangeY = Property(
        bool,
        BasePlot.getAutoRangeY,
        BasePlot.setAutoRangeY,
        BasePlot.resetAutoRangeY,
        doc="""
Whether or not the Y-axis automatically rescales to fit the data.
If true, the values in minYRange and maxYRange are ignored.""",
    )

    minYRange = Property(
        float,
        BasePlot.getMinYRange,
        BasePlot.setMinYRange,
        doc="""
Minimum Y-axis value visible on the plot.""",
    )

    maxYRange = Property(
        float,
        BasePlot.getMaxYRange,
        BasePlot.setMaxYRange,
        doc="""
Maximum Y-axis value visible on the plot.""",
    )
