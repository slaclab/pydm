import os
import numpy as np
from unittest import mock
from qtpy.QtCore import QUrl
from qtpy.QtNetwork import QNetworkRequest, QNetworkReply
from pydm.data_plugins.archiver_plugin import Connection
from pydm.tests.conftest import ConnectionSignals
from pydm.widgets.channel import PyDMChannel

import logging

logger = logging.getLogger(__name__)


class MockNetworkManager:
    """A mock of the Qt NetworkManager. Does not actually make any requests, but allows the
    inspection of what those requests would have been.
    """

    def __init__(self):
        self.request_url = None

    def get(self, request: QNetworkRequest):
        """Simply set the request_url to the call that would have been made to the archiver"""
        self.request_url = request.url().url()


class MockNetworkReply:
    """A mock of a reply made from the archiver. Setup here rather than in a unit test to keep the
    test clean as the response is rather long-winded."""

    def __init__(self, is_optimized: bool):
        self.data = None
        if is_optimized:
            self.response = (
                b'[ \n{ "meta": { "name": "ROOM:TEMP" , "EGU": "DegF" , "PREC": "1" },\n"data": '
                b'[ \n{ "secs": 100, "val": [53, 0.2, 52, 54, 10], "nanos": 10, "severity":0, '
                b'"status":0 } ,\n{ "secs": 101, "val": [54.1, 0.3, 54, 55, 10], "nanos": 47, '
                b'"severity":0, "status":0 } ,\n{ "secs": 102, "val": [53.9, 0.1, 53.8, 54, 10], '
                b'"nanos": 22, "severity":0, "status":0 }\n] }\n ]\n'
            )
            self.url_obj = QUrl("http://mock-pydm-url.com/response&pv=optimized")
        else:
            self.response = (
                b'[ \n{ "meta": { "name": "ROOM:TEMP" , "EGU": "DegF" , "PREC": "1" },\n"data": '
                b'[ \n{ "secs": 100, "val": 53, "nanos": 10, "severity":0, "status":0 },\n{ "secs": 101,'
                b' "val": 54.1, "nanos": 47, "severity":0, "status":0 },\n{ "secs": 102, "val": 53.9, '
                b'"nanos": 22, "severity":0, "status":0 }\n] }\n ]\n'
            )
            self.url_obj = QUrl("http://mock-pydm-url")

    def readAll(self):
        return self.response

    def url(self):
        return self.url_obj

    def error(self):
        return QNetworkReply.NoError

    def header(self, content_type):
        return "application/json"

    def deleteLater(self):
        pass


@mock.patch.dict(os.environ, {"PYDM_ARCHIVER_URL": "http://mock-pydm-url"})
def test_fetch_data():
    """Ensure that the url request is built correctly based on the input parameters received"""
    mock_channel = PyDMChannel()
    archiver_connection = Connection(mock_channel, "pv=mock_pv_address")
    archiver_connection.network_manager = MockNetworkManager()

    # Here the from date timestamp is after the to date for the request. This makes no sense, so the
    # request should not happen, hence the request_url remains None.
    archiver_connection.fetch_data(100, 90)
    assert archiver_connection.network_manager.request_url is None

    # This is requesting archive data between December 14th at 8AM and December 15th at 9:30 AM.
    archiver_connection.fetch_data(1639468800, 1639560600)
    expected_url = (
        "http://mock-pydm-url/retrieval/data/getData.json?pv=mock_pv_address"
        "&from=2021-12-14T08:00:00.000Z&to=2021-12-15T09:30:00.000Z"
    )
    assert archiver_connection.network_manager.request_url == expected_url

    # Finally try one that includes a processing command for the archiver appliance
    archiver_connection.fetch_data(1639468800, 1639560600, "optimized_1000")
    expected_url = (
        "http://mock-pydm-url/retrieval/data/getData.json?pv=optimized_1000(mock_pv_address)"
        "&from=2021-12-14T08:00:00.000Z&to=2021-12-15T09:30:00.000Z"
    )

    assert archiver_connection.network_manager.request_url == expected_url


def test_data_request_finished(signals: ConnectionSignals):
    """Verify that an archiver response is parsed correctly and sends the data out in the right format, using
    both the raw data and optimized data formats"""
    mock_channel = PyDMChannel()
    archiver_connection = Connection(mock_channel, "pv=mock_pv_address")

    # First we setup a reply that represents raw data
    mock_reply = MockNetworkReply(is_optimized=False)

    # Create a slot for receiving the data
    archiver_connection.new_value_signal[np.ndarray].connect(signals.receiveValue)
    archiver_connection.data_request_finished(mock_reply)  # type: ignore

    # Verify the data was sent in the expected format
    expected_data_sent = np.array([[100, 101, 102], [53, 54.1, 53.9]])
    assert np.array_equal(signals.value, expected_data_sent)

    # Now repeat the process, except this time as if we requested optimized data
    mock_reply = MockNetworkReply(is_optimized=True)
    archiver_connection.data_request_finished(mock_reply)  # type: ignore

    # Verify the data was sent as expected (timestamps, values, standard deviations, minimums, maximums)
    expected_data_sent = np.array([[100, 101, 102], [53, 54.1, 53.9], [0.2, 0.3, 0.1], [52, 54, 53.8], [54, 55, 54]])
    assert np.array_equal(signals._value, expected_data_sent)
