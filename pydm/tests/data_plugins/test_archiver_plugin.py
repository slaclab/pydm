import os
import pytest
from qtpy.QtNetwork import QNetworkRequest
from unittest import mock
from pydm.data_plugins.archiver_plugin import Connection
from pydm.widgets.channel import PyDMChannel

import logging
logger = logging.getLogger(__name__)


class MockNetworkManager:
    """ A mock of the Qt NetworkManager. Does not actually make any requests, but allows the
        inspection of what those requests would have been.
    """
    def __init__(self):
        self.request_url = None

    def get(self, request: QNetworkRequest):
        """ Simply set the request_url to the call that would have been made to the archiver """
        self.request_url = request.url().url()


@mock.patch.dict(os.environ, {"PYDM_ARCHIVER_URL": "http://mock-pydm-url"})
def test_fetch_data():
    """ Ensure that the url request is built correctly based on the input parameters received """
    mock_channel = PyDMChannel()
    archiver_connection = Connection(mock_channel, "pv=mock_pv_address")
    archiver_connection.network_manager = MockNetworkManager()

    # Here the from date timestamp is after the to date for the request. This makes no sense, so the
    # request should not happen, hence the request_url remains None.
    archiver_connection.fetch_data(100, 90)
    assert archiver_connection.network_manager.request_url is None

    # This is requesting archive data between December 14th at 8AM and December 15th at 9:30 AM.
    archiver_connection.fetch_data(1639468800, 1639560600)
    expected_url = "http://mock-pydm-url/retrieval/data/getData.json?pv=mock_pv_address" \
                   "&from=2021-12-14T08:00:00.000Z&to=2021-12-15T09:30:00.000Z"
    assert archiver_connection.network_manager.request_url == expected_url

    # Finally try one that includes a processing command for the archiver appliance
    archiver_connection.fetch_data(1639468800, 1639560600, "optimized_1000")
    expected_url = "http://mock-pydm-url/retrieval/data/getData.json?pv=optimized_1000(mock_pv_address)" \
                   "&from=2021-12-14T08:00:00.000Z&to=2021-12-15T09:30:00.000Z"

    assert archiver_connection.network_manager.request_url == expected_url
