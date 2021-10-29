"""Local Plugin."""
import decimal
import logging
import ast
import numpy as np

try:
    from urllib import parse  # Python 3
except ImportError:
    import urlparse as parse

from qtpy.QtCore import Slot, Qt
from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection

logger = logging.getLogger(__name__)


class Connection(PyDMConnection):
    def __init__(self, channel, address, protocol=None, parent=None):
        self._is_connection_configured = False
        self._value_type = None
        self._precision_set = None
        self._type_kwargs = {}

        self._required_config_keys = [
            'name',
            'type',
            'init'
        ]

        self._extra_config_keys = [
            "precision",
            "unit",
            "upper_limit",
            "lower_limit",
            "enum_string"
        ]

        self._data_types = {
            'int': int,
            'float': float,
            'str': str,
            'bool': bool,
            'array': np.array
        }

        self._precision = None
        self._unit = None
        self._upper_limit = None
        self._lower_limit = None
        self._enum_string = None

        super(Connection, self).__init__(channel, address, protocol, parent)
        self._configuration = {}
        self.add_listener(channel)
        self.send_connection_state(False)
        self.send_access_state()
        self.connected = False

    def _configure_local_plugin(self, channel):
        if self._is_connection_configured:
            logger.debug('LocalPlugin connection already configured.')
            return

        try:
            url_data = UrlToPython(channel).get_info()
        except ValueError("Not enough information"):
            logger.debug('Invalid configuration for LocalPlugin connection', exc_info=True)
            return

        self._configuration['name'] = url_data[1]
        address = url_data[2]

        if url_data[0] is not None:
            self._configuration.update(url_data[0])
            self.address = address

            # set the object's attributes
            init_value = self._configuration.get('init')[0]
            self._value_type = self._configuration.get('type')[0]
            self.name = self._configuration.get('name')

            # get the extra info if any
            self.parse_channel_extras(self._configuration)

            # send initial values
            self.value = self.convert_value(init_value, self._value_type)
            self.connected = True
            self.send_connection_state(True)
            self.send_new_value(self.value)

            # set connection configured to true
            self._is_connection_configured = True

    def parse_channel_extras(self, extras):
        """
        Parse the extras dictionary and either pass the data
        to the appropriate methods that will take care of it,
        or emit it right away.

        Parameters
        ----------
        extras : dict
            Dictionary containing extra parameters for the
            this local variable configuration
            These parameters are optional

        Returns
        -------
        None.

        """

        precision = extras.get('precision')
        if precision is not None:
            try:
                self._precision_set = int(precision[0])
                self.prec_signal.emit(self._precision_set)
            except ValueError:
                logger.debug('Cannot convert precision value=%r', precision)
        unit = extras.get('unit')
        if unit is not None:
            self.unit_signal.emit(str(unit[0]))
        upper_limit = extras.get('upper_limit')
        if upper_limit is not None and (self._value_type == 'float' or self._value_type == 'int'):
            self.send_upper_limit(upper_limit[0])
        lower_limit = extras.get('lower_limit')
        if lower_limit is not None and (self._value_type == 'float' or self._value_type == 'int'):
            self.send_lower_limit(lower_limit[0])
        enum_string = extras.get('enum_string')
        if enum_string is not None:
            self.send_enum_string(enum_string[0])

        type_kwargs = {k: v for k, v in extras.items()
                       if k not in self._extra_config_keys and k not in self._required_config_keys}

        if type_kwargs:
            self.format_type_params(type_kwargs)

    @Slot(int)
    @Slot(float)
    @Slot(str)
    @Slot(bool)
    @Slot(np.ndarray)
    def send_new_value(self, value):
        """
        Send the values sent through a specific local
        variable channel to all its listeners.
        """

        if value is not None:
            self.new_value_signal[type(value)].emit(value)

    def send_precision(self, value):
        """
        Calculate and send the precision for float values if precision
        is not specified in the extras

        Parameters
        ----------
        value : int
            The value to be sent,should be sent as int

        Returns
        -------
        None.

        """
        if value is not None:
            self._precision = self.precision_for_value(value)
            self.prec_signal.emit(self._precision)

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
            self._unit = str(unit)
            self.prec_signal.emit(self.unit)

    def send_upper_limit(self, upper_limit):
        """
        Send the upper limit value as float or int.

        Parameters
        ----------
        upper_limit : int or float

        Returns
        -------
        None.

        """
        if upper_limit is not None:
            if self._value_type == "int":
                self._upper_limit = int(upper_limit)
            else:
                self._upper_limit = float(upper_limit)

            self.upper_ctrl_limit_signal.emit(self._upper_limit)

    def send_lower_limit(self, lower_limit):
        """
        Send the lower limit value as float or int.

        Parameters
        ----------
        lower_limit : int, float, or str

        Returns
        -------
        None.

        """
        if lower_limit is not None:
            if self._value_type == "int":
                self._lower_limit = int(lower_limit)
            else:
                self._lower_limit = float(lower_limit)

            self.lower_ctrl_limit_signal.emit(self._lower_limit)

    def send_enum_string(self, enum_string):
        """
        Send enum_string as tuple of strings.

        Parameters
        ----------
        enum_string : int or float

        Returns
        -------
        None.

        """
        if enum_string is not None:
            try:
                self._enum_string = tuple(ast.literal_eval(enum_string))
                self.enum_strings_signal.emit(self._enum_string)
            except ValueError:
                logger.debug("Error when converting enum_string")

    def format_type_params(self, type_kwargs):
        """
        Format value_type parameters.

        Parameters
        ----------
        type_kwargs : dict

        Returns
        -------
            dict

        """

        dtype = type_kwargs.get('dtype')

        if dtype is not None:
            dtype = dtype[0]
            try:
                self._type_kwargs['dtype'] = np.dtype(dtype)
                return self._type_kwargs
            except TypeError:
                logger.debug('Cannot convert dtype value=%r', dtype)
        else:
            dtype = 'object'
            try:
                self._type_kwargs['dtype'] = np.dtype(dtype)
                return self._type_kwargs
            except TypeError:
                logger.debug('Cannot convert dtype value=%r', dtype)

        return self._type_kwargs

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
        Convert values to their appropriate types.

        Parameters
        ----------
        value :
            Data for this variable.
        value_type : str
            Data type intended for this variable.

        Returns
        -------
            The data for this variable converted to its appropriate type

        """

        _type = self._data_types.get(value_type)
        if _type is not None:
            try:
                if value_type == "array":
                    value = ast.literal_eval(value)
                return _type(value, **self._type_kwargs)
            except ValueError:
                logger.debug('Cannot convert value_type')
        else:
            return None

    def send_connection_state(self, conn):
        self.connected = conn
        self.connection_state_signal.emit(conn)

    def add_listener(self, channel):
        super(Connection, self).add_listener(channel)
        self._configure_local_plugin(channel)
        # send write access == True to the listeners
        self.send_access_state()
        # send new values to the listeners right away
        self.send_new_value(self.value)
        # send the precision in case of float values
        if isinstance(self.value, float):
            if self._precision_set is None:
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
        Slot connected to the channel.value_signal.
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

    @staticmethod
    def precision_for_value(value, max_precision=8):
        dec = decimal.Decimal(str(value))
        solution = min((len(str(dec).split('.')[1]), max_precision))
        return solution


class LocalPlugin(PyDMPlugin):
    protocol = "loc"
    connection_class = Connection

    @staticmethod
    def get_connection_id(channel):
        obj = UrlToPython(channel)
        name = obj.get_info()[1]
        return name


class UrlToPython:
    def __init__(self, channel):
        self.channel = channel

    def get_info(self):
        """
        Parses a given url into a list and a string.

        Parameters
        ----------

        Returns
        -------
        A tuple: (<list>, <str>)
        """
        address = PyDMPlugin.get_address(self.channel)
        address = "loc://" + address
        name = None
        config = None

        try:
            config = parse.parse_qs(parse.urlsplit(address).query)
            name = parse.urlsplit(address).netloc

            if not name or not config:
                raise
            elif config['init'] is None or config['type'] is None:
                raise
        except Exception:
            try:
                if not name:
                    raise
                logger.debug('LocalPlugin connection %s got new listener.', address)
                return None, name, address
            except Exception:
                msg = "Invalid configuration for LocalPlugin connection. %s"
                logger.exception(msg, address, exc_info=True)
                raise ValueError("error in local data plugin input")

        return config, name, address
