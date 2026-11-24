"""
Data plugin for Tango Controls (https://www.tango-controls.org), based on PyTango.

Channel address syntax::

    tango://domain/family/member/attribute
    tango://host:port/domain/family/member/attribute
    tango://host:port/domain/family/member/attribute#dbase=no
    tango://device_alias/attribute
    tango://domain/family/member/attribute?w_value
    tango://domain/family/member/command
    tango://domain/family/member/command?argout

With ``?w_value``, the channel receives the write value (setpoint) of the attribute instead of the
read value, with every update of the read value. Writing to such a channel writes the attribute as usual.

If the device has no attribute of the given name, but a command, the channel executes the command
whenever a value is written to it, with that value as the input argument. It never executes the
command by itself. Its value is the last input argument, or a neutral value of the input type before
the first execution. With ``?argout``, the channel is read only and receives the output argument
every time the command is executed from this application.

Values are received through Tango change events. If the attribute is not configured to send
change events, the plugin falls back to polling the attribute from the client side every
``PYDM_TANGO_POLL_PERIOD`` milliseconds (default: 1000).
"""

import atexit
import logging
import os
import re
import sys
import threading
import time
import weakref
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import tango
from tango.utils import is_array_type, is_bool_type, is_float_type, is_int_type, is_str_type
from qtpy.compat import isalive
from qtpy.QtCore import Qt, QTimer, Signal, Slot

from pydm.data_plugins import is_read_only
from pydm.data_plugins.plugin import PyDMConnection, PyDMPlugin

logger = logging.getLogger(__name__)

POLL_PERIOD = int(os.getenv("PYDM_TANGO_POLL_PERIOD", 1000))

# Error reasons telling us that the attribute exists, but does not send change events
NO_EVENT_REASONS = ("API_AttributePollingNotStarted", "API_EventPropertiesNotSet")

NOT_SPECIFIED = ("", "Not specified", "No unit")

# Map Tango attribute quality onto PyDM alarm severity
QUALITY_TO_SEVERITY = {
    tango.AttrQuality.ATTR_VALID: 0,
    tango.AttrQuality.ATTR_CHANGING: 0,
    tango.AttrQuality.ATTR_WARNING: 1,
    tango.AttrQuality.ATTR_ALARM: 2,
    tango.AttrQuality.ATTR_INVALID: 3,
}

WRITABLE_TYPES = (
    tango.AttrWriteType.WRITE,
    tango.AttrWriteType.READ_WRITE,
    tango.AttrWriteType.READ_WITH_WRITE,
)

# PyTango >= 10.1 replaces the 'stateless' flag by the 'sub_mode' parameter
if hasattr(tango, "EventSubMode"):
    STATELESS = {"sub_mode": tango.EventSubMode.Stateless}
else:
    STATELESS = {"stateless": True}

# Input arguments of these types cannot be entered with PyDM widgets
STRUCT_TYPES = (tango.CmdArgType.DevVarLongStringArray, tango.CmdArgType.DevVarDoubleStringArray)

STATE_NAMES = tuple(name for name, _ in sorted(tango.DevState.names.items(), key=lambda item: int(item[1])))
BOOL_NAMES = ("False", "True")


def split_address(address):
    """
    Split a PyDM tango address into the Tango device name and the attribute name.

    Parameters
    ----------
    address : str
        The address without the protocol, e.g. ``host:10000/sys/tg_test/1/double_scalar#dbase=no``

    Returns
    -------
    device_name : str
    attribute_name : str
    """
    address, _, fragment = address.partition("#")
    device_name, _, attribute_name = address.rpartition("/")
    if not device_name or not attribute_name:
        raise ValueError("Invalid Tango address {!r}, expected <device>/<attribute>".format(address))
    if ":" in device_name.split("/")[0]:
        device_name = "tango://" + device_name
    if fragment:
        device_name += "#" + fragment
    return device_name, attribute_name


def neutral_value(data_type):
    """
    The value a command channel has before the command was executed, or None if the type cannot be written.

    PyDM write widgets only send values once they received one, and convert user input into its type.
    """
    if data_type in STRUCT_TYPES:
        return None
    if is_array_type(data_type):
        return np.array([], dtype=str if is_str_type(data_type) else float)
    if is_float_type(data_type):
        return 0.0
    if is_str_type(data_type):
        return ""
    # DevVoid, integers, DevUChar, DevBoolean and DevState
    return 0


def convert_argin(data_type, value):
    """
    Convert a value from a PyDM widget into the input type of a command.

    Unlike write_attribute, command_inout does not convert e.g. the float sent by a PyDMSpinbox into an integer.
    """
    if is_array_type(data_type):
        return np.asarray(value)
    if is_int_type(data_type) or data_type == tango.CmdArgType.DevUChar:
        if float(value) != int(float(value)):
            raise ValueError("{!r} is not an integer".format(value))
        return int(float(value))
    if is_bool_type(data_type):
        return bool(value)
    if is_float_type(data_type):
        return float(value)
    if is_str_type(data_type):
        return str(value)
    return value


def parse_number(text):
    """Convert a Tango configuration string into a float, or None if it is not specified."""
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def parse_precision(fmt):
    """Extract the precision from a printf-like Tango format string, e.g. '%6.2f' -> 2."""
    match = re.search(r"%[^.]*\.(\d+)", fmt or "")
    if match:
        return int(match.group(1))
    return None


def find_command(proxy, name):
    """
    Return the CommandInfo if the device has a command, but no attribute of this name, else None.

    Tango names are case insensitive. State and Status are attributes and commands, the attributes win.
    """
    if name.lower() in (attribute.lower() for attribute in proxy.get_attribute_list()):
        return None
    if name.lower() in (command.lower() for command in proxy.get_command_list()):
        return proxy.command_query(name)
    return None


class Connection(PyDMConnection):
    _start_timer_signal = Signal()
    _stop_timer_signal = Signal()

    # The ?argout connections of each command, by (device name, command name)
    _argout_listeners = {}

    def __init__(self, channel, address, protocol=None, parent=None):
        super().__init__(channel, address, protocol, parent)
        address, _, query = address.partition("?")
        # In the standard order "attr?w_value#dbase=no" the fragment ends up in the query
        query, _, fragment = query.partition("#")
        if fragment:
            address += "#" + fragment
        self.device_name, self.attribute_name = split_address(address)
        self.use_w_value = "w_value" in query.split("&")
        self.use_argout = "argout" in query.split("&")
        self.proxy = None
        # The CommandInfo if the address is a command, None for attributes
        self._command = None
        self._event_ids = {}
        self._polling = False
        self._closed = False
        self._lock = threading.Lock()
        self._busy = threading.Lock()

        self._data_type = None
        self._value = None
        self._severity = None
        self._timestamp = None
        self._config = None

        # Tango callbacks come from Tango's threads, so the timer is controlled through queued signals
        self._timer = QTimer(self)
        self._timer.setInterval(POLL_PERIOD)
        self._timer.timeout.connect(self._on_timer)
        self._start_timer_signal.connect(self._timer.start, Qt.QueuedConnection)
        self._stop_timer_signal.connect(self._timer.stop, Qt.QueuedConnection)

        self.add_listener(channel)
        TangoPlugin.thread_pool.submit(self._setup)

    def _setup(self):
        """Create the DeviceProxy and subscribe to events. Runs in the thread pool since it blocks."""
        with self._lock:
            if self._closed:
                return
            try:
                proxy = tango.DeviceProxy(self.device_name)
                command = find_command(proxy, self.attribute_name)
            except tango.DevFailed as e:
                logger.error("Unable to connect to Tango device %s: %s", self.device_name, e.args[0].desc)
                self.send_connection_state(False)
                self._start_timer_signal.emit()
                return
            self.proxy = proxy
            if command is not None:
                self._setup_command(command)
                return
            self._stop_timer_signal.emit()
            # Stateless subscriptions report most errors to the callbacks, and Tango keeps retrying in the
            # background, which also handles devices that are currently down.
            for event_type, callback in (
                (tango.EventType.ATTR_CONF_EVENT, self._on_config_event),
                (tango.EventType.CHANGE_EVENT, self._on_change_event),
            ):
                try:
                    self._event_ids[event_type] = self.proxy.subscribe_event(
                        self.attribute_name, event_type, callback, **STATELESS
                    )
                except tango.DevFailed as e:
                    # Rarely raised anyway, e.g. "Could not find event consumer" when many subscriptions
                    # start at once. Start over with a new proxy, otherwise the attribute never updates.
                    logger.warning("Unable to subscribe to %s, retrying: %s", self.address, e.args[0].desc)
                    self._unsubscribe_events()
                    self.proxy = None
                    self._start_timer_signal.emit()
                    return

    def _setup_command(self, command):
        self._command = command
        self._data_type = command.out_type if self.use_argout else command.in_type
        if self.use_argout:
            Connection._argout_listeners.setdefault(self._command_key(), weakref.WeakSet()).add(self)
        self.send_command_enum_strings()
        # Commands send no events, so the connection state is checked by pinging the device
        self._polling = True
        self._command_connected()
        self._start_timer_signal.emit()

    def send_command_enum_strings(self):
        if self._data_type == tango.CmdArgType.DevState:
            self.enum_strings_signal.emit(STATE_NAMES)
        elif is_bool_type(self._data_type):
            self.enum_strings_signal.emit(BOOL_NAMES)

    def _command_key(self):
        return self.device_name.lower(), self.attribute_name.lower()

    def _command_connected(self):
        self.send_connection_state(True)
        if self._value is None and not self.use_argout:
            value = neutral_value(self._command.in_type)
            if value is not None:
                self._value = value
                self.emit_value(value)

    def _ping(self):
        try:
            self.proxy.ping()
        except tango.DevFailed as e:
            if self.connected:
                logger.warning("Lost connection to %s: %s", self.device_name, e.args[0].desc)
            self.send_connection_state(False)
            return
        self._command_connected()

    def _on_timer(self):
        TangoPlugin.thread_pool.submit(self._poll)

    def _poll(self):
        # Skip this cycle if the previous one is still running, e.g. because of a slow device
        if not self._busy.acquire(blocking=False):
            return
        try:
            if self.proxy is None:
                self._setup()
            elif self._command is not None:
                self._ping()
            elif self._polling:
                self._read()
        finally:
            self._busy.release()

    def _read(self):
        try:
            attr_value = self.proxy.read_attribute(self.attribute_name)
        except tango.DevFailed as e:
            if self.connected:
                logger.warning("Unable to read %s: %s", self.address, e.args[0].desc)
            self.send_connection_state(False)
            return
        if self._config is None:
            try:
                self.send_config(self.proxy.get_attribute_config(self.attribute_name))
            except tango.DevFailed:
                pass
        self.send_connection_state(True)
        self.send_new_value(attr_value)

    def _on_change_event(self, event):
        self._handle_event(self._change_event, event)

    def _on_config_event(self, event):
        self._handle_event(self._config_event, event)

    def _handle_event(self, handler, event):
        """Tango calls this from its own threads, possibly after Qt deleted this object on exit."""
        if self._closed:
            return
        try:
            handler(event)
        except RuntimeError:
            if isalive(self):
                raise
            self._closed = True

    def _change_event(self, event):
        if not event.err:
            self.send_connection_state(True)
            self.send_new_value(event.attr_value)
            return
        reason = event.errors[0].reason
        if reason in NO_EVENT_REASONS:
            if not self._polling:
                logger.info("%s does not send change events, polling every %d ms", self.address, POLL_PERIOD)
                self._polling = True
                TangoPlugin.thread_pool.submit(self._unsubscribe_change_event)
                TangoPlugin.thread_pool.submit(self._poll)
                self._start_timer_signal.emit()
        else:
            if self.connected:
                logger.warning("Lost connection to %s: %s", self.address, event.errors[0].desc)
            self.send_connection_state(False)

    def _unsubscribe_change_event(self):
        # Runs after _setup released the lock, so the id of the subscription is known by now
        with self._lock:
            event_id = self._event_ids.pop(tango.EventType.CHANGE_EVENT, None)
            if event_id is not None:
                try:
                    self.proxy.unsubscribe_event(event_id)
                except tango.DevFailed:
                    pass

    def _config_event(self, event):
        if not event.err:
            self.send_config(event.attr_conf)

    def send_connection_state(self, conn):
        if conn == self.connected:
            return
        self.connected = conn
        self.connection_state_signal.emit(conn)
        if conn:
            self.send_write_access()
        else:
            # Make sure everything is sent again once we reconnect
            self._value = None
            self._severity = None

    def send_write_access(self):
        if self._command is not None:
            writable = not self.use_argout and self._command.in_type not in STRUCT_TYPES
        else:
            writable = self._config is not None and self._config.writable in WRITABLE_TYPES
        self.write_access_signal.emit(writable and self.connected and not is_read_only())

    def send_new_value(self, attr_value):
        self._data_type = attr_value.type
        self._timestamp = attr_value.time.totime()
        self.timestamp_signal.emit(self._timestamp)

        severity = QUALITY_TO_SEVERITY.get(attr_value.quality, 0)
        if severity != self._severity:
            self._severity = severity
            self.new_severity_signal.emit(severity)

        value = attr_value.w_value if self.use_w_value else attr_value.value
        if value is None:
            # e.g. quality ATTR_INVALID, or a read only attribute asked for its w_value
            return
        if attr_value.data_format != tango.AttrDataFormat.SCALAR:
            value = np.asarray(value)
        # The write value is sent with every update of the read value, even if unchanged, so that
        # e.g. a time plot shows the setpoint over time next to the readback
        if not self.use_w_value and self._value is not None and np.array_equal(value, self._value):
            return
        self._value = value
        self.emit_value(value)

    def send_argout(self, argout):
        """Send the output argument of the command, executed by any connection to it."""
        if argout is None:
            return
        self._timestamp = time.time()
        self.timestamp_signal.emit(self._timestamp)
        if is_array_type(self._data_type) and self._data_type not in STRUCT_TYPES:
            argout = np.asarray(argout)
        self._value = argout
        self.emit_value(argout)

    def emit_value(self, value):
        data_type = self._data_type
        if isinstance(value, np.ndarray):
            self.new_value_signal[np.ndarray].emit(value)
        elif data_type == tango.CmdArgType.DevVoid:
            # The neutral value of a command without input
            self.new_value_signal[int].emit(int(value))
        elif data_type in (tango.CmdArgType.DevState, tango.CmdArgType.DevEnum, tango.CmdArgType.DevBoolean):
            self.new_value_signal[int].emit(int(value))
        elif is_int_type(data_type) or data_type == tango.CmdArgType.DevUChar:
            # PyTango does not count DevUChar as an integer type
            self.new_value_signal[int].emit(int(value))
        elif is_float_type(data_type):
            self.new_value_signal[float].emit(float(value))
        elif is_str_type(data_type):
            self.new_value_signal[str].emit(str(value))
        else:
            self.new_value_signal[object].emit(value)

    def send_config(self, config):
        """Send the metadata from an AttributeInfoEx to the listeners."""
        self._config = config
        self.send_write_access()

        if config.data_type == tango.CmdArgType.DevState:
            self.enum_strings_signal.emit(STATE_NAMES)
        elif config.data_type == tango.CmdArgType.DevBoolean:
            self.enum_strings_signal.emit(BOOL_NAMES)
        elif config.data_type == tango.CmdArgType.DevEnum:
            self.enum_strings_signal.emit(tuple(config.enum_labels))

        if config.unit not in NOT_SPECIFIED:
            self.unit_signal.emit(config.unit)

        precision = parse_precision(config.format)
        if precision is not None:
            self.prec_signal.emit(precision)

        for signal, text in (
            (self.upper_ctrl_limit_signal, config.max_value),
            (self.lower_ctrl_limit_signal, config.min_value),
            (self.upper_alarm_limit_signal, config.alarms.max_alarm),
            (self.lower_alarm_limit_signal, config.alarms.min_alarm),
            (self.upper_warning_limit_signal, config.alarms.max_warning),
            (self.lower_warning_limit_signal, config.alarms.min_warning),
        ):
            limit = parse_number(text)
            if limit is not None:
                signal.emit(limit)

    @Slot(int)
    @Slot(float)
    @Slot(str)
    @Slot(np.ndarray)
    def put_value(self, new_val):
        if is_read_only() or self.proxy is None:
            return
        if self._command is not None:
            if not self.use_argout:
                TangoPlugin.thread_pool.submit(self._execute, new_val)
            return
        TangoPlugin.thread_pool.submit(self._write, new_val)

    def _execute(self, argin):
        in_type = self._command.in_type
        try:
            if in_type == tango.CmdArgType.DevVoid:
                argout = self.proxy.command_inout(self.attribute_name)
            else:
                argin = convert_argin(in_type, argin)
                argout = self.proxy.command_inout(self.attribute_name, argin)
        except (tango.DevFailed, TypeError, ValueError) as e:
            desc = e.args[0].desc if isinstance(e, tango.DevFailed) else str(e)
            logger.error("Unable to execute %s with %r: %s", self.address, argin, desc)
            return
        if in_type != tango.CmdArgType.DevVoid:
            # Like the write value of an attribute, the channel shows the last input argument
            self._value = argin
            self.emit_value(argin)
        for connection in list(Connection._argout_listeners.get(self._command_key(), ())):
            connection.send_argout(argout)

    def _write(self, new_val):
        try:
            self.proxy.write_attribute(self.attribute_name, new_val)
        except (tango.DevFailed, TypeError, ValueError) as e:
            desc = e.args[0].desc if isinstance(e, tango.DevFailed) else str(e)
            logger.error("Unable to write %r to %s: %s", new_val, self.address, desc)
            return
        if self._polling:
            self._poll()

    def add_listener(self, channel):
        super().add_listener(channel)
        # Send the cached state, so that a new listener on an existing connection is up to date
        self.connection_state_signal.emit(self.connected)
        if self._config is not None:
            self.send_config(self._config)
        if self._command is not None:
            self.send_write_access()
            self.send_command_enum_strings()
        if self._severity is not None:
            self.new_severity_signal.emit(self._severity)
        if self._timestamp is not None:
            self.timestamp_signal.emit(self._timestamp)
        if self._value is not None:
            self.emit_value(self._value)
        # If the channel is used for writing, hook it up to the 'put' method.
        if channel.value_signal is not None:
            for signal_type in (str, int, float, np.ndarray):
                try:
                    channel.value_signal[signal_type].connect(self.put_value, Qt.QueuedConnection)
                # When signal type can't be found, PyQt5 throws KeyError here, but PySide6 index error.
                # If signal type exists but doesn't match the slot, TypeError gets thrown.
                except (KeyError, IndexError, TypeError):
                    pass

    def close(self):
        self._closed = True
        listeners = Connection._argout_listeners.get(self._command_key())
        if listeners is not None:
            listeners.discard(self)
        if isalive(self._timer):
            self._timer.stop()
        try:
            TangoPlugin.thread_pool.submit(self._unsubscribe_all)
        except RuntimeError:
            # The thread pool is already shut down when the application exits
            pass

    def _unsubscribe_all(self):
        with self._lock:
            self._unsubscribe_events()

    def _unsubscribe_events(self):
        for event_id in self._event_ids.values():
            try:
                self.proxy.unsubscribe_event(event_id)
            except (tango.DevFailed, KeyError):
                pass
        self._event_ids = {}


class TangoPlugin(PyDMPlugin):
    protocol = "tango"
    connection_class = Connection
    thread_pool = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if TangoPlugin.thread_pool is None:
            thread_pool = ThreadPoolExecutor(thread_name_prefix="pydm-tango")
            if sys.version_info >= (3, 9):
                atexit.register(thread_pool.shutdown, wait=False, cancel_futures=True)
            else:
                atexit.register(thread_pool.shutdown, wait=False)
            TangoPlugin.thread_pool = thread_pool

    @staticmethod
    def get_address(channel):
        # Tango names contain slashes, so the address is the full 'netloc/path', not only the netloc.
        # The query selects e.g. the write value, so it is part of the address as well.
        address = PyDMPlugin.get_full_address(channel)
        query = PyDMPlugin.get_parsed_address(channel).query
        return address + "?" + query if query else address

    @staticmethod
    def get_connection_id(channel):
        return TangoPlugin.get_address(channel)
