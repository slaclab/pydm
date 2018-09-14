import time
import json
import datetime
import collections
from collections import OrderedDict
from pyqtgraph import ViewBox, AxisItem
import numpy as np
from qtpy.QtGui import (QColor, QFrame, QVBoxLayout, QApplication, QLabel,
                        QPushButton, QTableWidget, QTableWidgetItem, QCursor)
from qtpy.QtCore import (Slot, Property, QTimer, Qt)
from .baseplot import BasePlot, BasePlotCurveItem
from .channel import PyDMChannel
from ..utilities import remove_protocol
from .base import PyDMWidget


logger = logging.getLogger(__name__)


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
        self.setAcceptDrops(True)
        self.plotItem.disableAutoRange(ViewBox.XAxis)
        self.getViewBox().setMouseEnabled(x=False)
        self._bufferSize = 1200
        self.update_timer = QTimer(self)
        self._time_span = 5.0  # This is in seconds
        self._update_interval = 100
        self.update_timer.setInterval(self._update_interval)
        self._update_mode = PyDMTimePlot.SynchronousMode
        self._needs_redraw = True
        for channel in init_y_channels:
            self.addYChannel(channel)

    def initialize_for_designer(self):
        # If we are in Qt Designer, don't update the plot continuously.
        # This function gets called by PyDMTimePlot's designer plugin.
        self.redraw_timer.setSingleShot(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('text/plain'):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat('text/plain'):
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        '''
        Handle drop events (result of a drag-and-drop operation)

        Multiple addresses can be specified, delimited by LF (\n).
        Note that the mime data is using text/plain and not URLs, due to the
        fact that many pydm addresses are invalid URLs according to QUrl.
        '''
        addresses = str(event.mimeData().text()).split('\n')
        for new_addr in addresses:
            logger.debug('Address dropped: %s', new_addr)
            if new_addr is None:
                logger.warning('Empty address dropped')
                continue

            if not any(curve.address == new_addr for curve in self._curves):
                logger.debug('Adding new channel: %s', new_addr)
                curve = self.addYChannel(y_channel=new_addr)
                if curve.channel is not None:
                    self.app.add_connection(curve.channel)

        logger.debug('%s Curve address list:', self)
        for idx, curve in enumerate(self._curves):
            logger.debug('%d) %s', idx, curve.address)

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
        if not self._needs_redraw or not self.isVisible():
            return

        self.updateXAxis()
        for curve in self._curves:
            curve.redrawCurve()
        self._needs_redraw = False

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


class PyDMHistoryTable(QTableWidget, PyDMWidget):
    """
    A QTableWidget with support for Channels and more from PyDM.

    Values of the array are displayed in the selected number of columns.
    The number of rows is determined by the size of the waveform.
    It is possible to define the labels of each row and column.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

    def __init__(self, max_items=5, value_history=None, parent=None,
                 init_channel=None):
        QTableWidget.__init__(self, parent)
        PyDMWidget.__init__(self, init_channel=init_channel)
        self._columnHeaders = ["Timestamp", "Value"]
        self._rowHeaders = []
        self._itemsFlags = (Qt.ItemIsSelectable |
                            Qt.ItemIsEnabled)
        self.setColumnCount(2)
        self.setSizeAdjustPolicy(self.AdjustToContents)

        if value_history is None:
            value_history = []
        else:
            value_history = list(value_history)

        self.value_history = collections.deque(value_history, max_items)

    def value_changed(self, new_value):
        """
        Callback invoked when the Channel value is changed.

        Parameters
        ----------
        new_value : np.ndarray
            The new waveform value from the channel.
        """
        ts = time.time()
        self.value_history.append((ts, new_value))
        super(PyDMHistoryTable, self).value_changed(new_value)

        if not self.isVisible():
            return

        self.setRowCount(len(self.value_history))
        for row, (ts, value) in enumerate(reversed(self.value_history)):
            value_cell = QTableWidgetItem(str(value))
            value_cell.setFlags(self._itemsFlags)
            ts = str(datetime.datetime.fromtimestamp(ts))
            self.setItem(row, 0, QTableWidgetItem(ts))
            self.setItem(row, 1, value_cell)

        self.setVerticalHeaderLabels(self._rowHeaders)
        self.setHorizontalHeaderLabels(self._columnHeaders)
        self.resizeColumnsToContents()

    @pyqtProperty("QStringList")
    def columnHeaderLabels(self):
        """
        Return the list of labels for the columns of the Table.

        Returns
        -------
        list of strings
        """
        return self._columnHeaders

    @columnHeaderLabels.setter
    def columnHeaderLabels(self, new_labels):
        """
        Set the list of labels for the columns of the Table.

        If new_labels is empty the column numbers will be used.

        Parameters
        ----------
        new_labels : list of strings
        """
        if new_labels:
            new_labels += (self.columnCount() - len(new_labels)) * [""]
        self._columnHeaders = new_labels
        self.setHorizontalHeaderLabels(self._columnHeaders)
        self.setColumnCount(len(self._columnHeaders))

    @pyqtProperty("QStringList")
    def rowHeaderLabels(self):
        """
        Return the list of labels for the rows of the Table.

        Returns
        -------
        list of strings
        """
        return self._rowHeaders

    @rowHeaderLabels.setter
    def rowHeaderLabels(self, new_labels):
        """
        Set the list of labels for the rows of the Table.

        If new_labels is empty the row numbers will be used.

        Parameters
        ----------
        new_labels : list of strings
        """
        if new_labels:
            new_labels += (self.rowCount() - len(new_labels)) * [""]
        self._rowHeaders = new_labels
        self.setVerticalHeaderLabels(self._rowHeaders)


class PyDMHistoryFrame(QFrame):
    def __init__(self, value_history, parent=None, background='default'):
        super(PyDMHistoryFrame, self).__init__(parent=None)
        self.setMinimumWidth(200)
        self.setMinimumHeight(200)

        self.value_history = value_history
        self.pop_out_button = QPushButton('Expand')
        self.pop_out_button.pressed.connect(self.pop_out)
        self.pop_out_button.setMaximumWidth(100)
        self.popped_out = False

        self.layout = QVBoxLayout()
        # self.title_widget = QLabel(parent.channel)
        # self.title_widget.setAlignment(Qt.AlignCenter)
        self.plot_widget = PyDMTimePlot(parent=None,
                                        init_y_channels=[parent.channel],
                                        background=background)
        self.table_widget = PyDMHistoryTable(init_channel=parent.channel,
                                             parent=None,
                                             value_history=value_history)
        self.layout.addWidget(self.pop_out_button)
        # self.layout.addWidget(self.title_widget)
        self.layout.addWidget(self.plot_widget)
        self.layout.addWidget(self.table_widget)
        self.setLayout(self.layout)
        self.setWindowFlags(Qt.Popup | Qt.WindowStaysOnTopHint)
        self._copy_history()

    def showEvent(self, event):
        self.pop_out_button.setVisible(not self.popped_out)

    def hideEvent(self, event):
        self.pop_out_button.setVisible(True)
        self.popped_out = False

    def pop_out(self):
        self.setWindowFlags(Qt.Dialog)
        self.setVisible(True)
        self.show()
        self.activateWindow()

        self.popped_out = True
        self.pop_out_button.setVisible(False)

    def _copy_history(self):
        if not self.plot_widget._curves:
            return

        curve = self.plot_widget._curves[0]

        num_points = min(curve._bufferSize, len(self.value_history))
        slc = slice(-num_points, None)
        points = tuple(self.value_history)[slc]
        curve.data_buffer[0, slc] = [ts for ts, datapoint in points]
        curve.data_buffer[1, slc] = [datapoint for ts, datapoint in points]
        curve.points_accumulated = num_points
