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

        self.emit_access_state()

        # self.value = address
        self._value = None
        self._value_type = None
        self._name = None
        self.connected = True
        self._configure_local_plugin(address)

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
        # set the object's attributes
        self._value = self._configuration.get('init')
        self._value_type = self._configuration.get('type')
        self.name = self._configuration.get('name')
        if self._configuration.get('type') and self._configuration.get('init'):
            self._is_connection_configured = True
            # send initial value
            self.send_connection_state(conn=True)
            send_value = self.convert_value(self.value, self.value_type)
            self.send_new_value(send_value)

    @Slot(int)
    @Slot(float)
    @Slot(str)
    @Slot(bool)
    @Slot(np.ndarray)
    def send_new_value(self, value):
        if value is not None:
            if isinstance(value, (int, float, bool)):
                self.new_value_signal[type(value)].emit(value)
            elif isinstance(value, np.ndarray):
                self.new_value_signal[np.ndarray].emit(value)
            else:
                self.new_value_signal[str].emit(str(value))

    def emit_access_state(self):
        # emit true for now
        self.write_access_signal.emit(True)

    def convert_value(self, value, value_type):
        # if value is not None and value_type is not None:
        if value_type == 'int':
            try:
                return int(value)
            except TypeError:
                return None
        elif value_type == 'np.ndarray':
            try:
                return np.array(list(value))
            except TypeError:
                return None
        elif value_type == 'float':
            try:
                return float(value)
            except TypeError:
                return None
        elif value_type == 'str':
            try:
                return value
            except TypeError:
                return None
        elif value_type == 'bool':
            try:
                return bool(value)
            except TypeError:
                return None
        else:
            logger.debug(
                'In convert_value provided unknown type %s', value_type)
            return None

    def send_connection_state(self, conn):
        self.connection_state_signal.emit(conn)

    def add_listener(self, channel):
        super(Connection, self).add_listener(channel)
        self.send_connection_state(conn=True)

        # Connect the channel up  to the 'put_value' method
        # TODO: add a function to give you the type?
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

    @Slot(int)
    @Slot(float)
    @Slot(str)
    @Slot(bool)
    @Slot(np.ndarray)
    def put_value(self, new_value):
        if new_value is not None:
            # update the attributes here with the new values
            self._value = new_value
            # send this value
            self.send_new_value(new_value)


class LocalPlugin(PyDMPlugin):
    protocol = "loc"
    connection_class = Connection
