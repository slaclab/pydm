import time
import json
from collections import OrderedDict
from pyqtgraph import ViewBox, AxisItem
import numpy as np
from qtpy.QtGui import QColor
from qtpy.QtCore import Signal, Slot, Property, QTimer
from qtpy.QtWidgets import QAction
from .baseplot import BasePlot, BasePlotCurveItem
from .channel import PyDMChannel
from .. utilities import remove_protocol

import logging
logger = logging.getLogger(__name__)

MINIMUM_BUFFER_SIZE = 2
DEFAULT_BUFFER_SIZE = 18000

DEFAULT_X_MIN = -30
DEFAULT_Y_MIN = 0

DEFAULT_TIME_SPAN = 5.0
DEFAULT_UPDATE_INTERVAL = 100


class TimePlotCurveItem(BasePlotCurveItem):
    """
    TimePlotCurveItem represents a single curve in a time plot.

    It is used to plot a scalar value vs. time.  In addition to the parameters
    listed below, TimePlotCurveItem accepts keyword arguments for all plot
    options that pyqtgraph.PlotDataItem accepts.

    Parameters
    ----------
    channel_address : str
        The address to of the scalar data to plot.
    plot_by_timestamps : bool
        If True, the x-axis shows timestamps as ticks, and those timestamps
        scroll to the left as time progresses.  If False, the x-axis tick marks
        show time relative to the current time.
    color : QColor, optional
        The color used to draw the curve line and the symbols.
    lineStyle: int, optional
        Style of the line connecting the data points.
        Must be a value from the Qt::PenStyle enum
        (see http://doc.qt.io/qt-5/qt.html#PenStyle-enum).
    lineWidth: int, optional
        Width of the line connecting the data points.
    **kws : dict
        Additional parameters supported by pyqtgraph.PlotDataItem,
        like 'symbol' and 'symbolSize'.
    """
    _channels = ('channel',)

    def __init__(self, channel_address=None, plot_by_timestamps=True, **kws):
        """
        Parameters
        ----------
        channel_address : str
            The PV address
        plot_by_timestamps : bool
            If True, the x-axis shows timestamps as ticks, and those timestamps
            scroll to the left as time progresses.  If False, the x-axis tick
            marks show time relative to the current time.
        kws : dict
            Additional parameters supported by pyqtgraph.PlotDataItem,
            like 'symbol' and 'symbolSize'.
        """
        channel_address = "" if channel_address is None else channel_address
        if "name" not in kws or not kws["name"]:
            name = remove_protocol(channel_address)
            kws["name"] = name

        # Keep the x-axis moving with latest timestamps as ticks
        self._plot_by_timestamps = plot_by_timestamps

        self._bufferSize = MINIMUM_BUFFER_SIZE
        self._update_mode = PyDMTimePlot.SynchronousMode

        self._min_y_value = None
        self._max_y_value = None

        self.data_buffer = np.zeros((2, self._bufferSize), order='f', dtype=float)
        self.connected = False
        self.points_accumulated = 0
        self.latest_value = None
        self.channel = None
        self.address = channel_address
        super(TimePlotCurveItem, self).__init__(**kws)

    def to_dict(self):
        dic_ = OrderedDict([("channel", self.address), ])
        dic_.update(super(TimePlotCurveItem, self).to_dict())
        return dic_

    @property
    def address(self):
        if self.channel is None:
            return None
        return self.channel.address

    @address.setter
    def address(self, new_address):
        if new_address is None or len(str(new_address)) < 1:
            self.channel = None
            return
        self.channel = PyDMChannel(address=new_address,
                                   connection_slot=self.connectionStateChanged,
                                   value_slot=self.receiveNewValue)

    @property
    def plotByTimeStamps(self):
        return self._plot_by_timestamps

    @plotByTimeStamps.setter
    def plotByTimeStamps(self, new_value):
        if self._plot_by_timestamps != new_value:
            self._plot_by_timestamps = new_value

    @property
    def minY(self):
        """
        Get the minimum y-value so far in the same plot. This is useful to
        scale the y-axis for a selected curve.

        Returns : float
        -------
        The minimum y-value collected so far for this current curve.
        """
        return self._min_y_value

    @property
    def maxY(self):
        """
        Get the maximum y-value so far in the same plot. This is useful to
        scale the y-axis for a selected curve.

        Returns
        -------
        float
            The maximum y-value collected so far for this current curve.
        """
        return self._max_y_value

    @Slot(bool)
    def connectionStateChanged(self, connected):
        # Maybe change pen stroke?
        self.connected = connected
        if not self.connected:
            self.latest_value = np.nan

    @Slot(float)
    @Slot(int)
    def receiveNewValue(self, new_value):
        """
        Rotate and fill the data buffer when a new value is available.

        For Synchronous mode, write the new value into the data buffer
        immediately, and increment the accumulated point counter.
        For Asynchronous, write the new value into a temporary (buffered)
        variable, which will be written to the data buffer when asyncUpdate
        is called.

        Parameters
        ----------
        new_value : float
            The new y-value just available.
        """
        self.update_min_max_y_values(new_value)

        if self._update_mode == PyDMTimePlot.SynchronousMode:
            self.data_buffer = np.roll(self.data_buffer, -1)
            #The first array row is to record timestamps, when a new value arrives.
            self.data_buffer[0, self._bufferSize - 1] = time.time()
            #The second array row is to record the actual values.
            self.data_buffer[1, self._bufferSize - 1] = new_value

            if self.points_accumulated < self._bufferSize:
                self.points_accumulated += 1
            self.data_changed.emit()
        elif self._update_mode == PyDMTimePlot.AsynchronousMode:
            self.latest_value = new_value

    @Slot()
    def asyncUpdate(self):
        """
        Updates the latest data read from the buffered variable into the data
        buffer, together with the timestamp when this happens. Also increments
        the accumulated point counter.
        """
        if self._update_mode != PyDMTimePlot.AsynchronousMode:
            return
        self.data_buffer = np.roll(self.data_buffer, -1)
        self.data_buffer[0, self._bufferSize - 1] = time.time()
        self.data_buffer[1, self._bufferSize - 1] = self.latest_value
        if self.points_accumulated < self._bufferSize:
            self.points_accumulated = self.points_accumulated + 1
        self.data_changed.emit()

    def update_min_max_y_values(self, new_value):
        """
        Updte the min and max y-value as a new value is available. This is
        useful for auto-scaling to a specific curve.

        Parameters
        ----------
        new_value : float
            The new y-value just available.
        """
        if self._min_y_value is None and self._max_y_value is None:
            self._min_y_value = self._max_y_value = new_value
        elif self._min_y_value > new_value:
            self._min_y_value = new_value
        elif self._max_y_value < new_value:
            self._max_y_value = new_value

    def initialize_buffer(self):
        """
        Initialize the data buffer used to plot the current curve.
        """
        self.points_accumulated = 0

        # If you don't specify dtype=float, you don't have enough
        # resolution for the timestamp data.
        self.data_buffer = np.zeros((2, self._bufferSize),
                                    order='f', dtype=float)
        self.data_buffer[0].fill(time.time())

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

    @Slot()
    def redrawCurve(self):
        """
        Redraw the curve with the new data.

        If plot by timestamps, plot the x-axis with the timestamps as the ticks.

        On the other hand, if plot by relative time, take the time diff from
        the starting time of the curve, and plot the data to the time diff
        position on the x-axis.
        """
        try:
            x = self.data_buffer[0, -self.points_accumulated:].astype(np.float)
            y = self.data_buffer[1, -self.points_accumulated:].astype(np.float)

            if not self._plot_by_timestamps:
                x -= time.time()

            self.setData(y=y, x=x)
        except (ZeroDivisionError, OverflowError):
            # Solve an issue with pyqtgraph and initial downsampling
            pass

    def setUpdatesAsynchronously(self, value):
        if value is True:
            self._update_mode = PyDMTimePlot.AsynchronousMode
        else:
            self._update_mode = PyDMTimePlot.SynchronousMode
        self.initialize_buffer()

    def resetUpdatesAsynchronously(self):
        self._update_mode = PyDMTimePlot.SynchronousMode
        self.initialize_buffer()

    def max_x(self):
        """
        Provide the the most recent timestamp accumulated from the data buffer.
        This is useful for scaling the x-axis.

        Returns
        -------
        float
            The timestamp of the most recent data point recorded into the data buffer.
        """
        return self.data_buffer[0, -1]

    def channels(self):
        return [self.channel]


class PyDMTimePlot(BasePlot):
    """
    PyDMWaveformPlot is a widget to plot one or more waveforms.

    Each curve can plot either a Y-axis waveform vs. its indices,
    or a Y-axis waveform against an X-axis waveform.

    Parameters
    ----------
    parent : optional
        The parent of this widget.
    init_y_channels : list
        A list of scalar channels to plot vs time.
    plot_by_timestamps : bool
        If True, the x-axis shows timestamps as ticks, and those timestamps
        scroll to the left as time progresses.  If False, the x-axis tick marks
        show time relative to the current time.
    background: optional
        The background color for the plot.  Accepts any arguments that
        pyqtgraph.mkColor will accept.
    """
    SynchronousMode = 1
    AsynchronousMode = 2

    plot_redrawn_signal = Signal(TimePlotCurveItem)

    def __init__(self, parent=None, init_y_channels=[], plot_by_timestamps=True, background='default'):
        """
        Parameters
        ----------

        parent : Widget
            The parent widget of the chart.
        init_y_channels : list
            A list of scalar channels to plot vs time.
        plot_by_timestamps : bool
            If True, the x-axis shows timestamps as ticks, and those timestamps
            scroll to the left as time progresses.  If False, the x-axis tick
            marks show time relative to the current time.
        background : str, optional
            The background color for the plot.  Accepts any arguments that
            pyqtgraph.mkColor will accept.
        """
        self._plot_by_timestamps = plot_by_timestamps

        self._left_axis = AxisItem("left")
        if plot_by_timestamps:
            self._bottom_axis = TimeAxisItem('bottom')
        else:
            self.starting_epoch_time = time.time()
            self._bottom_axis = AxisItem('bottom')

        super(PyDMTimePlot, self).__init__(parent=parent, background=background,
                                           axisItems={"bottom": self._bottom_axis, "left": self._left_axis})

        # Removing the downsampling while PR 763 is not merged at pyqtgraph
        # Reference: https://github.com/pyqtgraph/pyqtgraph/pull/763
        # self.setDownsampling(ds=True, auto=True, mode="mean")

        if self._plot_by_timestamps:
            self.plotItem.disableAutoRange(ViewBox.XAxis)
            self.getViewBox().setMouseEnabled(x=False)
        else:
            self.plotItem.setRange(xRange=[DEFAULT_X_MIN, 0], padding=0)
            self.plotItem.setLimits(xMax=0)

        self._bufferSize = DEFAULT_BUFFER_SIZE

        self._time_span = DEFAULT_TIME_SPAN  # This is in seconds
        self._update_interval = DEFAULT_UPDATE_INTERVAL

        self.update_timer = QTimer(self)
        self.update_timer.setInterval(self._update_interval)
        self._update_mode = PyDMTimePlot.SynchronousMode
        self._needs_redraw = True

        self.labels = {
            "left": None,
            "right": None,
            "bottom": None
        }

        self.units = {
            "left": None,
            "right": None,
            "bottom": None
        }

        for channel in init_y_channels:
            self.addYChannel(channel)

    def initialize_for_designer(self):
        # If we are in Qt Designer, don't update the plot continuously.
        # This function gets called by PyDMTimePlot's designer plugin.
        self.redraw_timer.setSingleShot(True)

    def addYChannel(self, y_channel=None, name=None, color=None,
                    lineStyle=None, lineWidth=None, symbol=None,
                    symbolSize=None):
        """
        Adds a new curve to the current plot

        Parameters
        ----------
        y_channel : str
            The PV address
        name : str
            The name of the curve (usually made the same as the PV address)
        color : QColor
            The color for the curve
        lineStyle : str
            The line style of the curve, i.e. solid, dash, dot, etc.
        lineWidth : int
            How thick the curve line should be
        symbol : str
            The symbols as markers along the curve, i.e. circle, square,
            triangle, star, etc.
        symbolSize : int
            How big the symbols should be

        Returns
        -------
        new_curve : TimePlotCurveItem
            The newly created curve.
        """
        plot_opts = dict()
        plot_opts['symbol'] = symbol
        if symbolSize is not None:
            plot_opts['symbolSize'] = symbolSize
        if lineStyle is not None:
            plot_opts['lineStyle'] = lineStyle
        if lineWidth is not None:
            plot_opts['lineWidth'] = lineWidth

        # Add curve
        new_curve = TimePlotCurveItem(y_channel, plot_by_timestamps=self._plot_by_timestamps, name=name, color=color,
                                      **plot_opts)
        new_curve.setUpdatesAsynchronously(self.updatesAsynchronously)
        new_curve.setBufferSize(self._bufferSize)

        self.update_timer.timeout.connect(new_curve.asyncUpdate)
        self.addCurve(new_curve, curve_color=color)

        new_curve.data_changed.connect(self.set_needs_redraw)
        self.redraw_timer.start()

        return new_curve

    def removeYChannel(self, curve):
        """
        Remove a curve from the graph. This also stops update the timer
        associated with the curve.

        Parameters
        ----------
        curve : TimePlotCurveItem
            The curve to be removed.
        """
        self.update_timer.timeout.disconnect(curve.asyncUpdate)
        self.removeCurve(curve)
        if len(self._curves) < 1:
            self.redraw_timer.stop()

    def removeYChannelAtIndex(self, index):
        """
        Remove a curve from the graph, given its index in the graph's curve
        list.

        Parameters
        ----------
        index : int
            The curve's index from the graph's curve list.
        """
        curve = self._curves[index]
        self.removeYChannel(curve)

    @Slot()
    def set_needs_redraw(self):
        self._needs_redraw = True

    @Slot()
    def redrawPlot(self):
        """
        Redraw the graph
        """
        if not self._needs_redraw:
            return

        self.updateXAxis()

        for curve in self._curves:
            curve.redrawCurve()
            self.plot_redrawn_signal.emit(curve)
        self._needs_redraw = False

    def updateXAxis(self, update_immediately=False):
        """
        Update the x-axis for every graph redraw.

        Parameters
        ----------
        update_immediately : bool
            Update the axis range(s) immediately if True, or defer until the
            next rendering.
        """
        if len(self._curves) == 0:
            return

        if self._plot_by_timestamps:
            if self._update_mode == PyDMTimePlot.SynchronousMode:
                maxrange = max([curve.max_x() for curve in self._curves])
            else:
                maxrange = time.time()
            minrange = maxrange - self._time_span
            self.plotItem.setXRange(minrange, maxrange, padding=0.0, update=update_immediately)
        else:
            diff_time = self.starting_epoch_time - max([curve.max_x() for curve in self._curves])
            if diff_time > DEFAULT_X_MIN:
                diff_time = DEFAULT_X_MIN
            self.getViewBox().setLimits(minXRange=diff_time)

    def clearCurves(self):
        """
        Remove all curves from the graph.
        """
        super(PyDMTimePlot, self).clear()

    def getCurves(self):
        """
        Dump the current list of curves and each curve's settings into a list
        of JSON-formatted strings.

        Returns
        -------
        settings : list
            A list of JSON-formatted strings, each containing a curve's
            settings
        """
        return [json.dumps(curve.to_dict()) for curve in self._curves]

    def setCurves(self, new_list):
        """
        Add a list of curves into the graph.

        Parameters
        ----------
        new_list : list
            A list of JSON-formatted strings, each contains a curve and its
            settings
        """
        try:
            new_list = [json.loads(str(i)) for i in new_list]
        except ValueError as e:
            logger.exception("Error parsing curve json data: {}".format(e))
            return
        self.clearCurves()
        for d in new_list:
            color = d.get('color')
            if color:
                color = QColor(color)
            self.addYChannel(d['channel'],
                             name=d.get('name'), color=color,
                             lineStyle=d.get('lineStyle'),
                             lineWidth=d.get('lineWidth'),
                             symbol=d.get('symbol'),
                             symbolSize=d.get('symbolSize'))

    curves = Property("QStringList", getCurves, setCurves)

    def findCurve(self, pv_name):
        """
        Find a curve from a graph's curve list.

        Parameters
        ----------
        pv_name : str
            The curve's PV address.

        Returns
        -------
        curve : TimePlotCurveItem
            The found curve, or None.
        """
        for curve in self._curves:
            if curve.address == pv_name:
                return curve

    def refreshCurve(self, curve):
        """
        Remove a curve currently being plotted on the timeplot, then redraw
        that curve, which could have been updated with a new symbol, line
        style, line width, etc.

        Parameters
        ----------
        curve : TimePlotCurveItem
            The curve to be re-added.
        """
        curve = self.findCurve(curve.channel)
        if curve:
            self.removeYChannel(curve)
            self.addYChannel(y_channel=curve.address, color=curve.color,
                             name=curve.address, lineStyle=curve.lineStyle,
                             lineWidth=curve.lineWidth, symbol=curve.symbol,
                             symbolSize=curve.symbolSize)

    def addLegendItem(self, item, pv_name, force_show_legend=False):
        """
        Add an item into the graph's legend.

        Parameters
        ----------
        item : TimePlotCurveItem
            A curve being plotted in the graph
        pv_name : str
            The PV channel
        force_show_legend : bool
            True to make the legend to be displayed; False to just add the
            item, but do not display the legend.
        """
        self._legend.addItem(item, pv_name)
        self.setShowLegend(force_show_legend)

    def removeLegendItem(self, pv_name):
        """
        Remove an item from the legend.

        Parameters
        ----------
        pv_name : str
            The PV channel, used to search for the legend item to remove.
        """
        self._legend.removeItem(pv_name)
        if len(self._legend.items) == 0:
            self.setShowLegend(False)

    def getBufferSize(self):
        """
        Get the size of the data buffer for the entire chart.

        Returns
        -------
        size : int
            The chart's data buffer size.
        """
        return int(self._bufferSize)

    def setBufferSize(self, value):
        """
        Set the size of the data buffer of the entire chart. This will also
        update the same value for each of the data buffer of each chart's
        curve.

        Parameters
        ----------
        value : int
            The new buffer size for the chart.
        """
        if self._bufferSize != int(value):
            # Originally, the bufferSize is the max between the user's input and 1, and 1 doesn't make sense.
            # So, I'm comparing the user's input with the minimum buffer size, and pick the max between the two
            self._bufferSize = max(int(value), MINIMUM_BUFFER_SIZE)
            for curve in self._curves:
                curve.setBufferSize(value)

    def resetBufferSize(self):
        """
        Reset the data buffer size of the chart, and each of the chart's
        curve's data buffer, to the minimum
        """
        if self._bufferSize != DEFAULT_BUFFER_SIZE:
            self._bufferSize = DEFAULT_BUFFER_SIZE
            for curve in self._curves:
                curve.resetBufferSize()

    bufferSize = Property("int", getBufferSize, setBufferSize, resetBufferSize)

    def getUpdatesAsynchronously(self):
        return self._update_mode == PyDMTimePlot.AsynchronousMode

    def setUpdatesAsynchronously(self, value):
        for curve in self._curves:
            curve.setUpdatesAsynchronously(value)
        if value is True:
            self._update_mode = PyDMTimePlot.AsynchronousMode
            self.update_timer.start()
        else:
            self._update_mode = PyDMTimePlot.SynchronousMode
            self.update_timer.stop()

    def resetUpdatesAsynchronously(self):
        self._update_mode = PyDMTimePlot.SynchronousMode
        self.update_timer.stop()
        for curve in self._curves:
            curve.resetUpdatesAsynchronously()

    updatesAsynchronously = Property("bool",
                                     getUpdatesAsynchronously,
                                     setUpdatesAsynchronously,
                                     resetUpdatesAsynchronously)

    def getTimeSpan(self):
        """
        The extent of the x-axis of the chart, in seconds.  In other words,
        how long a data point stays on the plot before falling off the left
        edge.

        Returns
        -------
        time_span : float
            The extent of the x-axis of the chart, in seconds.
        """
        return float(self._time_span)

    def setTimeSpan(self, value):
        """
        Set the extent of the x-axis of the chart, in seconds.
        In aynchronous mode, the chart will allocate enough buffer for the new time span duration.
        Data arriving after each duration will be recorded into the buffer
        having been rotated.

        Parameters
        ----------
        value : float
            The time span duration, in seconds, to allocate enough buffer to
            collect data for, before rotating the buffer.
        """
        value = float(value)
        if self._time_span != value:
            self._time_span = value

            if self.getUpdatesAsynchronously():
                self.setBufferSize(int((self._time_span * 1000.0) / self._update_interval))

            self.updateXAxis(update_immediately=True)

    def resetTimeSpan(self):
        """
        Reset the timespan to the default value.
        """
        if self._time_span != DEFAULT_TIME_SPAN:
            self._time_span = DEFAULT_TIME_SPAN
            if self.getUpdatesAsynchronously():
                self.setBufferSize(int((self._time_span * 1000.0) / self._update_interval))
            self.updateXAxis(update_immediately=True)

    timeSpan = Property(float, getTimeSpan, setTimeSpan, resetTimeSpan)

    def getUpdateInterval(self):
        """
        Get the update interval for the chart.

        Returns
        -------
        interval : float
            The update interval of the chart.
        """
        return float(self._update_interval) / 1000.0

    def setUpdateInterval(self, value):
        """
        Set a new update interval for the chart and update its data buffer size.

        Parameters
        ----------
        value : float
            The new update interval value.
        """
        value = abs(int(1000.0 * value))
        if self._update_interval != value:
            self._update_interval = value
            self.update_timer.setInterval(self._update_interval)
            if self.getUpdatesAsynchronously():
                self.setBufferSize(int((self._time_span * 1000.0) / self._update_interval))

    def resetUpdateInterval(self):
        """
        Reset the chart's update interval to the default.
        """
        if self._update_interval != DEFAULT_UPDATE_INTERVAL:
            self._update_interval = DEFAULT_UPDATE_INTERVAL
            self.update_timer.setInterval(self._update_interval)
            if self.getUpdatesAsynchronously():
                self.setBufferSize(int((self._time_span * 1000.0) / self._update_interval))

    updateInterval = Property(float, getUpdateInterval,
                              setUpdateInterval, resetUpdateInterval)

    def getAutoRangeX(self):
        if self._plot_by_timestamps:
            return False
        else:
            super(PyDMTimePlot, self).getAutoRangeX()

    def setAutoRangeX(self, value):
        if self._plot_by_timestamps:
            self._auto_range_x = False
            self.plotItem.enableAutoRange(ViewBox.XAxis, enable=self._auto_range_x)
        else:
            super(PyDMTimePlot, self).setAutoRangeX(value)

    def channels(self):
        return [curve.channel for curve in self._curves]

    # The methods for autoRangeY, minYRange, and maxYRange are
    # all defined in BasePlot, but we don't expose them as properties there, because not all plot
    # subclasses necessarily want them to be user-configurable in Designer.
    autoRangeY = Property(bool, BasePlot.getAutoRangeY,
                          BasePlot.setAutoRangeY,
                          BasePlot.resetAutoRangeY, doc="""
    Whether or not the Y-axis automatically rescales to fit the data.
    If true, the values in minYRange and maxYRange are ignored.
    """)

    minYRange = Property(float, BasePlot.getMinYRange,
                         BasePlot.setMinYRange, doc="""
    Minimum Y-axis value visible on the plot.""")

    maxYRange = Property(float, BasePlot.getMaxYRange,
                         BasePlot.setMaxYRange, doc="""
    Maximum Y-axis value visible on the plot.""")

    def enableCrosshair(self, is_enabled, starting_x_pos=DEFAULT_X_MIN, starting_y_pos=DEFAULT_Y_MIN, vertical_angle=90,
                        horizontal_angle=0, vertical_movable=False, horizontal_movable=False):
        """
        Display a crosshair on the graph.

        Parameters
        ----------
        is_enabled : bool
            True is to display the crosshair; False is to hide it.
        starting_x_pos : float
            The x position where the vertical line will cross
        starting_y_pos : float
            The y position where the horizontal line will cross
        vertical_angle : int
            The angle of the vertical line
        horizontal_angle : int
            The angle of the horizontal line
        vertical_movable : bool
            True if the user can move the vertical line; False if not
        horizontal_movable : bool
            True if the user can move the horizontal line; False if not
        """
        super(PyDMTimePlot, self).enableCrosshair(is_enabled, starting_x_pos, starting_y_pos, vertical_angle,
                                                  horizontal_angle, vertical_movable, horizontal_movable)


class TimeAxisItem(AxisItem):
    """
    TimeAxisItem formats a unix time axis into a human-readable format.
    """
    def tickStrings(self, values, scale, spacing):
        strings = []
        for val in values:
            strings.append(time.strftime("%H:%M:%S", time.localtime(val)))
        return strings
