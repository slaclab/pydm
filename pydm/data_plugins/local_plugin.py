"""
Local Plugin
"""
import ast
import decimal
import logging
import json
import numpy as np
from qtpy.QtCore import Slot, Qt
from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection


logger = logging.getLogger(__name__)


class Connection(PyDMConnection):
    def __init__(self, channel, address, protocol=None, parent=None):
        self._is_connection_configured = False
        self._value_type = None
        self._subtype = None

        super(Connection, self).__init__(channel, address, protocol, parent)

        self.add_listener(channel)

        self._configuration = {}

        self.send_connection_state(False)
        self.send_access_state()

        self.connected = False
        self._configure_local_plugin(channel)

    def _configure_local_plugin(self, channel):
        if self._is_connection_configured:
            logger.debug('LocalPlugin connection already configured.')
            return

        address = PyDMPlugin.get_address(channel)

        try:
            self._configuration = json.loads(address)
        except json.decoder.JSONDecodeError:
            logger.debug(
                'Invalid configuration for LocalPlugin connection. %s',
                address)
            return

        if self._configuration.get('subtype'):
            self._subtype = self._configuration.get('subtype')
            self._subtype = np.dtype(self._subtype)
        if (self._configuration.get('name') and self._configuration.get('type')
                and self._configuration.get('init')):
            self._is_connection_configured = True
            self.address = address
            # set the object's attributes
            init_value = self._configuration.get('init')
            self._value_type = self._configuration.get('type')
            self.name = self._configuration.get('name')
            # send initial values
            self.value = self.convert_value(init_value,
                                            self._value_type, self._subtype)
            self.connected = True
            self.send_connection_state(True)
            self.send_new_value(self.value)

    @Slot(int)
    @Slot(float)
    @Slot(str)
    @Slot(bool)
    @Slot(np.ndarray)
    def send_new_value(self, value):
        """
        Sends all the values sent trought a specific local
        variable channel to all its listeners

        """
        if value is not None:
            if isinstance(value, (int, float, bool, str)):
                self.new_value_signal[type(value)].emit(value)
            elif isinstance(value, np.ndarray):
                self.new_value_signal[np.ndarray].emit(value)
            else:
                logger.debug('Does not support this type')

    def send_precision(self, value):
        """
        Sends the precision for float values
        It is being sent anytime a float value is sent

        Parameters
        ----------
        value : float
            The value to be sent

        """
        if value is not None:
            dec = decimal.Decimal(str(value))
            precision = len(str(dec).split('.')[1])
            self.prec_signal.emit(precision)

    def send_access_state(self):
        # emit true for all widgets using Local Plugin
        self.write_access_signal.emit(True)

    def convert_value(self, value, value_type, subtype):
        """
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

        """
        if value_type == 'int':
            try:
                return int(value)
            except ValueError:
                pass
        elif 'ndarray' in value_type:
            try:
                # evaluate it first
                value_list = ast.literal_eval(value)
                value_array = None
                # convert into a numpy array
                if subtype is not None:
                    value_array = np.array(value_list, dtype=subtype)
                else:
                    # default the subtype to int64 if no subtype provided
                    value_array = np.array(value_list, dtype=np.int64)
                return value_array
            except ValueError:
                pass
        elif value_type == 'float':
            try:
                return float(value)
            except ValueError:
                pass
        elif value_type == 'str':
            try:
                return str(value)
            except ValueError:
                pass
        elif value_type == 'bool':
            try:
                # is True if not found in the list with possible false values
                str_value = str(value).strip().lower()
                return str_value not in ['false', 'f', 'n', '1', '']
            except ValueError:
                pass
        else:
            msg = 'In convert_value provide unknown type %s', value
            logger.debug(msg)
            raise ValueError(msg)

    def send_connection_state(self, conn):
        self.connected = conn
        self.connection_state_signal.emit(conn)

    def add_listener(self, channel):
        super(Connection, self).add_listener(channel)
        self._configure_local_plugin(channel)
        # send write acces == True to the listeners
        self.send_access_state()
        # send new values to the listeners right away
        self.send_new_value(self.value)
        # send the precision in case of float values
        if isinstance(self.value, float):
            self.send_precision(self.value)

        if channel.connection_slot is not None:
            self.send_connection_state(conn=True)

        # Connect the put_value slot to the channel's value_signal,
        # which captures the values sent through the plugin
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
        """
        Slot connected to the channal.value_signal.
        Updates the value of this local variable and then broadcasts it to
        the other listeners to this channel
        """
        if new_value is not None:
            # update the attributes here with the new values
            self.value = new_value
            # send this value
            self.send_new_value(new_value)
            # send precision for float values
            if isinstance(new_value, float):
                self.send_precision(new_value)


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
