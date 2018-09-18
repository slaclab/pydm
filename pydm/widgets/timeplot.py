from pyqtgraph import CurvePoint
import time
import json
from collections import OrderedDict
from pyqtgraph import ViewBox, AxisItem
import numpy as np
from qtpy.QtGui import QColor
from qtpy.QtCore import Qt, Slot, Property, QTimer
from .baseplot import BasePlot, BasePlotCurveItem
from .channel import PyDMChannel
from .. utilities import remove_protocol

MINIMUM_BUFFER_SIZE = 10
DEFAULT_X_MIN = -30
DEFAULT_Y_MIN = 0


class TimePlotCurveItem(BasePlotCurveItem):
    """
    TimePlot now supports two mode:

    1. The "classic" mode, in which the x-axis shows the timestamps, and move to the left
    2. The new mode, in which the x-axis shows the negative time in seconds from the starting time, at which x = 0.

    To maintain backward compatibility, the default drawing mode is in the classic, "plot_by_timestamps" mode, for both
    TimePlotCurveItem and TimePlotCurve.
    """
    def __init__(self, channel_address=None, plot_by_timestamps=True, **kws):
        channel_address = "" if channel_address is None else channel_address
        if "name" not in kws or not kws["name"]:
            name = remove_protocol(channel_address)
            kws["name"] = name

        self.plot_by_timestamps = plot_by_timestamps

        self.starting_epoch_time = time.time()
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
        return self.plot_by_timestamps

    @plotByTimeStamps.setter
    def plotByTimeStamps(self, new_value):
        self.plot_by_timestamps = new_value

    @property
    def minY(self):
        return self._min_y_value

    @property
    def maxY(self):
        return self._max_y_value

    @Slot(bool)
    def connectionStateChanged(self, connected):
        # Maybe change pen stroke?
        self.connected = connected

    @Slot(float)
    @Slot(int)
    def receiveNewValue(self, new_value):
        self.update_min_max_y_values(new_value)

        if self._update_mode == PyDMTimePlot.SynchronousMode:
            self.data_buffer = np.roll(self.data_buffer, -1)
            self.data_buffer[0, self._bufferSize - 1] = time.time()
            self.data_buffer[1, self._bufferSize - 1] = new_value

            if self.points_accumulated < self._bufferSize:
                self.points_accumulated += 1
            self.data_changed.emit()
        elif self._update_mode == PyDMTimePlot.AsynchronousMode:
            self.latest_value = new_value

    @Slot()
    def asyncUpdate(self):
        if self._update_mode != PyDMTimePlot.AsynchronousMode:
            return
        self.data_buffer = np.roll(self.data_buffer, -1)
        self.data_buffer[0, self._bufferSize - 1] = time.time()
        self.data_buffer[1, self._bufferSize - 1] = self.latest_value
        if self.points_accumulated < self._bufferSize:
            self.points_accumulated = self.points_accumulated + 1
        self.data_changed.emit()

        if self._update_mode == PyDMTimePlot.AsynchronousMode:
            self.data_buffer = np.roll(self.data_buffer, -1)
            self.data_buffer[0, self._bufferSize - 1] = time.time()
            self.data_buffer[1, self._bufferSize - 1] = self.latest_value

            if self.points_accumulated < self._bufferSize:
                self.points_accumulated += 1

    def update_min_max_y_values(self, new_value):
        if self._min_y_value is None and self._max_y_value is None:
            self._min_y_value = self._max_y_value = new_value
        elif self._min_y_value > new_value:
            self._min_y_value = new_value
        elif self._max_y_value < new_value:
            self._max_y_value = new_value

    def initialize_buffer(self):
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
            self._bufferSize = max(int(value), 1)
            self.initialize_buffer()

    def resetBufferSize(self):
        if self._bufferSize != MINIMUM_BUFFER_SIZE:
            self._bufferSize = MINIMUM_BUFFER_SIZE
            self.initialize_buffer()

    @Slot()
    def redrawCurve(self):
        if self.connected:
            x = self.data_buffer[0, -self.points_accumulated:].astype(np.float)
            y = self.data_buffer[1, -self.points_accumulated:].astype(np.float)

            if self.plot_by_timestamps:
                self.setData(y=y, x=x)
            else:
                time_diff = self.starting_epoch_time - x[len(x) - 1]
                self.setData(y=self.data_buffer[1, -self.points_accumulated:])
                self.setPos(time_diff, 0)

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
        return self.data_buffer[0, -1]

    def max_y(self):
        return self.data_buffer[1, -1]


class PyDMTimePlot(BasePlot):
    """
    TimePlot now supports two mode:

    1. The "classic" mode, in which the x-axis shows the timestamps, and move to the left
    2. The new mode, in which the x-axis shows the negative time in seconds from the starting time, at which x = 0.

    To maintain backward compatibility, the default drawing mode is in the classic, "plot_by_timestamps" mode, for both
    TimePlotCurveItem and TimePlotCurve.
    """
    SynchronousMode = 1
    AsynchronousMode = 2

    def __init__(self, parent=None, init_y_channels=[], plot_by_timestamps=True, background='default',
                 plot_display=None):
        self.plot_by_timestamps = plot_by_timestamps

        self._left_axis = AxisItem("left")
        if plot_by_timestamps:
            self._bottom_axis = TimeAxisItem('bottom')
        else:
            self.starting_epoch_time = time.time()
            self._bottom_axis = AxisItem('bottom')

        super(PyDMTimePlot, self).__init__(parent=parent, background=background,
                                           axisItems={"bottom": self._bottom_axis, "left": self._left_axis},
                                           plot_display=plot_display)

        if self.plot_by_timestamps:
            self.plotItem.disableAutoRange(ViewBox.XAxis)
            self.getViewBox().setMouseEnabled(x=False)
        else:
            self.plotItem.setRange(xRange=[DEFAULT_X_MIN, 0])
            self.plotItem.setLimits(xMax=0)

        self._bufferSize = MINIMUM_BUFFER_SIZE

        self._time_span = 5.0  # This is in seconds
        self._update_interval = 100

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

        self._show_right_axis = False

        for channel in init_y_channels:
            self.addYChannel(channel)

    def initialize_for_designer(self):
        # If we are in Qt Designer, don't update the plot continuously.
        # This function gets called by PyDMTimePlot's designer plugin.
        self.redraw_timer.setSingleShot(True)

    def getPlotByTimestamps(self):
        """
        Whether the graph will show the moving timestamps as the x-axis (default), or the relative time after the
        starting time.

        :return: True if the x-axis will show the moving timestamps (default); or the relative time as the x-axis
                 ticks if False.
        """
        return self.plot_by_timestamps

    def setPlotByTimesStamps(self, new_value):
        if new_value != self.plot_by_timestamps:
            self.plot_by_timestamps = new_value

    plotByTimeStamps = Property("bool", getPlotByTimestamps, setPlotByTimesStamps)

    # Adds a new curve to the current plot
    def addYChannel(self, y_channel=None, name=None, color=None,
                    lineStyle=None, lineWidth=None, symbol=None,
                    symbolSize=None):
        plot_opts = dict()
        plot_opts['symbol'] = symbol
        if symbolSize is not None:
            plot_opts['symbolSize'] = symbolSize
        if lineStyle is not None:
            plot_opts['lineStyle'] = lineStyle
        if lineWidth is not None:
            plot_opts['lineWidth'] = lineWidth

        # Add curve
        new_curve = TimePlotCurveItem(y_channel, plot_by_timestamps=self.plot_by_timestamps, name=name, color=color,
                                      **plot_opts)
        new_curve.setUpdatesAsynchronously(self.updatesAsynchronously)
        new_curve.setBufferSize(self._bufferSize)

        self.update_timer.timeout.connect(new_curve.asyncUpdate)
        self.addCurve(new_curve, curve_color=color)

        new_curve.data_changed.connect(self.set_needs_redraw)
        self.redraw_timer.start()

        return new_curve

    def removeYChannel(self, curve):
        self.update_timer.timeout.disconnect(curve.asyncUpdate)
        self.removeCurve(curve)
        if len(self._curves) < 1:
            self.redraw_timer.stop()

    def removeYChannelAtIndex(self, index):
        curve = self._curves[index]
        self.removeYChannel(curve)

    @Slot()
    def set_needs_redraw(self):
        self._needs_redraw = True

    @Slot()
    def redrawPlot(self):
        if not self._needs_redraw:
            return
        self.updateXAxis()

        for curve in self._curves:
            curve.redrawCurve()
            if self.plot_display:
                self.plot_display.update_curve_data(curve)
        self._needs_redraw = False

    def updateXAxis(self, update_immediately=False):
        if len(self._curves) == 0:
            return

        if self.plot_by_timestamps:
            if self._update_mode == PyDMTimePlot.SynchronousMode:
                maxrange = max([curve.max_x() for curve in self._curves])
            else:
                maxrange = time.time()
            minrange = maxrange - self._time_span
            self.plotItem.setXRange(minrange, maxrange, padding=0.0, update=update_immediately)
        else:
            diff_time = self.starting_epoch_time - min([curve.max_x() for curve in self._curves])
            if diff_time > DEFAULT_X_MIN:
                diff_time = DEFAULT_X_MIN
            self.getViewBox().setLimits(minXRange=diff_time + 10)

    def clearCurves(self):
        super(PyDMTimePlot, self).clear()

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
            self.addYChannel(d['channel'],
                             name=d.get('name'), color=color,
                             lineStyle=d.get('lineStyle'),
                             lineWidth=d.get('lineWidth'),
                             symbol=d.get('symbol'),
                             symbolSize=d.get('symbolSize'))

    curves = Property("QStringList", getCurves, setCurves)

    def findCurve(self, pv_name):
        for curve in self._curves:
            if curve.address == pv_name:
                return curve

    def refreshCurve(self, curve):
        """
        Remove a curve currently being plotted on the timeplot, then redraw that curve, which could have been updated
        with a new symbol, line style, line width, etc.
        :param curve:
        :return:
        """
        curve = self.findCurve(curve.channel)
        if curve:
            self.removeYChannel(curve)
            self.addYChannel(y_channel=curve.address, color=curve.color, name=curve.address,
                             lineStyle=curve.lineStyle, lineWidth=curve.lineWidth, symbol=curve.symbol,
                             symbolSize=curve.symbolSize)

    def annotateCurve(self, curve, annotation):
        curve_point = CurvePoint(curve)
        self.plotItem.addItem(curve_point)
        annotation.setParentItem(curve_point)
        curve_point.setPos(1)

    def addLegendItem(self, item, pv_name, force_show_legend=False):
        self._legend.addItem(item, pv_name)
        self.setShowLegend(force_show_legend)

    def removeLegendItem(self, pv_name):
        self._legend.removeItem(pv_name)
        if len(self._legend.items) == 0:
            self.setShowLegend(False)

    def getBufferSize(self):
        return int(self._bufferSize)

    def setBufferSize(self, value):
        if self._bufferSize != int(value):
            # Originally, the bufferSize is the max between the user's input and 1, and 1 doesn't make sense.
            # So, I'm comparing the user's input with the minimum buffer size, and pick the max between the two
            self._bufferSize = max(int(value), MINIMUM_BUFFER_SIZE)
            for curve in self._curves:
                curve.setBufferSize(value)

    def resetBufferSize(self):
        if self._bufferSize != MINIMUM_BUFFER_SIZE:
            self._bufferSize = MINIMUM_BUFFER_SIZE
            for curve in self._curves:
                curve.resetBufferSize()

    bufferSize = Property("int", getBufferSize,
                          setBufferSize, resetBufferSize)

    def pausePlotting(self):
        remaining_time = self.redraw_timer.remainingTime()
        if remaining_time > 0:
            self.redraw_timer.stop()
        else:
            self.redraw_timer.start()
        return remaining_time

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
        return float(self._time_span)

    def setTimeSpan(self, value):
        value = float(value)
        if self._time_span != value:
            self._time_span = value

            if self.getUpdatesAsynchronously():
                for curve in self._curves:
                    self.setBufferSize(int((self._time_span * 1000.0) / self._update_interval))
            self.updateXAxis(update_immediately=True)

    def resetTimeSpan(self):
        if self._time_span != 5.0:
            self._time_span = 5.0
            if self.getUpdatesAsynchronously():
                for curve in self._curves:
                    curve.setBufferSize(int((self._time_span * 1000.0) /
                                            self._update_interval))
            self.updateXAxis(update_immediately=True)

    timeSpan = Property(float, getTimeSpan, setTimeSpan, resetTimeSpan)

    def getUpdateInterval(self):
        return float(self._update_interval) / 1000.0

    def setUpdateInterval(self, value):
        value = abs(int(1000.0 * value))
        if self._update_interval != value:
            self._update_interval = value
            self.update_timer.setInterval(self._update_interval)
            if self.getUpdatesAsynchronously():
                self.setBufferSize(int((self._time_span * 1000.0) /
                                       self._update_interval))

    def resetUpdateInterval(self):
        if self._update_interval != 100:
            self._update_interval = 100
            self.update_timer.setInterval(self._update_interval)
            if self.getUpdatesAsynchronously():
                self.setBufferSize(int((self._time_span * 1000.0) /
                                       self._update_interval))

    updateInterval = Property(float, getUpdateInterval,
                              setUpdateInterval, resetUpdateInterval)

    def getAutoRangeX(self):
        return False

    def setAutoRangeX(self, value):
        self._auto_range_x = False
        self.plotItem.enableAutoRange(ViewBox.XAxis, enable=self._auto_range_x)

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

    def getShowRightAxis(self):
        return self._show_right_axis

    def setShowRightAxis(self, show):
        self._show_right_axis = show

    showRightAxis = Property("bool", getShowRightAxis, setShowRightAxis)

    def enableCrosshair(self, is_enabled, starting_x_pos=DEFAULT_X_MIN, starting_y_pos=DEFAULT_Y_MIN, vertical_angle=90,
                        horizontal_angle=0, vertical_movable=False, horizontal_movable=False):
        super(PyDMTimePlot, self).enableCrosshair(is_enabled, starting_x_pos, starting_y_pos, vertical_angle,
                                                  horizontal_angle, vertical_movable, horizontal_movable)


class TimeAxisItem(AxisItem):
    def tickStrings(self, values, scale, spacing):
        strings = []
        for val in values:
            strings.append(time.strftime("%H:%M:%S", time.localtime(val)))
        return strings
