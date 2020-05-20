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
        except json.decoder.JSONDecodeError:
            logger.debug(
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
            # send initial values
            # this should set the type of this variable and there
            # should not be any need to convert it somewhere else
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
        '''
        Function that converts values from string to
        their appropriate type

        Parameters
        ----------
        value : str
            Data for this variable.
        value_type : str
            Data type intended for this variable.

        Returns
        -------
            The data for this variable converted to its appropriate type

        '''
        if value_type == 'int':
            try:
                return int(value)
            except TypeError:
                pass
        elif (value_type == 'np.ndarray' or value_type == 'numpy.ndarray' or
              value_type == 'np.array' or value_type == 'numpy.array'):
            try:
                # convert this into an np.ndarray of floats for now
                return np.ndarray(value)
            except TypeError:
                pass
        elif value_type == 'float':
            try:
                return float(value)
            except TypeError:
                pass
        elif value_type == 'str':
            try:
                return value
            except TypeError:
                pass
        elif value_type == 'bool':
            try:
                return bool(value)
            except TypeError:
                pass
        else:
            logger.debug(
                'In convert_value provided unknown type %s,'
                'will default to str', value_type)
            return value

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
        '''
        Slot connected to the channal.value_signal.
        Updates the value of this local variable and then broadcasts it to
        the other listeners to this channel
        '''
        print('---- the value type: ---', type(new_value))
        if new_value is not None:
            # update the attributes here with the new values
            self._value = new_value
            # send this value
            self.send_new_value(new_value)


class LocalPlugin(PyDMPlugin):
    protocol = "loc"
    connection_class = Connection

    @staticmethod
    def get_connection_id(channel):
        address = PyDMPlugin.get_address(channel)

        addr = json.loads(address)
        name = addr.get('name')
        if not name:
            raise ValueError("Name is a required field for local plugin")
        return name
