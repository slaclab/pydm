"""Local Plugin."""
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
        self._precision_set = None
        self._type_kwargs = {}

        self._extra_config_keys = [
            "precision",
            "unit",
            "upper_limit",
            "lower_limit",
            "enum_string",
            "severity"
            ]

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

        if (self._configuration.get('name') and self._configuration.get('type')
                and self._configuration.get('init')):
            self._is_connection_configured = True
            self.address = address

            # get the extra info if any
            extras = self._configuration.get('extras')
            if extras:
                self.parse_channel_extras(extras)

            # set the object's attributes
            init_value = self._configuration.get('init')
            self._value_type = self._configuration.get('type')
            self.name = self._configuration.get('name')

            # send initial values
            self.value = self.convert_value(init_value, self._value_type)
            self.connected = True
            self.send_connection_state(True)
            self.send_new_value(self.value)

    def parse_channel_extras(self, extras):
        """
        Parse the extras dictionay and either pass the data
        to the appropriate methods that will take care of it,
        or emit it right away.
        Those methods should be responsible for converting
        the data into appropriate types as well, this function
        will pass strings to them

        Parameters
        ----------
        extras : dict
            Dictionary containing extra parameters for the
            this local variable configuration configuration
            These parameters are optional

        Returns
        -------
        None.

        """
        precision = extras.get('precision')
        if precision is not None:
            try:
                precision = int(precision)
                self._precision_set = precision
                self.prec_signal.emit(self._precision_set)
            except ValueError:
                logger.debug('Cannot convert precision')
        unit = extras.get('unit')
        if unit is not None:
            self.unit_signal.emit(str(unit))
        upper_limit = extras.get('upper_limit')
        if upper_limit is not None:
            self.send_upper_limit(upper_limit)
        lower_limit = extras.get('lower_limit')
        if lower_limit is not None:
            self.send_lower_limit(lower_limit)
        enum_string = extras.get('enum_string')
        if enum_string is not None:
            self.send_enum_string(enum_string)
        severity = extras.get('severity')
        if severity is not None:
            self.send_severity(severity)
        type_kwargs = {k: v for k, v in extras.items()
                       if k not in self._extra_config_keys}
        if type_kwargs:
            self.format_ndarray_params(type_kwargs)

    @Slot(int)
    @Slot(float)
    @Slot(str)
    @Slot(bool)
    @Slot(np.ndarray)
    def send_new_value(self, value):
        """
        Send the values sent trought a specific local
        variable channel to all its listeners.
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
        Send the precision for float values.
        It is being sent anytime a float value is sent.

        Parameters
        ----------
        value : string
            The value to be sent,should be sent as int

        Returns
        -------
        None.

        """
        if value is not None:
            dec = decimal.Decimal(str(value))
            precision = len(str(dec).split('.')[1])
            self.prec_signal.emit(precision)

    def send_unit(self, unit):
        """
        Send the unit for the data.

        Parameters
        ----------
        unit : string

        Returns
        -------
        None.

        """
        if unit is not None:
            self.prec_signal.emit(str(unit))

    def send_upper_limit(self, upper_limit):
        """
        Send the upper limit value as float or int.

        Parameters
        ----------
        upper_limit : string

        Returns
        -------
        None.

        """
        if upper_limit is not None:
            try:
                upper_limit = int(upper_limit)
            except ValueError:
                upper_limit = float(upper_limit)

            self.upper_ctrl_limit_signal.emit(upper_limit)

    def send_lower_limit(self, lower_limit):
        """
        Send the lower limit value as float or int.

        Parameters
        ----------
        lower_limit : string

        Returns
        -------
        None.

        """
        if lower_limit is not None:
            try:
                lower_limit = int(lower_limit)
            except ValueError:
                lower_limit = float(lower_limit)

            self.lower_ctrl_limit_signal.emit(lower_limit)

    def send_enum_string(self, enum_string):
        """
        Send enum_string as tuple of strings.

        Parameters
        ----------
        enum_string : string

        Returns
        -------
        None.

        """
        if enum_string is not None:
            try:
                enum = enum_string.replace('(', '').replace(')', '').split(',')
                enum_string = tuple(enum)
                self.enum_strings_signal.emit(enum_string)
            except ValueError:
                logger.debug("Error when converting enum_string")

    def send_severity(self, severity):
        """
        Send severity as int.

        Possible values:
            0 - NO_ALARM
            1 - MINOR
            2 - MAJOR
            3 - INVALID

        Parameters
        ----------
        severity : string

        Returns
        -------
        None.

        """
        if severity is not None:
            try:
                severity = int(severity)
                self.new_severity_signal.emit(severity)
            except ValueError:
                logger.debug("Cannot convert severity")

    def format_ndarray_params(self, type_kwargs):
        """
        Format the ndarray parameters.
        Possible parameters:
            object - array_like
            dtype - data-type, optional
            copy - bool, optional
            order - {'K', 'A', 'C', 'F'}, optional
            subok - bool, optional
            ndmin - int, optional

        Parameters
        ----------
        type_kwargs : dict
            String representing a set of parameters for np.array()

        Returns
        -------
            ndarray

        """
        # default values that a np.array() will normally use
        # to construct a ndarray if they are not specified
        dtype = None
        copy = True
        order = 'K'
        subok = False
        ndmin = 0

        if type_kwargs:

            dtype = type_kwargs.get('dtype')
            if dtype is not None:
                try:
                    dtype = np.dtype(dtype)
                except ValueError:
                    logger.debug('Cannot convert dtype')

            copy = type_kwargs.get('copy')
            if copy is not None:
                if copy == 'False':
                    copy = False
                else:
                    copy = True

            order = type_kwargs.get('order')
            if order is not None:
                if order not in ['K', 'A', 'C', 'F']:
                    # set it to the default value
                    order = 'K'

            subok = type_kwargs.get('subok')
            if subok is not None:
                if subok == 'True':
                    subok = True
                else:
                    subok = False

            ndmin = type_kwargs.get('ndmin')
            if ndmin is not None:
                try:
                    ndmin = int(ndmin)
                except ValueError:
                    logger.debug('Cannot convert ndmin to integer')

            self._type_kwargs = {
                'dtype': dtype,
                'copy': copy,
                'order': order,
                'subok': subok,
                'ndmin': ndmin
                }

    def send_access_state(self):
        """
        Send True for all the widgets using Local Plugin.

        Returns
        -------
        None.

        """
        self.write_access_signal.emit(True)

    def convert_value(self, value, value_type):
        """
        Convert values from string to their appropriate type.

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
                # convert into a numpy array using the extras
                if self._type_kwargs:
                    value_array = np.array(value_list, **self._type_kwargs)
                else:
                    value_array = np.array(value_list)
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
            if self._precision_set is None:
                print('is set....', self._precision_set)
                self.send_precision(self.value)
            else:
                self.prec_signal.emit(self._precision_set)

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
                if self._precision_set is None:
                    self.send_precision(new_value)
                else:
                    self.prec_signal.emit(self._precision_set)


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
