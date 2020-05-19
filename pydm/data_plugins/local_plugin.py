import logging
import json
import numpy as np

from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection
from qtpy.QtCore import Slot, Signal, Qt

logger = logging.getLogger(__name__)


class Connection(PyDMConnection):
    new_data_signal = Signal([int], [float], [str], [bool], [np.ndarray])

    def __init__(self, channel, address, protocol=None, parent=None):
        super(Connection, self).__init__(channel, address, protocol, parent)

        self.add_listener(channel)
        self._is_connection_configured = False
        self._configuration = {}

        self._configure_local_plugin(address)
        self.emit_access_state()

        self._value = None
        self._value_type = None
        self._name = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @property
    def value_type(self):
        return self._value_type

    @value_type.setter
    def value_type(self, value_type):
        self._value_type = value_type

    def _configure_local_plugin(self, address):
        if self._is_connection_configured:
            logger.debug('LocalPlugin connection already configured.')
            return
        try:
            self._configuration = json.loads(address)
        except:
            logger.warning(
                'Invalid configuration for LocalPlugin connection. %s',
                address)
            return
        if self._configuration.get('type') and self._configuration.get('init'):
            self._is_connection_configured = True
            # set the object's attributes
            self.value = self._configuration.get('init')
            self.value_type = self._configuration.get('type')
            self.name = self._configuration.get('name')
            # send initial value
            self.send_new_value(self.value)

    @Slot(int)
    @Slot(float)
    @Slot(str)
    @Slot(bool)
    @Slot(np.ndarray)
    def send_new_value(self, value):
        if value is not None:
            self.new_value_signal[type(value)].emit(value)
            if isinstance(value, (int, float, bool)):
                self.new_value_signal[type(value)].emit(value)
            elif isinstance(value, np.ndarray):
                self.new_value_signal[np.ndarray].emit(value)
            else:
                self.new_value_signal[str].emit(str(value))

    def emit_access_state(self):
        # emit true for now
        self.write_access_signal.emit(True)

    def send_connection_state(self, conn):
        self.connection_state_signal.emit(conn)

    def add_listener(self, channel):
        super(Connection, self).add_listener(channel)
        self.send_connection_state(conn=True)
        # Connect the channel up  to the 'put_value' method
        if channel.value_signal is not None:
            try:
                channel.value_signal[int].connect(
                   self.put_value, Qt.QueuedConnection)
            except KeyError:
                pass
            try:
                channel.value_signal[float].connect(
                   self.put_value, Qt.QueuedConnection)
            except KeyError:
                pass
            try:
                channel.value_signal[str].connect(
                   self.put_value, Qt.QueuedConnection)
            except KeyError:
                pass
            try:
                channel.value_signal[bool].connect(
                   self.put_value, Qt.QueuedConnection)
            except KeyError:
                pass
            try:
                channel.value_signal[np.ndarray].connect(
                   self.put_value, Qt.QueuedConnection)
            except KeyError:
                pass
        # self.update()

    # @Slot()
    # def update(self):
    #     if self.value is None:
    #         self.send_connection_state(False)
    #         return
    #     else:
    #         self.send_connection_state(True)
    #         self.send_new_value(self.value)

    # def is_connected(self):
    #     try:
    #         # some way of finding out if connected
    #         return True
    #     except:
    #         return False

    @Slot(int)
    @Slot(float)
    @Slot(str)
    @Slot(bool)
    @Slot(np.ndarray)
    def put_value(self, new_value):
        if new_value is not None:
            # update the attributes here with the new values
            self.value = new_value
            # send this value
            self.send_new_value(new_value)

            # self.new_value_signal[type(new_value)].emit(new_value)
            # if isinstance(new_value, (int, float, bool)):
            #     print('is bool or int or float')
            #     self.new_value_signal[type(new_value)].emit(new_value)
            # elif isinstance(new_value, np.ndarray):
            #     print('is np.ndarray')
            #     self.new_value_signal[np.ndarray].emit(new_value)
            # else:
            #     print('is string')
            #     self.new_value_signal[str].emit(str(new_value))

            # self.update()
            # maybe here just update the attributes for the class


class LocalPlugin(PyDMPlugin):
    protocol = "loc"
    connection_class = Connection

    @staticmethod
    def get_connection_id(channel):
        address = PyDMPlugin.get_address(channel)
        addr = json.loads(address)
        name = addr.get('name')
        if not name:
            raise ValueError('Name is a required field for the local plugin')
        return name
