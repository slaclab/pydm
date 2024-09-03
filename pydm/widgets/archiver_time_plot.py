import json
import re
import time
import numpy as np
from collections import OrderedDict
from typing import List, Optional
from pyqtgraph import DateAxisItem, ErrorBarItem
from pydm.utilities import remove_protocol
from pydm.widgets.channel import PyDMChannel
from pydm.widgets.timeplot import TimePlotCurveItem
from pydm.widgets import PyDMTimePlot
from qtpy.QtCore import QObject, QTimer, Property, Signal, Slot
from qtpy.QtGui import QColor
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
    **kws : dict[str: any]
        Additional parameters supported by pyqtgraph.PlotDataItem.
    """

    # Used to request data from archiver appliance (starting timestamp, ending timestamp, processing command)
    archive_data_request_signal = Signal(float, float, str)
    archive_data_received_signal = Signal()

    def __init__(
        self, channel_address: Optional[str] = None, use_archive_data: bool = True, liveData: bool = True, **kws
    ):
        super(ArchivePlotCurveItem, self).__init__(**kws)
        self.use_archive_data = use_archive_data
        self.archive_channel = None
        self.archive_points_accumulated = 0
        self._archiveBufferSize = DEFAULT_ARCHIVE_BUFFER_SIZE
        self.archive_data_buffer = np.zeros((2, self._archiveBufferSize), order="f", dtype=float)
        self._liveData = liveData

        # When optimized or mean value data is requested, we can display error bars representing
        # the full range of values retrieved
        self.error_bar_item = ErrorBarItem()
        self.error_bar_needs_set = True

        self.address = channel_address

    def to_dict(self) -> OrderedDict:
        """Returns an OrderedDict representation with values for all properties needed to recreate this curve."""
        dic_ = OrderedDict([("useArchiveData", self.use_archive_data), ("liveData", self.liveData)])
        dic_.update(super(ArchivePlotCurveItem, self).to_dict())
        return dic_

    @property
    def address(self):
        return super().address

    @address.setter
    def address(self, new_address: str) -> None:
        """Creates the channel for the input address for communicating with the archiver appliance plugin."""
        TimePlotCurveItem.address.__set__(self, new_address)

        if not new_address:
            self.archive_channel = None
            return
        elif self.archive_channel and new_address == self.archive_channel.address:
            return

        # Prepare new address to use the archiver plugin and create the new channel
        archive_address = "archiver://pv=" + remove_protocol(new_address.strip())
        self.archive_channel = PyDMChannel(
            address=archive_address, value_slot=self.receiveArchiveData, value_signal=self.archive_data_request_signal
        )

        # Clear the archive data of the previous channel and redraw the curve
        if self.archive_points_accumulated:
            self.initializeArchiveBuffer()
            self.redrawCurve()

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
            self.error_bar_item.setData(
                x=self.archive_data_buffer[0, -self.archive_points_accumulated :],
                y=self.archive_data_buffer[1, -self.archive_points_accumulated :],
                top=data[4] - data[1],
                bottom=data[1] - data[3],
                beam=0.5,
                pen={"color": self.color},
            )
            if self.error_bar_needs_set:
                self.getViewBox().addItem(self.error_bar_item)
                self.error_bar_needs_set = False

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
            super(ArchivePlotCurveItem, self).redrawCurve()
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

    def receiveNewValue(self, new_value):
        """ """
        if self._liveData:
            super().receiveNewValue(new_value)


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

    archive_data_request_signal = Signal(float, float, str)
    archive_data_received_signal = Signal()
    formula_invalid_signal = Signal()

    def __init__(
        self,
        formula: str = None,
        pvs: dict = None,
        use_archive_data: Optional[bool] = True,
        liveData: Optional[bool] = True,
        color: Optional[str] = "green",
        **kws
    ):
        super(FormulaCurveItem, self).__init__(**kws)
        self.color = color
        self.use_archive_data = use_archive_data
        self.archive_points_accumulated = 0
        # Start with empty buffers because we don't
        # calculate anything until we try to draw the curve
        self._archiveBufferSize = DEFAULT_ARCHIVE_BUFFER_SIZE
        self._bufferSize = 0
        self.archive_data_buffer = np.zeros((2, 0), order="f", dtype=float)

        self.data_buffer = np.zeros((2, 0), order="f", dtype=float)

        # When optimized or mean value data is requested, we can display error bars representing
        # the full range of values retrieved
        self.error_bar_item = ErrorBarItem()
        self.error_bar_needs_set = True
        self._formula = formula
        # Have a formula for internal calculations, that the user does not see
        self._trueFormula = self.createTrueFormula()
        self.pvs = pvs
        self._liveData = liveData
        self.plot_style = "Line"

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
        dic_.update(super(FormulaCurveItem, self).to_dict())
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
        if not self.checkFormula():
            self.formula_invalid_signal.emit()
            return
        pvArchiveData = dict()
        pvLiveData = dict()
        pvIndices = dict()
        pvValues = dict()
        formula = self._trueFormula
        if not formula:
            logger.error("invalid formula")
            return

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
        the data step by step and calculate our formula at each timestamp available

        Parameters
        ----------------
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
            Whether or not this is computing for the Archive or for Live"""

        current_time = self.min_archiver_x
        output = np.zeros((2, 0), order="f", dtype=float)
        while True:
            if archive:
                self.archive_points_accumulated += 1
            else:
                self.points_accumulated += 1
            minPV = None
            # Find the next x point out of all of our rows.
            # Update only that row's value, use the previous value of other rows for calcs.
            current_time = 0
            min_pv_current_index = 0
            for pv in self.pvs.keys():
                pv_times = pvData[pv][0]
                pv_current_index = pvIndices[pv]
                if minPV is None or pv_times[pv_current_index] < current_time:
                    minPV = pv
                    current_time = pv_times[pv_current_index]
                    min_pv_current_index = pv_current_index

            pvValues[minPV] = pvData[minPV][1][min_pv_current_index]
            try:
                temp = np.array([[current_time], [eval(formula)]])
            except ValueError:
                logger.warning("Evaluate failed (domain errors? unknown function?)")
                temp = np.array([[current_time], [0]])
            output = np.append(output, temp, axis=1)
            pvIndices[minPV] += 1
            # If we are out of data for this row, stop!
            if pvIndices[minPV] >= len(pvData[minPV][0]):
                break
        return output

    @Slot()
    def redrawCurve(self, min_x=None, max_x=None) -> None:
        """
        Redraw the curve with any new data added since the last draw call.
        """
        if not self.pvs:
            # If we are just a constant, then forget about data
            # just draw a straight line from 1970 to 300 years or so in the future
            y = [eval(self._trueFormula), eval(self._trueFormula)]
            x = [0, APPROX_SECONDS_300_YEARS]
            # There is a known bug that this won't graph a constant with an x axis
            # of between 30 minutes and 1hr 30 minutes in range. Unknown reason
            self.setData(y=y, x=x)
            return
        self.evaluate()
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
    background: str
        The background color for the plot.  Accepts any arguments that
        pyqtgraph.mkColor will accept.
    optimized_data_bins: int
        The number of bins of data returned from the archiver when using optimized requests
    """

    def __init__(
        self,
        parent: Optional[QObject] = None,
        init_y_channels: List[str] = [],
        background: str = "default",
        optimized_data_bins: int = 2000,
    ):
        super(PyDMArchiverTimePlot, self).__init__(
            parent=parent,
            init_y_channels=init_y_channels,
            plot_by_timestamps=True,
            background=background,
            bottom_axis=DateAxisItem("bottom"),
        )
        self.optimized_data_bins = optimized_data_bins
        self._min_x = None
        self._prev_x = None  # Holds the minimum x-value of the previous update of the plot
        self._starting_timestamp = time.time()  # The timestamp at which the plot was first rendered
        self._archive_request_queued = False

    def updateXAxis(self, update_immediately: bool = False) -> None:
        """Manages the requests to archiver appliance. When the user pans or zooms the x axis to the left,
        a request will be made for backfill data"""
        if len(self._curves) == 0 or self.auto_scroll_timer.isActive():
            return

        min_x = self.plotItem.getAxis("bottom").range[0]  # Gets the leftmost timestamp displayed on the x-axis
        max_x = self.plotItem.getAxis("bottom").range[1]
        max_point = max([curve.max_x() for curve in self._curves])
        if min_x == 0:  # This is zero when the plot first renders
            min_x = time.time()
            self._min_x = min_x
            self._starting_timestamp = min_x - DEFAULT_TIME_SPAN  # A bit of a buffer so we don't overwrite live data
            if self.getTimeSpan() != DEFAULT_TIME_SPAN:
                # Initialize x-axis based on the time span as well as trigger a call to the archiver below
                self._min_x = self._min_x - self.getTimeSpan()
                self._archive_request_queued = True
                self.requestDataFromArchiver()
            self.plotItem.setXRange(
                time.time() - DEFAULT_TIME_SPAN, time.time(), padding=0.0, update=update_immediately
            )
        elif min_x < self._min_x and not self.plotItem.isAnyXAutoRange():
            # This means the user has manually scrolled to the left, so request archived data
            self._min_x = min_x
            self.setTimeSpan(max_point - min_x)
            if not self._archive_request_queued:
                # Letting the user pan or scroll the plot is convenient, but can generate a lot of events in under
                # a second that would trigger a request for data. By using a timer, we avoid this burst of events
                # and consolidate what would be many requests to archiver into just one.
                self._archive_request_queued = True
                QTimer.singleShot(1000, self.requestDataFromArchiver)
        # Here we only update the x-axis if the user hasn't asked for autorange and they haven't zoomed in (as
        # detected by the max range showing on the plot being less than the data available)
        elif not self.plotItem.isAnyXAutoRange() and max_x >= max_point - 10:
            if min_x > (self._prev_x + 15) or min_x < (self._prev_x - 15):
                # The plus/minus 15 just makes sure we don't do this on every update tick of the graph
                self.setTimeSpan(max_point - min_x)
            else:
                # Keep the plot moving with a rolling window based on the current timestamp
                self.plotItem.setXRange(
                    max_point - self.getTimeSpan(), max_point, padding=0.0, update=update_immediately
                )
        self._prev_x = min_x

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
        if min_x is None:
            min_x = self._min_x
        for curve in self._curves:
            processing_command = ""
            if curve.use_archive_data:
                if max_x is None:
                    max_x = curve.min_x()
                requested_seconds = max_x - min_x
                if requested_seconds <= 5:
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
        return curve_item

    @Slot()
    def archive_data_received(self):
        """Take any action needed when this plot receives new data from archiver appliance"""
        self._archive_request_queued = False
        if self.auto_scroll_timer.isActive():
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
            # Need to clear out any bars from optimized data, then super() can handle the rest
            if not curve.error_bar_needs_set:
                curve.getViewBox().removeItem(curve.error_bar_item)

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
        useArchiveData=False,
        liveData=True,
    ) -> ArchivePlotCurveItem:
        """
        Overrides timeplot addYChannel method to be able to pass the liveData flag.
        """
        return super().addYChannel(
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
        )

    def addFormulaChannel(self, yAxisName: str, **kwargs) -> FormulaCurveItem:
        """Creates a FormulaCurveItem and links it to the given y axis"""
        FormulaCurve = FormulaCurveItem(yAxisName=yAxisName, **kwargs)
        self.plotItem.linkDataToAxis(FormulaCurve, yAxisName)
        return FormulaCurve
