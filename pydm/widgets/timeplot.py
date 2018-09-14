from qtpy.QtGui import QColor
from qtpy.QtCore import Slot, Property, QTimer
from pyqtgraph import ViewBox, AxisItem
import numpy as np
import time
import json
from collections import OrderedDict
from .baseplot import BasePlot, BasePlotCurveItem
from .channel import PyDMChannel
from .. utilities import remove_protocol


class TimePlotCurveItem(BasePlotCurveItem):

    def __init__(self, channel_address=None, **kws):
        channel_address = "" if channel_address is None else channel_address
        if 'name' not in kws or kws['name'] is None:
            name = remove_protocol(channel_address)
            kws['name'] = name
        self._bufferSize = 1200
        self._update_mode = PyDMTimePlot.SynchronousMode
        self.data_buffer = np.zeros((2, self._bufferSize),
                                    order='f', dtype=float)
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

    @Slot(bool)
    def connectionStateChanged(self, connected):
        # Maybe change pen stroke?
        self.connected = connected

    @Slot(float)
    @Slot(int)
    def receiveNewValue(self, new_value):
        if self._update_mode == PyDMTimePlot.SynchronousMode:
            self.data_buffer = np.roll(self.data_buffer, -1)
            self.data_buffer[0, self._bufferSize - 1] = time.time()
            self.data_buffer[1, self._bufferSize - 1] = new_value
            if self.points_accumulated < self._bufferSize:
                self.points_accumulated = self.points_accumulated + 1
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
        if self._bufferSize != 1200:
            self._bufferSize = 1200
            self.initialize_buffer()

    @Slot()
    def redrawCurve(self):
        if self.connected:
            self.setData(y=self.data_buffer[1, -self.points_accumulated:].astype(np.float),
                         x=self.data_buffer[0, -self.points_accumulated:].astype(np.float))

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


class PyDMTimePlot(BasePlot):
    SynchronousMode = 1
    AsynchronousMode = 2

    def __init__(self, parent=None, init_y_channels=[], background='default'):
        self._bottom_axis = TimeAxisItem('bottom')
        self._left_axis = AxisItem('left')
        super(PyDMTimePlot, self).__init__(
                                    parent=parent,
                                    background=background,
                                    axisItems={'bottom': self._bottom_axis,
                                               'left': self._left_axis}
                                    )
        self.plotItem.disableAutoRange(ViewBox.XAxis)
        self.getViewBox().setMouseEnabled(x=False)
        self._bufferSize = 1200
        self.update_timer = QTimer(self)
        self._time_span = 5.0  # This is in seconds
        self._update_interval = 100
        self.update_timer.setInterval(self._update_interval)
        self._update_mode = PyDMTimePlot.SynchronousMode
        for channel in init_y_channels:
            self.addYChannel(channel)

    def initialize_for_designer(self):
        # If we are in Qt Designer, don't update the plot continuously.
        # This function gets called by PyDMTimePlot's designer plugin.
        self.redraw_timer.setSingleShot(True)

    # Adds a new curve to the current plot
    def addYChannel(self, y_channel=None, name=None, color=None,
                    lineStyle=None, lineWidth=None, symbol=None,
                    symbolSize=None):
        plot_opts = {}
        plot_opts['symbol'] = symbol
        if symbolSize is not None:
            plot_opts['symbolSize'] = symbolSize
        if lineStyle is not None:
            plot_opts['lineStyle'] = lineStyle
        if lineWidth is not None:
            plot_opts['lineWidth'] = lineWidth
        # Add curve
        new_curve = TimePlotCurveItem(y_channel,
                                      name=name,
                                      color=color,
                                      **plot_opts)
        new_curve.setUpdatesAsynchronously(self.updatesAsynchronously)
        new_curve.setBufferSize(self._bufferSize)
        self.update_timer.timeout.connect(new_curve.asyncUpdate)
        self.addCurve(new_curve, curve_color=color)
        self.redraw_timer.start()

    def removeYChannel(self, curve):
        self.update_timer.timeout.disconnect(curve.asyncUpdate)
        self.removeCurve(curve)
        if len(self._curves) < 1:
            self.redraw_timer.stop()

    def removeYChannelAtIndex(self, index):
        curve = self._curves[index]
        self.removeYChannel(curve)

    @Slot()
    def redrawPlot(self):
        self.updateXAxis()
        for curve in self._curves:
            curve.redrawCurve()

    def updateXAxis(self, update_immediately=False):
        if len(self._curves) == 0:
            return
        if self._update_mode == PyDMTimePlot.SynchronousMode:
            maxrange = max([curve.max_x() for curve in self._curves])
        else:
            maxrange = time.time()
        minrange = maxrange - self._time_span
        self.plotItem.setXRange(minrange, maxrange, padding=0.0,
                                update=update_immediately)

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

    def getBufferSize(self):
        return int(self._bufferSize)

    def setBufferSize(self, value):
        if self._bufferSize != int(value):
            self._bufferSize = max(int(value), 1)
            for curve in self._curves:
                curve.setBufferSize(value)

    def resetBufferSize(self):
        if self._bufferSize != 1200:
            self._bufferSize = 1200
            for curve in self._curves:
                curve.resetBufferSize()

    bufferSize = Property("int", getBufferSize,
                          setBufferSize, resetBufferSize)

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
                    curve.setBufferSize(int((self._time_span * 1000.0) /
                                            self._update_interval))
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


class TimeAxisItem(AxisItem):

    def tickStrings(self, values, scale, spacing):
        strings = []
        for val in values:
            strings.append(time.strftime("%H:%M:%S", time.localtime(val)))
        return strings
