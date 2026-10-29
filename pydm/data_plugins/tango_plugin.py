"""
Data plugin for Tango Controls (https://www.tango-controls.org), based on PyTango.

Channel address syntax::

    tango://domain/family/member/attribute
    tango://host:port/domain/family/member/attribute
    tango://host:port/domain/family/member/attribute#dbase=no
    tango://device_alias/attribute
    tango://domain/family/member/attribute?w_value

With ``?w_value``, the channel receives the write value (setpoint) of the attribute instead of the
read value, with every update of the read value. Writing to such a channel writes the attribute as usual.

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
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import tango
from tango.utils import is_float_type, is_int_type, is_str_type
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


class Connection(PyDMConnection):
    _start_timer_signal = Signal()
    _stop_timer_signal = Signal()

    def __init__(self, channel, address, protocol=None, parent=None):
        super().__init__(channel, address, protocol, parent)
        address, _, query = address.partition("?")
        self.device_name, self.attribute_name = split_address(address)
        self.use_w_value = "w_value" in query.split("&")
        self.proxy = None
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
                self.proxy = tango.DeviceProxy(self.device_name)
            except tango.DevFailed as e:
                logger.error("Unable to connect to Tango device %s: %s", self.device_name, e.args[0].desc)
                self.send_connection_state(False)
                self._start_timer_signal.emit()
                return
            self._stop_timer_signal.emit()
            # Stateless subscriptions do not raise; errors are delivered to the callbacks and Tango
            # keeps retrying in the background, which also handles devices that are currently down.
            for event_type, callback in (
                (tango.EventType.ATTR_CONF_EVENT, self._on_config_event),
                (tango.EventType.CHANGE_EVENT, self._on_change_event),
            ):
                try:
                    self._event_ids[event_type] = self.proxy.subscribe_event(
                        self.attribute_name, event_type, callback, **STATELESS
                    )
                except tango.DevFailed as e:
                    logger.error("Unable to subscribe to %s: %s", self.address, e.args[0].desc)

    def _on_timer(self):
        TangoPlugin.thread_pool.submit(self._poll)

    def _poll(self):
        # Skip this cycle if the previous one is still running, e.g. because of a slow device
        if not self._busy.acquire(blocking=False):
            return
        try:
            if self.proxy is None:
                self._setup()
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

    def emit_value(self, value):
        data_type = self._data_type
        if isinstance(value, np.ndarray):
            self.new_value_signal[np.ndarray].emit(value)
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
        TangoPlugin.thread_pool.submit(self._write, new_val)

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
        if isalive(self._timer):
            self._timer.stop()
        try:
            TangoPlugin.thread_pool.submit(self._unsubscribe_all)
        except RuntimeError:
            # The thread pool is already shut down when the application exits
            pass

    def _unsubscribe_all(self):
        with self._lock:
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
