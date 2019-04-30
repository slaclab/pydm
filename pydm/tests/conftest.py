# coding: utf-8
# Fixtures for PyDM Unit Tests

import pytest
from pytestqt.qt_compat import qt_api

import tempfile
import logging

from pydm.application import PyDMApplication
from pydm import data_plugins
from pydm.data_plugins import PyDMPlugin, add_plugin, PyDMConnection

logger = logging.getLogger(__name__)
_, file_path = tempfile.mkstemp(suffix=".log")
handler = logging.FileHandler(file_path)
logger.addHandler(handler)


@pytest.yield_fixture(scope='session')
def qapp(qapp_args):
    """
    Fixture for a PyDMApplication app instance.

    Parameters
    ----------
    qapp_args: Arguments for the QApp.

    Returns
    -------
    An instance of PyDMApplication.
    """
    app = qt_api.QApplication.instance()
    if app is None or not isinstance(app, PyDMApplication):
        global _qapp_instance
        _qapp_instance = PyDMApplication(use_main_window=False, *qapp_args)
        yield _qapp_instance
    else:
        yield app  # pragma: no cover


class TestPluginConnection(PyDMConnection):
    def __init__(self, *args, **kwargs):
        super(TestPluginConnection, self).__init__(*args, **kwargs)
        self.payload_received = None

    def receive_from_channel(self, payload):
        self.payload_received = payload

    def write_introspection(self, intro):
        self.introspection = intro

    def write_data(self, payload):
        self.data = payload
        self.send_to_channel()


class TestPlugin(PyDMPlugin):
    protocol = "tst"
    connection_class = TestPluginConnection


@pytest.fixture(scope='function')
def test_plugin():
    # Create test PyDMPlugin with mock protocol
    test_plug = TestPlugin
    add_plugin(test_plug)
    return data_plugins.plugin_modules['tst']
