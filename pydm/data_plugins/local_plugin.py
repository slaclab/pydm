import logging
import json
import numpy as np

from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection
from qtpy.QtCore import Slot, Qt

logger = logging.getLogger(__name__)


class Connection(PyDMConnection):
    def __init__(self, channel, address, protocol=None, parent=None):
        super(Connection, self).__init__(channel, address, protocol, parent)

        self.add_listener(channel)

        self._is_connection_configured = False
        self._configuration = {}

        self.emit_access_state()

        self._value = None
        self._value_type = None
        self._name = None
        self.connected = False
        self._configure_local_plugin(address)
        self.send_new_value(723)

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
        self._name = self._configuration.get('name')
        if self._configuration.get('type') and self._configuration.get('init'):
            self._is_connection_configured = True
            self.send_connection_state(conn=True)
            # send initial value
            send_value = self.convert_value(self._value, self._value_type)
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
                #return np.ndarray(list(value))
                # this is for np.array
                return np.fromstring(value[1:-1], dtype=np.int, sep=',')
                # this is for np.ndarray
                #np.fromstring(value.replace(), .reshape())
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
        self.connected = conn
        self.connection_state_signal.emit(conn)

    def add_listener(self, channel):
        super(Connection, self).add_listener(channel)
        if channel.connection_slot is not None:
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
