import os
import json
import logging
import numpy as np

from datetime import datetime, timezone
from typing import Optional

from pydm.widgets.channel import PyDMChannel
from qtpy.compat import isalive
from qtpy.QtCore import Slot, QObject, QUrl, QTimer
from qtpy.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection

logger = logging.getLogger(__name__)


class Connection(PyDMConnection):
    """
    Manages the requests between the archiver data plugin and the archiver appliance itself.
    """

    def __init__(
        self, channel: PyDMChannel, address: str, protocol: Optional[str] = None, parent: Optional[QObject] = None
    ):
        super().__init__(channel, address, protocol, parent)
        self.add_listener(channel)
        self.address = address
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished[QNetworkReply].connect(self.data_request_finished)

    def add_listener(self, channel: PyDMChannel) -> None:
        """
        Connects a channel's signal to the slot on this connection so that the channel has a way of requesting
        and receiving data from the archiver.

        Parameters
        ----------
        channel : PyDMChannel
            The channel to connect
        """
        super().add_listener(channel)
        if channel.value_signal is not None:
            channel.value_signal.connect(self.fetch_data)

    def fetch_data(self, from_date: float, to_date: float, processing_command: Optional[str] = None) -> None:
        """
        Fetches data from the Archiver Appliance based on the input parameters.

        Parameters
        ----------
        from_date : float
            Timestamp for the oldest data point to retrieve
        to_date : float
            Timestamp for the newest data point to retrieve
        processing_command : str
            A string that will be added to the URL to request additional processing on the archiver side before
            returning the data such as mean values or optimized. For a full list see:
            https://slacmshankar.github.io/epicsarchiver_docs/userguide.html
            Note: Due to the potential of additional valid options in the future, no validation is
            done on this parameter. It is the responsibility of the caller to ensure it is valid
        """
        if from_date >= to_date:
            logger.error(f"Cannot fetch data for invalid data range, from date={from_date} and to date={to_date}")
            return

        # Archiver expects timestamps to be in utc by default
        from_dt = datetime.fromtimestamp(from_date, tz=timezone.utc)
        to_dt = datetime.fromtimestamp(to_date, tz=timezone.utc)

        # Put the dates into the form expected by the archiver in the request url, see here for more details:
        # http://joda-time.sourceforge.net/apidocs/org/joda/time/format/ISODateTimeFormat.html#dateTime()
        from_date_str = from_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        to_date_str = to_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        base_url = os.getenv("PYDM_ARCHIVER_URL")
        if base_url is None:
            logger.error(
                "Environment variable: PYDM_ARCHIVER_URL must be defined to use the archiver plugin, for "
                "example: http://lcls-archapp.slac.stanford.edu"
            )
            self.connection_state_signal.emit(False)
            return

        url_string = f"{base_url}/retrieval/data/getData.json?{self.address}&from={from_date_str}&to={to_date_str}"
        if processing_command:
            url_string = url_string.replace("pv=", "pv=" + processing_command + "(", 1)
            url_string = url_string.replace("&from=", ")&from=", 1)

        request = QNetworkRequest(QUrl(url_string))
        # This get call is non-blocking, can be made in parallel with others, and when the results are ready they
        # will be delivered to the data_request_finished method below via the "finished" signal
        reply = self.network_manager.get(request)

        def timeout():
            if not isinstance(reply, QNetworkReply) or not isalive(reply):
                return
            reply.abort()

        QTimer.singleShot(7500, timeout)

    @Slot(QNetworkReply)
    def data_request_finished(self, reply: QNetworkReply) -> None:
        """
        Invoked when the request to the archiver appliance has been completed and the reply has been returned. Will
        fire off the value signal with a 2D numpy array containing the x-values (timestamps) and y-values (PV data).

        Parameters
        ----------
        reply: The response from the archiver appliance
        """
        success = (
            reply.error() == QNetworkReply.NoError
            and reply.header(QNetworkRequest.ContentTypeHeader) == "application/json"
        )
        self.connection_state_signal.emit(success)
        if success:
            bytes_str = reply.readAll()
            data_dict = json.loads(str(bytes_str, "utf-8"))

            if "pv=optimized" in reply.url().url():  # From a url object to a string
                self._send_optimized_data(data_dict)
            else:
                self._send_raw_data(data_dict)
        else:
            logger.debug(
                f"Request for data from archiver failed, request url: {reply.url()} retrieved header: "
                f"{reply.header(QNetworkRequest.ContentTypeHeader)} error: {reply.error()}"
            )
        reply.deleteLater()

    def _send_raw_data(self, data_dict: dict) -> None:
        """
        Sends a numpy array of shape (2, data_length) containing the x-values (timestamps) and y-values (PV data)
        via the new value signal
        """
        data = np.array(
            ([point["secs"] for point in data_dict[0]["data"]], [point["val"] for point in data_dict[0]["data"]])
        )
        self.new_value_signal[np.ndarray].emit(data)

    def _send_optimized_data(self, data_dict: dict) -> None:
        """
        Sends a numpy array of shape (5, data_length). Index 0 contains the timestamps, index 1 the mean values,
        index 2 the standard deviations, index 3 the minimum values, and index 4 the maximum values.
        """
        pv_data = [point["val"] for point in data_dict[0]["data"]]
        try:
            data = np.array(
                (
                    [point["secs"] for point in data_dict[0]["data"]],
                    [point[0] for point in pv_data],
                    [point[1] for point in pv_data],
                    [point[2] for point in pv_data],
                    [point[3] for point in pv_data],
                )
            )
        except TypeError:
            # The archiver will fall back to sending raw data if the optimized request is for more data points
            # than are in the bin
            self._send_raw_data(data_dict)
            return

        self.new_value_signal[np.ndarray].emit(data)


class ArchiverPlugin(PyDMPlugin):
    protocol = "archiver"
    connection_class = Connection
