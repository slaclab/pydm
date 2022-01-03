import json
import time
from collections import OrderedDict
import numpy as np
from pyqtgraph import DateAxisItem, ErrorBarItem
from pydm.widgets.channel import PyDMChannel
from pydm.widgets.timeplot import TimePlotCurveItem
from pydm.widgets import PyDMTimePlot
from qtpy.QtCore import Property, Signal, Slot
from qtpy.QtGui import QColor

import logging
logger = logging.getLogger(__name__)

DEFAULT_ARCHIVE_BUFFER_SIZE = 18000


class ArchivePlotCurveItem(TimePlotCurveItem):
    """
    ArchivePlotCurveItem is a TimePlotCurveItem with support for receiving data from
    the archiver appliance.

    Parameters
    ----------
    channel_address : str
        The address to of the scalar data to plot.
    plot_by_timestamps : bool
        If True, the x-axis shows timestamps as ticks, and those timestamps
        scroll to the left as time progresses.  If False, the x-axis tick marks
        show time relative to the current time.
    use_archive_data : bool
        If True, requests will be made to archiver appliance for archived data when
        the plot is zoomed or scrolled to the left.
    **kws : dict
        Additional parameters supported by pyqtgraph.PlotDataItem.
    """

    archive_data_request_signal = Signal(object, object, object)

    def __init__(self, channel_address=None, plot_by_timestamps=False, use_archive_data=True, **kws):
        super(ArchivePlotCurveItem, self).__init__(channel_address, plot_by_timestamps, **kws)
        self.use_archive_data = use_archive_data
        self.archive_channel = None
        self.archive_points_accumulated = 0
        self._archiveBufferSize = DEFAULT_ARCHIVE_BUFFER_SIZE
        self.archive_data_buffer = np.zeros((2, self._archiveBufferSize), order='f', dtype=float)
        self.error_bar_item = ErrorBarItem()
        self.error_bar_needs_set = True
        self.zoomed = False

        if channel_address is not None:
            self.setArchiveChannel(channel_address)

    def to_dict(self):
        dic_ = OrderedDict([("useArchiveData", self.use_archive_data), ])
        dic_.update(super(ArchivePlotCurveItem, self).to_dict())
        return dic_

    def setArchiveChannel(self, address):
        """ Creates the channel for communicating with the archiver appliance plugin """
        archive_address = ''
        if address.startswith('ca://'):
            archive_address = address.replace('ca://', 'archiver://pv=', 1)
        elif address.startswith('pva://'):
            archive_address = address.replace('pva://', 'archiver://pv=', 1)
        else:
            logger.error('Invalid address format for archiver appliance')
            return

        self.archive_channel = PyDMChannel(address=archive_address,
                                           value_slot=self.receiveArchiveData,
                                           value_signal=self.archive_data_request_signal)

    @Slot(np.ndarray)
    def receiveArchiveData(self, data):
        """ Receive data from archiver appliance and place it into the archive data buffer. """
        archive_data_length = len(data[0])
        min_x = data[0][0]
        max_x = data[0][archive_data_length-1]

        while max_x > self.data_buffer[0][-self.points_accumulated]:
            # Sometimes optimized queries return data past the current timestamp, this will delete those data points
            data = np.delete(data, len(data[0]) - 1, axis=1)
            archive_data_length -= 1
            max_x = data[0][archive_data_length-1]

        if self.zoomed and self.archive_points_accumulated != 0 and data.shape[0] == 2:
            # Zoomed means we drew a zoom box and shape of 2 means we got back raw data
            # Get the indices between which we want to insert the data
            min_insertion_index = np.searchsorted(self.archive_data_buffer[0], min_x)
            max_insertion_index = np.searchsorted(self.archive_data_buffer[0], max_x)
            print(f'Min insert is: {min_insertion_index} and max insert is: {max_insertion_index}')
            # Delete any non-raw data between the indices so we don't have multiple data points for the same timestamp
            self.archive_data_buffer = np.delete(self.archive_data_buffer, slice(min_insertion_index, max_insertion_index), axis=1)
            num_points_deleted = max_insertion_index - min_insertion_index
            delta_points = archive_data_length - num_points_deleted
            if archive_data_length > num_points_deleted:
                # If the insertion will overflow the data buffer, need to delete the oldest points
                self.archive_data_buffer = np.delete(self.archive_data_buffer, slice(0, delta_points), axis=1)
            else:
                self.archive_data_buffer = np.insert(self.archive_data_buffer, [0], np.zeros((2, delta_points)), axis=1)
            min_insertion_index = np.searchsorted(self.archive_data_buffer[0], min_x)
            self.archive_data_buffer = np.insert(self.archive_data_buffer, [min_insertion_index], data[0:2], axis=1)

            self.archive_points_accumulated += archive_data_length - num_points_deleted
            self.zoomed = False
        else:
            self.archive_data_buffer[0, len(self.archive_data_buffer[0]) - archive_data_length:] = data[0]
            self.archive_data_buffer[1, len(self.archive_data_buffer[0]) - archive_data_length:] = data[1]
            self.archive_points_accumulated = archive_data_length

            # Error bars
            if data.shape[0] == 5:  # 5 indicates optimized data was requested from the archiver
                self.error_bar_item.setData(x=self.archive_data_buffer[0, -self.archive_points_accumulated:],
                                            y=self.archive_data_buffer[1, -self.archive_points_accumulated:],
                                            top=data[4] - data[1],
                                            bottom=data[1] - data[3],
                                            beam=0.5,
                                            pen={'color': self.color})
                if self.error_bar_needs_set:
                    self.getViewBox().addItem(self.error_bar_item)
                    self.error_bar_needs_set = False

        self.data_changed.emit()

    @Slot()
    def redrawCurve(self):
        """
        Redraw the curve with the new data.
        """
        if self.archive_points_accumulated == 0:
            super(ArchivePlotCurveItem, self).redrawCurve()
        else:
            try:
                x = np.concatenate((self.archive_data_buffer[0, -self.archive_points_accumulated:].astype(np.float),
                                    self.data_buffer[0, -self.points_accumulated:].astype(np.float)))

                y = np.concatenate((self.archive_data_buffer[1, -self.archive_points_accumulated:].astype(np.float),
                                    self.data_buffer[1, -self.points_accumulated:].astype(np.float)))

                self.setData(y=y, x=x)
            except (ZeroDivisionError, OverflowError, TypeError):
                # Solve an issue with pyqtgraph and initial downsampling
                pass

    def initializeArchiveBuffer(self):
        """
        Initialize the archive data buffer used for this curve.
        """
        self.archive_points_accumulated = 0
        self.archive_data_buffer = np.zeros((2, self._archiveBufferSize), order='f', dtype=float)

    def getArchiveBufferSize(self):
        return int(self._archiveBufferSize)

    def setArchiveBufferSize(self, value):
        if self._archiveBufferSize != int(value):
            self._archiveBufferSize = max(int(value), 2)
            self.initializeArchiveBuffer()

    def resetArchiveBufferSize(self):
        if self._archiveBufferSize != DEFAULT_ARCHIVE_BUFFER_SIZE:
            self._archiveBufferSize = DEFAULT_ARCHIVE_BUFFER_SIZE
            self.initializeArchiveBuffer()

    def channels(self):
        return [self.channel, self.archive_channel]


class PyDMArchiverTimePlot(PyDMTimePlot):
    """
    PyDMArchiverTimePlot is a PyDMTimePlot with support for receiving data from
    the archiver appliance.

    Parameters
    ----------
    parent : optional
        The parent of this widget.
    init_y_channels : list
        A list of scalar channels to plot vs time.
    background: optional
        The background color for the plot.  Accepts any arguments that
        pyqtgraph.mkColor will accept.
    """

    def __init__(self, parent=None, init_y_channels=[], background='default'):
        super(PyDMArchiverTimePlot, self).__init__(parent=parent, init_y_channels=init_y_channels,
                                                   plot_by_timestamps=True, background=background)
        self._min_x = None
        self._to_timestamp = None
        self._bottom_axis = DateAxisItem('bottom')
        self.plotItem.setAxisItems({'bottom': self._bottom_axis})
        self.plotItem.getViewBox().sigMouseDraggedDone.connect(self.handleZoomEvent)

    def addYChannel(self, y_channel=None, name=None, color=None,
                    lineStyle=None, lineWidth=None, symbol=None,
                    symbolSize=None, yAxisName=None, useArchiveData=False):
        super(PyDMArchiverTimePlot, self).addYChannel(y_channel, name, color, lineStyle, lineWidth, symbol,
                                                      symbolSize, yAxisName, useArchiveData)

    def updateXAxis(self, update_immediately=False):
        if len(self._curves) == 0:
            return

        min_x = self.plotItem.getAxis('bottom').range[0]
        max_range = max([curve.max_x() for curve in self._curves])
        if min_x == 0:
            min_x = time.time()
            self._min_x = min_x
            self._most_recent_x = min_x
            self._to_timestamp = min_x
            self._to_timestamp -= 60
        elif min_x < self._min_x:
            time_requested = self._to_timestamp - min_x
            if time_requested >= 180:
                self.requestDataFromArchiver(min_x, self._to_timestamp)
                self._most_recent_x = min_x
                self._min_x = min_x

        if self.plotItem.getViewBox().state['autoRange'][1]:  # The way to check the pyqtgraph autorange setting
            self.plotItem.setXRange(min_x, max_range, padding=0.0, update=update_immediately)

    def requestDataFromArchiver(self, from_time, to_time):
        processing_command = ''
        requested_seconds = to_time - from_time
        max_data_request = int(0.10 * self.getArchiveBufferSize())  # Max amount of raw data to return before using optimized data
        if requested_seconds > max_data_request:
            processing_command = 'optimized_' + str(max_data_request)
        for curve in self._curves:
            curve.archive_data_request_signal.emit(from_time, to_time - 1, processing_command)

    def handleZoomEvent(self):
        min_x = self.plotItem.getAxis('bottom').range[0]
        max_x = self.plotItem.getAxis('bottom').range[1]

        if self._to_timestamp < max_x:
            return  # Don't fetch archive data when zooming in on live data

        for curve in self._curves:
            curve.zoomed = True

        if max_x - min_x < 86400:  # Only fetch raw data if not too many points were asked for
            self.requestDataFromArchiver(min_x, max_x)

    def getArchiveBufferSize(self):
        if len(self._curves) == 0:
            return DEFAULT_ARCHIVE_BUFFER_SIZE
        return self._curves[0].getArchiveBufferSize()

    def createCurveItem(self, y_channel, plot_by_timestamps, name, color, yAxisName, useArchiveData, **plot_opts):
        return ArchivePlotCurveItem(y_channel, plot_by_timestamps=plot_by_timestamps, name=name,
                                    color=color, yAxisName=yAxisName, use_archive_data=useArchiveData, **plot_opts)

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
        print(f'Setting curves the new way\n\n')
        try:
            new_list = [json.loads(str(i)) for i in new_list]
        except ValueError as e:
            logger.exception("Error parsing curve json data: {}".format(e))
            return
        self.clearCurves()
        print(f'new list is: {new_list}')
        for d in new_list:
            color = d.get('color')
            if color:
                color = QColor(color)
            self.addYChannel(d['channel'],
                             name=d.get('name'),
                             color=color,
                             lineStyle=d.get('lineStyle'),
                             lineWidth=d.get('lineWidth'),
                             symbol=d.get('symbol'),
                             symbolSize=d.get('symbolSize'),
                             yAxisName=d.get('yAxisName'),
                             useArchiveData=d.get('useArchiveData'))

    curves = Property("QStringList", getCurves, setCurves, designable=False)
