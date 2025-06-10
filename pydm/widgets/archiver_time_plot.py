import json
import re
import time
import numpy as np
import warnings
from collections import OrderedDict
from typing import List, Optional, Union
from pyqtgraph import DateAxisItem, ErrorBarItem, PlotCurveItem
from pydm.utilities import remove_protocol, is_qt_designer
from pydm.widgets.channel import PyDMChannel
from pydm.widgets.timeplot import TimePlotCurveItem
from pydm.widgets import PyDMTimePlot
from qtpy.QtCore import Qt, QObject, QTimer, Property, Signal, Slot
from qtpy.QtGui import QColor, QPen
import logging
from math import *  # noqa
from statistics import mean  # noqa

# We noqa those two because those functions/vars are useful in eval() but
# are never explicitly called by us, only in the background.
from pydm.widgets.baseplot import BasePlotCurveItem

logger = logging.getLogger(__name__)

DEFAULT_ARCHIVE_BUFFER_SIZE = 18000
DEFAULT_TIME_SPAN = 3600.0
MIN_TIME_SPAN = 5.0
APPROX_SECONDS_300_YEARS = 10000000000


class ArchivePlotCurveItem(TimePlotCurveItem):
    """
    ArchivePlotCurveItem is a TimePlotCurveItem with support for receiving data from
    the archiver appliance.

    Parameters
    ----------
    channel_address : str
        The address to of the scalar data to plot. Will also be used to retrieve data
        from archiver appliance if requested.
    use_archive_data : bool
        If True, requests will be made to archiver appliance for archived data when
        the plot is zoomed or scrolled to the left.
    liveData : bool
        If True, the curve will gather data in real time.
    show_extension_line : bool
        If True, shows a line that extends from the right-most point to the future.
        Defaults to False.
    **kws : dict[str: any]
        Additional parameters supported by pyqtgraph.PlotDataItem.
    """

    # Used to request data from archiver appliance (starting timestamp, ending timestamp, processing command)
    archive_data_request_signal = Signal(float, float, str)
    archive_data_received_signal = Signal()
    archive_channel_connection = Signal(bool)
    prompt_archive_request = Signal()

    def __init__(
        self,
        channel_address: Optional[str] = None,
        useArchiveData: bool = True,
        liveData: bool = True,
        showExtensionLine: bool = False,
        **kws,
    ):
        # Attributes that must exist before super().__init__() call
        self.archive_channel = None
        self.error_bar = ErrorBarItem()
        self._extension_line = PlotCurveItem()

        super().__init__(**kws)

        self.use_archive_data = useArchiveData
        self.archive_points_accumulated = 0
        self._archiveBufferSize = DEFAULT_ARCHIVE_BUFFER_SIZE
        self.archive_data_buffer = np.zeros((2, self._archiveBufferSize), order="f", dtype=float)
        self._liveData = liveData

        self._show_extension_line = showExtensionLine
        if not self._show_extension_line:
            self._extension_line.hide()

        self.error_bar_data = None

        self.destroyed.connect(lambda: self.remove_error_bar())
        self.destroyed.connect(lambda: self.remove_extenstion_line())
        self.address = channel_address

    def to_dict(self) -> OrderedDict:
        """Returns an OrderedDict representation with values for all properties needed to recreate this curve."""
        dic_ = OrderedDict(
            [
                ("useArchiveData", self.use_archive_data),
                ("liveData", self.liveData),
                ("showExtensionLine", self._show_extension_line),
            ]
        )
        dic_.update(super(ArchivePlotCurveItem, self).to_dict())
        return dic_

    @TimePlotCurveItem.address.setter
    def address(self, new_address: str) -> None:
        """Creates the channel for the input address for communicating with the archiver appliance plugin."""
        TimePlotCurveItem.address.fset(self, new_address)

        if self.archive_channel:
            if new_address == self.archive_channel.address:
                return
            self.archive_channel.disconnect()

        self.arch_connected = False
        if not new_address:
            self.archive_channel = None
            return

        # Prepare new address to use the archiver plugin and create the new channel
        archive_address = "archiver://pv=" + remove_protocol(new_address.strip())
        self.archive_channel = PyDMChannel(
            address=archive_address,
            value_slot=self.receiveArchiveData,
            value_signal=self.archive_data_request_signal,
            connection_slot=self.archiveConnectionStateChanged,
        )
        self.archive_channel.connect()

        # Clear the archive data of the previous channel and redraw the curve
        if self.archive_points_accumulated:
            self.initializeArchiveBuffer()
            self.redrawCurve()

        # Prompt the curve's associated plot to fetch archive data
        self.prompt_archive_request.emit()

    @BasePlotCurveItem.y_axis_name.setter
    def y_axis_name(self, axis_name: str) -> None:
        """
        Set the name of the y-axis that should be associated with this curve.
        Also move's the curve's error bar item and extension line.
        Parameters
        ----------
        axis_name: str
        """
        BasePlotCurveItem.y_axis_name.fset(self, axis_name)
        self.remove_error_bar()
        self.getViewBox().addItem(self.error_bar)

        self.remove_extenstion_line()
        self.getViewBox().addItem(self._extension_line)

    @BasePlotCurveItem.color.setter
    def color(self, new_color: Union[QColor, str]) -> None:
        """
        Set the name of the color of the curve and its parts.
        Parameters
        ----------
        new_color: QColor | str
        """
        BasePlotCurveItem.color.fset(self, new_color)
        self.refresh_extension_line_pen()
        self.refresh_error_bar_pen()

    @BasePlotCurveItem.lineWidth.setter
    def lineWidth(self, new_width: int) -> None:
        """
        Set the width of the line connecting the data points and the
        curve's extension line.

        Parameters
        -------
        new_width: int
        """
        BasePlotCurveItem.lineWidth.fset(self, new_width)
        self.refresh_extension_line_pen()

    @property
    def liveData(self):
        return self._liveData

    @liveData.setter
    def liveData(self, get_live: bool):
        if not get_live:
            self._liveData = False
            return

        min_x = self.data_buffer[0, self._bufferSize - 1]
        max_x = time.time()

        # Avoids noisy requests when first rendering the plot
        if max_x - min_x > 5:
            self.archive_data_request_signal.emit(min_x, max_x - 1, "")

        self._liveData = True

    @property
    def show_extension_line(self):
        return self._show_extension_line

    @show_extension_line.setter
    def show_extension_line(self, enable: bool):
        self._show_extension_line = enable
        if self._show_extension_line:
            self.set_extension_line_data()
            self._extension_line.show()
        else:
            self._extension_line.hide()

    @Slot(np.ndarray)
    def receiveArchiveData(self, data: np.ndarray) -> None:
        """Receive data from archiver appliance and place it into the archive data buffer.
        Will overwrite any previously existing data at the indices written to.

        Parameters
        ----------
        data : np.ndarray
            A numpy array of varying shape consisting of archived data for display.
            At a minimum, index 0 will contain the timestamps and index 1 the actual data observations.
            Additional indices may be used as well based on the type of request made to the archiver appliance.
            For example optimized data will include standard deviations, minimums, and maximums
        """
        archive_data_length = len(data[0])
        max_x = data[0][archive_data_length - 1]

        # Filling live buffer if data is more recent than Archive Data Buffer
        last_ts = self.archive_data_buffer[0][-1]
        if self.archive_data_buffer.any() and (int(last_ts) <= data[0][0]):
            self.insert_live_data(data)
            self.data_changed.emit()
            return

        if self.points_accumulated != 0:
            while max_x > self.data_buffer[0][-self.points_accumulated]:
                # Sometimes optimized queries return data past the current timestamp, this will delete those data points
                data = np.delete(data, len(data[0]) - 1, axis=1)
                archive_data_length -= 1
                max_x = data[0][archive_data_length - 1]

        self.archive_data_buffer[0, len(self.archive_data_buffer[0]) - archive_data_length :] = data[0]
        self.archive_data_buffer[1, len(self.archive_data_buffer[0]) - archive_data_length :] = data[1]
        self.archive_points_accumulated = archive_data_length

        # Error bars
        if data.shape[0] == 5:  # 5 indicates optimized data was requested from the archiver
            self.error_bar_data = data
            self.set_error_bar()
            self.error_bar.show()
        else:
            self.error_bar.hide()

        self.data_changed.emit()
        self.archive_data_received_signal.emit()

    def insert_archive_data(self, data: np.ndarray) -> None:
        """
        Inserts data directly into the archive buffer.

        An example use case would be zooming into optimized mean-value data and
        replacing it with the raw data.

        Parameters
        ----------
        data : np.ndarray
           A numpy array of shape (2, length_of_data). Index 0 contains
           timestamps and index 1 contains the data observations.
        """
        archive_data_length = len(data[0])
        min_x = data[0][0]
        max_x = data[0][archive_data_length - 1]
        # Get the indices between which we want to insert the data
        min_insertion_index = np.searchsorted(self.archive_data_buffer[0], min_x)
        max_insertion_index = np.searchsorted(self.archive_data_buffer[0], max_x)
        # Delete any non-raw data between the indices so we don't have multiple data points for the same timestamp
        self.archive_data_buffer = np.delete(
            self.archive_data_buffer, slice(min_insertion_index, max_insertion_index), axis=1
        )
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

    @Slot()
    def redrawCurve(self, min_x=None, max_x=None) -> None:
        """
        Redraw the curve with any new data added since the last draw call.
        """
        if self.archive_points_accumulated == 0:
            super().redrawCurve()
        else:
            try:
                x = np.concatenate(
                    (
                        self.archive_data_buffer[0, -self.archive_points_accumulated :].astype(float),
                        self.data_buffer[0, -self.points_accumulated :].astype(float),
                    )
                )

                y = np.concatenate(
                    (
                        self.archive_data_buffer[1, -self.archive_points_accumulated :].astype(float),
                        self.data_buffer[1, -self.points_accumulated :].astype(float),
                    )
                )

                self.setData(y=y, x=x)

            except (ZeroDivisionError, OverflowError, TypeError):
                # Solve an issue with pyqtgraph and initial downsampling
                pass

        if self._show_extension_line:
            self.set_extension_line_data()

    def set_extension_line_data(self) -> None:
        """
        Creates a dotted line from the latest point in the buffer
        (live or archived depending on if live data is active).
        """
        if self._liveData:
            if self.data_buffer.size == 0:
                return
            x_last = self.data_buffer[:, -1]
            y_last = self.data_buffer[:, -1]
        else:
            if self.archive_data_buffer.size == 0:
                return
            x_last = self.archive_data_buffer[:, -1]
            y_last = self.archive_data_buffer[:, -1]

        x_infinity = x_last[0] + APPROX_SECONDS_300_YEARS

        x_line = np.array([x_last[0], x_infinity])
        y_line = np.array([y_last[1], y_last[1]])
        self._extension_line.setData(x=x_line, y=y_line)

    @Slot()
    def remove_extenstion_line(self):
        """Remove the curve's error bar when the curve is deleted."""
        if self._extension_line is None:
            return
        if vb := self._extension_line.getViewBox():
            vb.removeItem(self._extension_line)

    def refresh_extension_line_pen(self) -> None:
        dotted_pen = QPen(self._pen)
        dotted_pen.setStyle(Qt.DotLine)
        self._extension_line.setPen(dotted_pen)

    def initializeArchiveBuffer(self) -> None:
        """
        Initialize the archive data buffer used for this curve.
        """
        self.archive_points_accumulated = 0
        self.archive_data_buffer = np.zeros((2, self._archiveBufferSize), order="f", dtype=float)

    def getArchiveBufferSize(self) -> int:
        """Return the length of the archive buffer"""
        return int(self._archiveBufferSize)

    def setArchiveBufferSize(self, value: int) -> None:
        """Set the length of the archive data buffer and zero it out"""
        if self._archiveBufferSize != int(value):
            self._archiveBufferSize = max(int(value), 2)
            self.initializeArchiveBuffer()

    def resetArchiveBufferSize(self) -> None:
        """Reset the length of the archive buffer back to the default and zero it out"""
        if self._archiveBufferSize != DEFAULT_ARCHIVE_BUFFER_SIZE:
            self._archiveBufferSize = DEFAULT_ARCHIVE_BUFFER_SIZE
            self.initializeArchiveBuffer()

    def set_error_bar(self):
        """Update the data in the ErrorBarItem. Applies log10 to the ErrorBarItem
        based on the curve's log mode.
        """
        x_val = self.error_bar_data[0]

        if self.error_bar.getViewBox() is None:
            self.getViewBox().addItem(self.error_bar)

        # Calculate y-value and range for error bars
        logMode = self.opts["logMode"][1]
        if logMode:
            # If the curve's log mode is enabled, then apply numpy.log10 to all y-values
            with np.errstate(divide="ignore"):
                y_val = np.log10(self.error_bar_data[1])
                bot_val = y_val - np.log10(self.error_bar_data[3])
                top_val = np.log10(self.error_bar_data[4]) - y_val
        else:
            y_val = self.error_bar_data[1]
            bot_val = y_val - self.error_bar_data[3]
            top_val = self.error_bar_data[4] - y_val

        self.error_bar.setData(x=x_val, y=y_val, top=top_val, bottom=bot_val, beam=0.5)

    @Slot()
    def remove_error_bar(self):
        """Remove the curve's error bar when the curve is deleted."""
        if self.error_bar is None:
            return
        if vb := self.error_bar.getViewBox():
            vb.removeItem(self.error_bar)

    def refresh_error_bar_pen(self) -> None:
        solid_pen = QPen(self._pen)
        solid_pen.setStyle(Qt.SolidLine)
        self.error_bar.setData(pen=solid_pen)

    def setLogMode(self, xState: bool, yState: bool) -> None:
        """When log mode is enabled for the respective axis by setting xState or
        yState to True, a mapping according to mapped = np.log10( value ) is applied
        to the data. For negative or zero values, this results in a NaN value.

        Parameters
        ----------
        xState : bool
            Set log mode for the x-axis
        yState : bool
            Set log mode for the y-axis
        """
        super().setLogMode(xState, yState)
        if self.error_bar_data is not None:
            self.set_error_bar()

    @Slot(bool)
    def archiveConnectionStateChanged(self, connected: bool) -> None:
        """Capture the archive channel connection status and emit changes

        Parameters
        ----------
        connected : bool
            The new connection status of the archive channel
        """
        self.arch_connected = connected
        self.archive_channel_connection.emit(connected)

    def channels(self) -> List[PyDMChannel]:
        """Return the list of channels this curve is connected to"""
        return [self.channel, self.archive_channel]

    def min_archiver_x(self):
        """
        Provide the the oldest valid timestamp from the archiver data buffer.

        Returns
        -------
        float
            The timestamp of the oldest data point in the archiver data buffer.
        """
        if self.archive_points_accumulated:
            return self.archive_data_buffer[0, -self.archive_points_accumulated]
        else:
            return self.min_x()

    def max_archiver_x(self):
        """
        Provide the the most recent timestamp from the archiver data buffer.
        This is useful for scaling the x-axis.

        Returns
        -------
        float
            The timestamp of the most recent data point in the archiver data buffer.
        """
        if self.archive_points_accumulated:
            return self.archive_data_buffer[0, -1]
        else:
            return self.min_x()

    def receiveNewValue(self, new_value: float) -> None:
        """Fill incoming live data if requested by user.

        Parameters
        ----------
        new_value : float
            The new y-value to append to the live data buffer
        """
        # Ignore incoming live data depending on user request
        if self._liveData:
            super().receiveNewValue(new_value)

    def setVisible(self, visible: bool) -> None:
        """Propagate visibility changes to extension line and error bar."""
        super().setVisible(visible)
        self._extension_line.setVisible(visible)
        self.error_bar.setVisible(visible)

    def hide(self):
        """Propagate visibility changes to extension line and error bar."""
        super().hide()
        self._extension_line.hide()
        self.error_bar.hide()

    def show(self):
        """Propagate visibility changes to extension line and error bar."""
        super().show()
        self._extension_line.show()
        self.error_bar.show()


class FormulaCurveItem(BasePlotCurveItem):
    """
    FormulaCurveItem is a BasePlotCurve that takes in a formula of curves and evaluates to graph a function.

    To use, instead of typing in a PV channel, this takes in the prefix 'f://' to indicate a function, then
    uses curly braces '{<PV row header>}' to find which curves to use as inputs. Other than that, FormulaCurveItems
    have the capacity to handle basic arithmetic functions and also special functions like log() and trigonometry.

    Finally, when populating its data buffers, it uses the union of the timesteps for each of its input curves, and uses
    last seen data to fill in the gaps when calculating.

    Parameters
    ----------
    formula : str
        The formula that we are graphing
    use_archive_data : bool
        If True, requests will be made to archiver appliance for archived data when
        the plot is zoomed or scrolled to the left.
    pvs: dict[str: BasePlotCurveItem]
        Has all the information for our FormulaCurveItem to evaluate the value at every timestep
    **kws : dict[str: any]
        Additional parameters supported by pyqtgraph.PlotDataItem.
    """

    _channels = ("channel",)
    archive_data_request_signal = Signal(float, float, str)
    archive_data_received_signal = Signal()
    live_channel_connection = Signal(bool)
    archive_channel_connection = Signal(bool)
    formula_invalid_signal = Signal()

    def __init__(
        self,
        formula: str = None,
        pvs: dict = None,
        use_archive_data: Optional[bool] = True,
        liveData: Optional[bool] = True,
        color: Optional[str] = "green",
        plot_style: str = "Line",
        **kws,
    ):
        super(FormulaCurveItem, self).__init__(**kws)
        self.color = color
        self.use_archive_data = use_archive_data
        self.points_accumulated = 0
        self.archive_points_accumulated = 0
        # Start with empty buffers because we don't
        # calculate anything until we try to draw the curve
        self._archiveBufferSize = DEFAULT_ARCHIVE_BUFFER_SIZE
        self._bufferSize = 0
        self.archive_data_buffer = np.zeros((2, 0), order="f", dtype=float)

        self.data_buffer = np.zeros((2, 0), order="f", dtype=float)

        # Have a formula for internal calculations, that the user does not see
        self._formula = formula
        self._trueFormula = self.createTrueFormula()
        self.pvs = pvs if pvs else {}
        self._liveData = liveData
        self.plot_style = plot_style

        self.connected, self.arch_connected = None, None
        self.live_connections, self.arch_connections = {}, {}

        for curve in self.pvs.values():
            self.live_connections[curve] = curve.connected
            self.arch_connections[curve] = curve.arch_connected

            curve.live_channel_connection.connect(self.live_conn_change)
            curve.archive_channel_connection.connect(self.arch_conn_change)

            if hasattr(curve, "archive_data_received_signal"):
                curve.archive_data_received_signal.connect(self.on_dependency_archive_data_received)

            if hasattr(curve, "data_changed"):
                curve.data_changed.connect(self.on_dependency_data_changed)

        self.connection_status_check()
        QTimer.singleShot(100, self.initial_evaluation)

    def initial_evaluation(self):
        """Perform initial evaluation after dependencies are set up"""
        self.evaluate()
        self.redrawCurve()

    def to_dict(self) -> OrderedDict:
        """Returns an OrderedDict representation with values for all properties needed to recreate this curve."""
        dic_ = OrderedDict(
            [
                ("useArchiveData", self.use_archive_data),
                ("liveData", self.liveData),
                ("plot_style", self.plot_style),
                ("formula", self.formula),
            ]
        )
        curveDict = dict()
        for header, curve in self.pvs.items():
            if isinstance(curve, ArchivePlotCurveItem):
                curveDict[header] = curve.address
            else:
                curveDict[header] = curve.formula
        dic_.update({"curveDict": curveDict})
        dic_.update(super().to_dict())
        return dic_

    @property
    def liveData(self):
        for pv in self.pvs.keys():
            if not self.pvs[pv].liveData:
                return False
        return True

    @liveData.setter
    def liveData(self, get_live: bool):
        if not get_live:
            self._liveData = False
            return
        self._liveData = True

    @property
    def formula(self):
        return self._formula

    @formula.setter
    def formula(self, formula: str):
        self._formula = formula
        self._trueFormula = self.createTrueFormula()

    @property
    def channel(self):
        return None

    def checkFormula(self) -> bool:
        """Make sure that our formula is still valid.
        Namely, all of the input curves need to still exist in the viewer"""
        for pv in self.pvs.keys():
            if not self.pvs[pv].exists:
                logger.warning(pv + " is no longer a valid row name")
                # If one of the rows we rely on is gone, not only are we no longer a valid formula,
                # but all rows that rely on us are also invalid.
                self.exists = False
                return False
        return True

    def createTrueFormula(self) -> str:
        """Convert our human-readable formula to something easier to use for the computer, in the background only"""
        prefix = "f://"
        if not self.formula.startswith(prefix):
            logger.warning("Invalid Formula")
            return None
        formula = self.formula[len(prefix) :]
        # custom function to clean up the formula. First thing replace rows with data entries
        formula = re.sub(r"{(.+?)}", r'pvValues["\g<1>"]', formula)
        formula = re.sub(r"\^", r"**", formula)
        formula = re.sub(r"mean\((.+?)\)", r"mean([\g<1>])", formula)
        # mean() requires a list of values, so just put brackets around the item
        formula = re.sub(r"ln\((.+?)\)", r"log(\g<1>)", formula)
        # ln is more intuitive than log
        return formula

    @Slot(np.ndarray)
    def evaluate(self) -> None:
        """
        Use our formula and input curves to calculate our value at each timestep.
        If one curve updates at a certain timestep and another does not, it uses the previously
        seen data of the second curve, and assumes it is accurate at the current timestep.
        """
        formula = self._trueFormula
        if not formula or not self.checkFormula():
            logger.error("invalid formula")
            self.formula_invalid_signal.emit()
            return
        if not self.pvs:
            # If we are just a constant, then store a straight line from 1970 to ~2200
            # Known Bug: Constants are hidden if the plot's x-axis range is between 30m and 1.5hr
            self.archive_data_buffer = np.array([[0], [eval(self._trueFormula)]])
            self.data_buffer = np.array([[APPROX_SECONDS_300_YEARS], [eval(self._trueFormula)]])
            self.points_accumulated = self.archive_points_accumulated = 1
            return

        if not (self.connected or self.arch_connected):
            return

        pvArchiveData = dict()
        pvLiveData = dict()
        pvIndices = dict()
        pvValues = dict()

        self.archive_data_buffer = np.zeros((2, 0), order="f", dtype=float)
        self.data_buffer = np.zeros((2, 0), order="f", dtype=float)
        # Reset buffers
        self.points_accumulated = 0
        self.archive_points_accumulated = 0
        # Populate new dictionaries, simply for ease of access and readability
        pvIndices = self.set_up_eval(archive=True)
        for pv in self.pvs.keys():
            pvArchiveData[pv] = self.pvs[pv].archive_data_buffer
            pvValues[pv] = pvArchiveData[pv][1][pvIndices[pv] - 1]

        self.archive_data_buffer = self.compute_evaluation(
            formula=formula, pvData=pvArchiveData, pvValues=pvValues, pvIndices=pvIndices, archive=True
        )
        if self.liveData:
            self.points_accumulated = 0
            pvIndices = self.set_up_eval(archive=False)
            pvValues = dict()
            # Do literally the exact same thing for live data
            for pv in self.pvs.keys():
                pvLiveData[pv] = self.pvs[pv].data_buffer
                pvValues[pv] = pvLiveData[pv][1][pvIndices[pv] - 1]
            self.data_buffer = self.compute_evaluation(
                formula=formula, pvData=pvLiveData, pvValues=pvValues, pvIndices=pvIndices, archive=False
            )

    def set_up_eval(self, archive: bool) -> dict:
        """Because we are doing very similar evaluations for Archive and Live Data,
        we are going to set up our data structures such that we can compute our evaluation
        more easily. This function will (generally) be called twice, once with archive = True,
        once with False

        Parameters
        ----------------
        archive: bool
            Whether this is setting up for Archive Data or Live Data"""
        pvIndices = dict()
        for pv in self.pvs.keys():
            pv_current_index = 0
            if archive:
                pv_times = self.pvs[pv].archive_data_buffer[0]
                while pv_current_index < len(pv_times) - 1 and pv_times[pv_current_index] < self.min_archiver_x():
                    pv_current_index += 1
                # Shift starting indices for each row to our minimum
            else:
                pv_times = self.pvs[pv].data_buffer[0]
                while pv_current_index < len(pv_times) - 1 and pv_times[pv_current_index] < self.min_x():
                    pv_current_index += 1
            pvIndices[pv] = pv_current_index
        return pvIndices

    def compute_evaluation(
        self, formula: str, pvData: dict, pvValues: dict, pvIndices: dict, archive: bool
    ) -> np.ndarray:
        """This is where the actual computation takes place. We are going to go through
        the data step by step and calculate our formula at each timestamp available.

        Parameters
        ----------
        formula: str
            The formula to compute
        pvData: dict
            A dictionary containing all of the Archive or Live data for each curve
        pvValues: dict
            The value of each curve at the current timestep. At the start of this function,
            each is set to their respective last seen values when the time is equal to the
            latest start time of all of the curves.
        pvIndices: dict
            A dictionary storing where in each curve's data buffer we are currently at while calculating
        archive: bool
            Whether or not this is computing for the Archive or for Live

        Returns
        -------
        output: np.ndarray
            formula curve data
        """

        output = np.zeros((2, 0), order="f", dtype=float)

        while True:
            if archive:
                self.archive_points_accumulated += 1
            else:
                self.points_accumulated += 1

            minPV = None
            current_time = 0
            min_pv_current_index = 0

            for pv in self.pvs.keys():
                pv_times = pvData[pv][0]
                pv_current_index = pvIndices[pv]

                if pv_current_index >= len(pv_times):
                    continue

                if minPV is None or pv_times[pv_current_index] < current_time:
                    minPV = pv
                    current_time = pv_times[pv_current_index]
                    min_pv_current_index = pv_current_index

            if minPV is None:
                break

            pvValues[minPV] = pvData[minPV][1][min_pv_current_index]

            try:
                formula_value = eval(formula)
            except (ValueError, ZeroDivisionError, OverflowError):
                logger.warning("Formula evaluation failed")
                formula_value = 0

            temp = np.array([[current_time], [formula_value]])
            output = np.append(output, temp, axis=1)

            pvIndices[minPV] += 1

            if pvIndices[minPV] >= len(pvData[minPV][0]):
                break

        return output

    @Slot()
    def redrawCurve(self, min_x=None, max_x=None) -> None:
        """Redraw the curve with any new data added since the last draw call."""
        self.evaluate()
        try:
            archive_x = self.archive_data_buffer[0, -self.archive_points_accumulated :].astype(float)
            archive_y = self.archive_data_buffer[1, -self.archive_points_accumulated :].astype(float)
            live_x = self.data_buffer[0, -self.points_accumulated :].astype(float)
            live_y = self.data_buffer[1, -self.points_accumulated :].astype(float)

            x = np.concatenate((archive_x, live_x))
            y = np.concatenate((archive_y, live_y))

            if len(x) > 0:
                valid_mask = x > 0
                x = x[valid_mask]
                y = y[valid_mask]

                # Remove near-duplicate timestamps
                if len(x) > 1:
                    sort_indices = np.argsort(x)
                    x_sorted = x[sort_indices]
                    y_sorted = y[sort_indices]

                    x_diff = np.diff(x_sorted)
                    significant_diff = np.concatenate(([True], x_diff > 0.001))

                    x = x_sorted[significant_diff]
                    y = y_sorted[significant_diff]

            self.setData(y=y, x=x)
        except (ZeroDivisionError, OverflowError, TypeError):
            pass

    def connection_status_check(self):
        """Check the connection status of all live and archive curves. Save and
        emit any changes.
        """
        connected = all(self.live_connections.values())
        self.connected = connected
        self.live_channel_connection.emit(self.connected)

        connected = all(self.arch_connections.values())
        self.arch_connected = connected
        self.archive_channel_connection.emit(self.arch_connected)

    @Slot(bool)
    def live_conn_change(self, status: bool) -> None:
        """Capture the live channel connection status of a given curve and
        check connection status

        Parameters
        ----------
        status : bool
            Live connection status for a given curve
        """
        curve = self.sender()
        self.live_connections[curve] = status
        self.connection_status_check()

    @Slot(bool)
    def arch_conn_change(self, status: bool) -> None:
        """Capture the archive channel connection status of a given curve and
        check connection status

        Parameters
        ----------
        status : bool
            Archive connection status for a given curve
        """
        curve = self.sender()
        self.arch_connections[curve] = status
        self.connection_status_check()

    @Slot()
    def on_dependency_archive_data_received(self):
        """Called when any dependency curve receives new archive data"""

        if self.use_archive_data and self.pvs:
            # Use a timer to batch updates if multiple dependencies update at once
            if not hasattr(self, "_update_timer"):
                self._update_timer = QTimer()
                self._update_timer.timeout.connect(self._delayed_update)
                self._update_timer.setSingleShot(True)

            self._update_timer.stop()
            self._update_timer.start(50)  # 50ms delay to batch updates

    @Slot()
    def on_dependency_data_changed(self):
        """Called when any dependency curve's data changes (live or archive)"""
        if self.pvs:
            if not hasattr(self, "_update_timer"):
                self._update_timer = QTimer()
                self._update_timer.timeout.connect(self._delayed_update)
                self._update_timer.setSingleShot(True)

            self._update_timer.stop()
            self._update_timer.start(50)

    def _delayed_update(self):
        """Perform the actual update after batching signals"""
        self.evaluate()
        self.redrawCurve()
        # Emit our own archive data received signal to propagate to dependent formulas
        if self.archive_points_accumulated > 0:
            self.archive_data_received_signal.emit()

    def getBufferSize(self):
        return self._bufferSize

    def initializeArchiveBuffer(self) -> None:
        """
        Initialize the archive data buffer used for this curve.
        """
        self.archive_data_buffer = np.zeros((2, self._archiveBufferSize), order="f", dtype=float)

    def getArchiveBufferSize(self) -> int:
        """Return the length of the archive buffer"""
        return int(self._archiveBufferSize)

    def setArchiveBufferSize(self, value: int) -> None:
        """Set the length of the archive data buffer and zero it out"""
        if self._archiveBufferSize != int(value):
            self._archiveBufferSize = max(int(value), 2)
            self.initializeArchiveBuffer()

    def resetArchiveBufferSize(self) -> None:
        """Reset the length of the archive buffer back to the default and zero it out"""
        if self._archiveBufferSize != DEFAULT_ARCHIVE_BUFFER_SIZE:
            self._archiveBufferSize = DEFAULT_ARCHIVE_BUFFER_SIZE
            self.initializeArchiveBuffer()

    def max_x(self):
        if not self.pvs:
            # We don't want our constants to affect the x axis at all, let them draw as required
            return 0
        maxx = APPROX_SECONDS_300_YEARS
        for curve in self.pvs.keys():
            maxx = min(self.pvs[curve].min_x(), maxx)
        return maxx

    def min_x(self):
        if not self.pvs:
            return APPROX_SECONDS_300_YEARS
        minx = 0
        for curve in self.pvs.keys():
            minx = max(self.pvs[curve].min_x(), minx)
        return minx

    def min_archiver_x(self):
        """
        Provide the the oldest valid timestamp from the archiver data buffer.

        Returns
        -------
        float
            The timestamp of the oldest data point in the archiver data buffer.
        """
        if not self.pvs:
            return APPROX_SECONDS_300_YEARS
        minx = 0
        for curve in self.pvs.keys():
            minx = max(self.pvs[curve].min_archiver_x(), minx)
        return minx

    def max_archiver_x(self):
        """
        Provide the the most recent timestamp from the archiver data buffer.
        This is useful for scaling the x-axis.

        Returns
        -------
        float
            The timestamp of the most recent data point in the archiver data buffer.
        """
        if not self.pvs:
            return 0
        maxx = APPROX_SECONDS_300_YEARS
        for curve in self.pvs.keys():
            maxx = min(self.pvs[curve].min_archiver_x(), maxx)
        return maxx

    def channels(self):
        return [self.channel]


class PyDMArchiverTimePlot(PyDMTimePlot):
    """
    PyDMArchiverTimePlot is a PyDMTimePlot with support for receiving data from
    the archiver appliance.

    Parameters
    ----------
    parent : QObject, optional
        The parent of this widget.
    init_y_channels : list
        A list of scalar channels to plot vs time.
    background : str
        The background color for the plot.  Accepts any arguments that
        pyqtgraph.mkColor will accept.
    optimized_data_bins : int
        The number of bins of data returned from the archiver when using optimized requests
    request_cooldown : int
        The time, in milliseconds, between requests to the archiver appliance
    cache_data : bool
        Whether curves should retain archive data or fetch new data when the x-axis changes
    show_all : bool
        Shifts the x-axis range to show all data, or stay where the user set the x-axis to
    show_extension_lines : bool
        Show a line extending from the right most point for all curves, defaults to False
    """

    def __init__(
        self,
        parent: Optional[QObject] = None,
        init_y_channels: List[str] = [],
        background: str = "default",
        optimized_data_bins: int = 2000,
        request_cooldown: int = 1000,
        cache_data: bool = True,
        show_all: bool = True,
        show_extension_lines: bool = False,
    ):
        super().__init__(
            parent=parent,
            init_y_channels=init_y_channels,
            plot_by_timestamps=True,
            background=background,
            bottom_axis=DateAxisItem("bottom"),
        )
        self._cache_data = None

        self.optimized_data_bins = optimized_data_bins
        self.request_cooldown = request_cooldown
        self.cache_data = cache_data
        self._show_all = show_all  # Show all plotted data after archiver fetch
        self._show_extension_lines = show_extension_lines

        self._starting_timestamp = time.time()  # The timestamp at which the plot was first rendered
        self._min_x = self._starting_timestamp - DEFAULT_TIME_SPAN
        self._prev_x = self._min_x  # Holds the minimum x-value of the previous update of the plot
        self._archive_request_queued = False
        self.setTimeSpan(DEFAULT_TIME_SPAN)

    @property
    def cache_data(self):
        """Returns if the curves of the plot are caching archive data or
        fetching new archive data on every change to the x-axis"""
        return self._cache_data

    @cache_data.setter
    def cache_data(self, enable: bool):
        """If true, the curves on the plot will keep their most recently fetched archive data. New
        data will only be fetched when users navigate to an "unseen" section of the plot.
        When false, the curves will fetch new archive data on every change to the x-axis.
        """
        if self._cache_data == enable:
            return
        if enable:
            try:
                # Catch the warnings when sigXRangeChanged and sigXRangeChangedManually were not connected yet.
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=RuntimeWarning)
                    self.plotItem.sigXRangeChanged.disconnect(self.updateXAxis)
                    self.plotItem.sigXRangeChangedManually.disconnect(self.updateXAxis)
            except TypeError:
                pass
        else:
            self.plotItem.sigXRangeChanged.connect(self.updateXAxis)
            self.plotItem.sigXRangeChangedManually.connect(self.updateXAxis)
        self._cache_data = enable

    @property
    def show_extension_lines(self):
        return self._show_extension_lines

    @show_extension_lines.setter
    def show_extension_lines(self, enable: bool):
        self._show_extension_lines = enable
        for curve in self._curves:
            curve.show_extension_line = enable

    def updateXAxis(self, update_immediately: bool = False) -> None:
        """Manages the requests to archiver appliance. When the user pans or zooms the x axis to the left,
        a request will be made for backfill data"""
        if not self._curves:
            return

        min_x, max_x = self.plotItem.getAxis("bottom").range  # Get current visible x-axis range
        if min_x == 0:  # Initial render case
            self._initialize_x_axis()
        elif not self._cache_data:
            self._handle_caching_off(min_x, max_x)
        elif not self.plotItem.isAnyXAutoRange():
            self._handle_manual_scrolling_or_zoom(min_x, max_x, update_immediately)

        self._prev_x = min_x

    def _initialize_x_axis(self) -> None:
        """Initializes the x-axis for the first render."""
        self._max_x = time.time()
        self._min_x = self._max_x - DEFAULT_TIME_SPAN
        self._starting_timestamp = self._max_x

        if self.getTimeSpan() != MIN_TIME_SPAN:
            self._min_x -= self.getTimeSpan()
            self._archive_request_queued = True
            self.requestDataFromArchiver()

        blocked = self.plotItem.blockSignals(True)
        self.plotItem.setXRange(self._min_x, self._max_x, padding=0.0, update=False)
        self.plotItem.blockSignals(blocked)

    def _handle_caching_off(self, min_x: float, max_x: float) -> None:
        """Handles the situation when there is no cached data and the user has changed the x-axis range."""
        if min_x != self._min_x or max_x != self._max_x:
            self._min_x = min_x
            self._max_x = max_x
            self.setTimeSpan(max_x - min_x)
            if not self._archive_request_queued:
                self._archive_request_queued = True
                QTimer.singleShot(self.request_cooldown, self.requestDataFromArchiver)

    def _handle_manual_scrolling_or_zoom(self, min_x: float, max_x: float, update_immediately: bool = False) -> None:
        """Handles scenarios of manual scrolling or zooming when autorange is disabled."""
        max_point = max(curve.max_x() for curve in self._curves)

        if min_x < self._min_x:
            # User scrolled to the left, request archived data
            self._min_x = min_x
            self.setTimeSpan(max_point - min_x)
            if not self._archive_request_queued:
                self._archive_request_queued = True
                QTimer.singleShot(self.request_cooldown, self.requestDataFromArchiver)
        elif max_x >= max_point - 10:
            # Check if we should update the x-axis
            if abs(min_x - self._prev_x) > 15:
                self.setTimeSpan(max_point - min_x)
            else:
                blocked = self.plotItem.blockSignals(True)
                self.plotItem.setXRange(
                    max_point - self.getTimeSpan(), max_point, padding=0.0, update=update_immediately
                )
                self.plotItem.blockSignals(blocked)

    def requestDataFromArchiver(self, min_x: Optional[float] = None, max_x: Optional[float] = None) -> None:
        """
        Make the request to the archiver appliance data plugin for archived data.

        Parameters
        ----------
        min_x : float, optional
           Timestamp representing the start of the time period to fetch archive data from. Defaults
           to the minimum value visible on the plot when omitted.
        max_x : float, optional
           Timestamp representing the end of the time period to fetch archive data from. Defaults
           to the timestamp of the oldest live data point in the buffer if available. If no live points are
           recorded yet, then defaults to the timestamp at which the plot was first rendered.
        """
        req_queued = False
        requested_max = max_x
        if min_x is None:
            min_x = self._min_x
        for curve in self._curves:
            processing_command = ""
            if curve.use_archive_data:
                if requested_max is None:  # If the caller didn't request a max, use the oldest data from the curve
                    max_x = curve.min_x()
                if not self._cache_data:
                    max_x = min(max_x, self._max_x)
                requested_seconds = max_x - min_x
                if requested_seconds <= MIN_TIME_SPAN:
                    continue  # Avoids noisy requests when first rendering the plot
                # Max amount of raw data to return before using optimized data
                max_data_request = int(0.80 * self.getArchiveBufferSize())
                if requested_seconds > max_data_request:
                    processing_command = "optimized_" + str(self.optimized_data_bins)
                curve.archive_data_request_signal.emit(min_x, max_x - 1, processing_command)
                req_queued |= True

        if not req_queued:
            self._archive_request_queued = False

    def setAutoScroll(self, enable: bool = False, timespan: float = 60, padding: float = 0.1, refresh_rate: int = 5000):
        """Enable/Disable autoscrolling along the x-axis. This will (un)pause
        the autoscrolling QTimer, which calls the auto_scroll slot when time is up.

        Parameters
        ----------
        enable : bool, optional
            Whether or not to start the autoscroll QTimer, by default False
        timespan : float, optional
            The timespan to set for autoscrolling along the x-axis in seconds, by default 60
        padding : float, optional
            The size of the empty space between the data and the sides of the plot, by default 0.1
        refresh_rate : int, optional
            How often the scroll should occur in milliseconds, by default 5000
        """
        super().setAutoScroll(enable, timespan, padding, refresh_rate)

        self._min_x = min(self._min_x, self.getViewBox().viewRange()[0][0])
        if self._min_x != self._prev_x:
            self.requestDataFromArchiver()
            self._prev_x = self._min_x

    def getArchiveBufferSize(self) -> int:
        """Returns the size of the data buffer used to store archived data"""
        if len(self._curves) == 0:
            return DEFAULT_ARCHIVE_BUFFER_SIZE
        return self._curves[0].getArchiveBufferSize()

    def createCurveItem(self, *args, **kwargs) -> ArchivePlotCurveItem:
        """Create and return a curve item to be plotted"""
        curve_item = ArchivePlotCurveItem(*args, **kwargs)
        curve_item.archive_data_received_signal.connect(self.archive_data_received)
        curve_item.prompt_archive_request.connect(self.requestDataFromArchiver)
        return curve_item

    @Slot()
    def archive_data_received(self):
        """Take any action needed when this plot receives new data from archiver appliance"""
        self._archive_request_queued = False
        if self.auto_scroll_timer.isActive() or not self._show_all:
            return

        max_x = max([curve.max_x() for curve in self._curves])
        # Assure the user sees all data available whenever the request data is returned
        self.plotItem.setXRange(max_x - self.getTimeSpan(), max_x, padding=0.0, update=True)

    def setTimeSpan(self, value):
        """Set the value of the plot's timespan"""
        if value < MIN_TIME_SPAN:  # Less than 5 seconds will break the plot
            return
        self._time_span = value

    def clearCurves(self) -> None:
        """Clear all curves from the plot"""
        for curve in self._curves:
            # Need to clear out any bars from optimized data; only applicable to ArchivePlotCurveItems
            if not isinstance(curve, ArchivePlotCurveItem):
                continue
            curve.remove_error_bar()

        # reset _min_x to let updateXAxis make requests anew
        self._min_x = self._starting_timestamp
        super().clearCurves()

    def getCurves(self) -> List[str]:
        """
        Dump and return the current list of curves and each curve's settings into a list
        of JSON-formatted strings.
        """
        return [json.dumps(curve.to_dict()) for curve in self._curves]

    def setCurves(self, new_list: List[str]) -> None:
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
        except ValueError as error:
            logger.exception("Error parsing curve json data: {}".format(error))
            return
        self.clearCurves()
        for d in new_list:
            color = d.get("color")
            if color:
                color = QColor(color)
            self.addYChannel(
                d["channel"],
                name=d.get("name"),
                color=color,
                lineStyle=d.get("lineStyle"),
                lineWidth=d.get("lineWidth"),
                symbol=d.get("symbol"),
                symbolSize=d.get("symbolSize"),
                yAxisName=d.get("yAxisName"),
                useArchiveData=d.get("useArchiveData"),
                liveData=d.get("liveData"),
            )

    curves = Property("QStringList", getCurves, setCurves, designable=False)

    def addYChannel(
        self,
        y_channel=None,
        plot_style=None,
        name=None,
        color=None,
        lineStyle=None,
        lineWidth=None,
        symbol=None,
        symbolSize=None,
        barWidth=None,
        upperThreshold=None,
        lowerThreshold=None,
        thresholdColor=None,
        yAxisName=None,
        useArchiveData=True,
        liveData=True,
        showExtensionLine=None,
    ) -> ArchivePlotCurveItem:
        """
        Overrides timeplot addYChannel method to be able to pass the liveData flag.
        """
        if showExtensionLine is None:
            showExtensionLine = self._show_extension_lines

        curve = super().addYChannel(
            y_channel=y_channel,
            plot_style=plot_style,
            name=name,
            color=color,
            lineStyle=lineStyle,
            lineWidth=lineWidth,
            symbol=symbol,
            symbolSize=symbolSize,
            barWidth=barWidth,
            upperThreshold=upperThreshold,
            lowerThreshold=lowerThreshold,
            thresholdColor=thresholdColor,
            yAxisName=yAxisName,
            useArchiveData=useArchiveData,
            liveData=liveData,
            showExtensionLine=showExtensionLine,
        )
        if not is_qt_designer():
            self.requestDataFromArchiver()

        return curve

    def addFormulaChannel(self, yAxisName: str, **kwargs) -> FormulaCurveItem:
        """Creates a FormulaCurveItem and links it to the given y axis"""
        formula_curve = FormulaCurveItem(yAxisName=yAxisName, **kwargs)

        self._curves.append(formula_curve)

        self.plotItem.addItem(formula_curve)
        self.plotItem.linkDataToAxis(formula_curve, yAxisName)

        return formula_curve
