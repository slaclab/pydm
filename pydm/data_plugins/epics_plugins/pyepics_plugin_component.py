import atexit
import logging
import sys
from concurrent.futures import ThreadPoolExecutor

import epics
import numpy as np
from epics.ca import use_initial_context
from pydm.data_plugins import is_read_only
from pydm.data_plugins.plugin import PyDMConnection, PyDMPlugin
from qtpy.QtCore import Qt, Slot
from qtpy.QtWidgets import QApplication

try:
    from epics import utils3

    utils3.EPICS_STR_ENCODING = "latin-1"
except Exception:
    pass

logger = logging.getLogger(__name__)

int_types = set(
    (
        epics.dbr.INT,
        epics.dbr.CTRL_INT,
        epics.dbr.TIME_INT,
        epics.dbr.ENUM,
        epics.dbr.CTRL_ENUM,
        epics.dbr.TIME_ENUM,
        epics.dbr.TIME_LONG,
        epics.dbr.LONG,
        epics.dbr.CTRL_LONG,
        epics.dbr.CHAR,
        epics.dbr.TIME_CHAR,
        epics.dbr.CTRL_CHAR,
        epics.dbr.TIME_SHORT,
        epics.dbr.CTRL_SHORT,
    )
)

float_types = set(
    (
        epics.dbr.CTRL_FLOAT,
        epics.dbr.FLOAT,
        epics.dbr.TIME_FLOAT,
        epics.dbr.CTRL_DOUBLE,
        epics.dbr.DOUBLE,
        epics.dbr.TIME_DOUBLE,
    )
)


class Connection(PyDMConnection):
    def __init__(self, channel, pv, protocol=None, parent=None):
        super().__init__(channel, pv, protocol, parent)
        self.app = QApplication.instance()
        self.pv = epics.PV(
            pv,
            connection_callback=self.send_connection_state,
            form="ctrl",
            auto_monitor=epics.dbr.DBE_VALUE | epics.dbr.DBE_ALARM | epics.dbr.DBE_PROPERTY,
            access_callback=self.send_access_state,
        )
        self._value = None
        self._severity = None
        self._precision = None
        self._enum_strs = None
        self._unit = None
        self._upper_ctrl_limit = None
        self._lower_ctrl_limit = None
        self._upper_alarm_limit = None
        self._lower_alarm_limit = None
        self._upper_warning_limit = None
        self._lower_warning_limit = None
        self._timestamp = None

        PyEPICSPlugin.thread_pool.submit(self.setup_callbacks, channel)

    def setup_callbacks(self, channel):
        use_initial_context()
        self.pv.add_callback(self.send_new_value, with_ctrlvars=True)
        self.add_listener(channel)

    def clear_cache(self):
        self._value = None
        self._severity = None
        self._precision = None
        self._enum_strs = None
        self._unit = None
        self._upper_ctrl_limit = None
        self._lower_ctrl_limit = None
        self._upper_alarm_limit = None
        self._lower_alarm_limit = None
        self._upper_warning_limit = None
        self._lower_warning_limit = None
        self._timestamp = None

    def send_new_value(self, value=None, char_value=None, count=None, ftype=None, *args, **kws):
        self.update_ctrl_vars(**kws)

        if value is not None and not np.array_equal(value, self._value):
            self._value = value
            if isinstance(value, np.ndarray):
                self.new_value_signal[np.ndarray].emit(value)
            else:
                if ftype in int_types:
                    try:
                        self.new_value_signal[int].emit(int(value))
                    except (ValueError, TypeError):  # This happens when a string is empty
                        # HACK since looks like for PyEpics a 1 element array
                        # is in fact a scalar. =( I will try to address this
                        # with Matt Newville
                        self.new_value_signal[str].emit(char_value)
                elif ftype in float_types:
                    self.new_value_signal[float].emit(float(value))
                else:
                    self.new_value_signal[str].emit(char_value)

    def update_ctrl_vars(
        self,
        units=None,
        enum_strs=None,
        severity=None,
        upper_ctrl_limit=None,
        lower_ctrl_limit=None,
        precision=None,
        upper_alarm_limit=None,
        lower_alarm_limit=None,
        upper_warning_limit=None,
        lower_warning_limit=None,
        timestamp=None,
        *args,
        **kws,
    ):
        """Callback invoked when there is a change any of these variables. For a full description see:
        https://cars9.uchicago.edu/software/python/pyepics3/pv.html#user-supplied-callback-functions
        """
        if severity is not None and self._severity != severity:
            self._severity = severity
            self.new_severity_signal.emit(int(severity))
        if precision is not None and self._precision != precision:
            self._precision = precision
            self.prec_signal.emit(precision)
        if enum_strs is not None and self._enum_strs != enum_strs:
            self._enum_strs = enum_strs
            try:
                enum_strs = tuple(b.decode(encoding="ascii") for b in enum_strs)
            except AttributeError:
                pass
            self.enum_strings_signal.emit(enum_strs)
        if units is not None and len(units) > 0 and self._unit != units:
            if isinstance(units, bytes):
                units = units.decode()
            self._unit = units
            self.unit_signal.emit(units)
        if upper_ctrl_limit is not None and self._upper_ctrl_limit != upper_ctrl_limit:
            self._upper_ctrl_limit = upper_ctrl_limit
            self.upper_ctrl_limit_signal.emit(upper_ctrl_limit)
        if lower_ctrl_limit is not None and self._lower_ctrl_limit != lower_ctrl_limit:
            self._lower_ctrl_limit = lower_ctrl_limit
            self.lower_ctrl_limit_signal.emit(lower_ctrl_limit)
        if upper_alarm_limit is not None and self._upper_alarm_limit != upper_alarm_limit:
            self._upper_alarm_limit = upper_alarm_limit
            self.upper_alarm_limit_signal.emit(upper_alarm_limit)
        if lower_alarm_limit is not None and self._lower_alarm_limit != lower_alarm_limit:
            self._lower_alarm_limit = lower_alarm_limit
            self.lower_alarm_limit_signal.emit(lower_alarm_limit)
        if upper_warning_limit is not None and self._upper_warning_limit != upper_warning_limit:
            self._upper_warning_limit = upper_warning_limit
            self.upper_warning_limit_signal.emit(upper_warning_limit)
        if lower_warning_limit is not None and self._lower_warning_limit != lower_warning_limit:
            self._lower_warning_limit = lower_warning_limit
            self.lower_warning_limit_signal.emit(lower_warning_limit)
        if timestamp is not None and self._timestamp != timestamp:
            self._timestamp = timestamp
            self.timestamp_signal.emit(timestamp)

    def send_access_state(self, read_access, write_access, *args, **kws):
        if is_read_only():
            self.write_access_signal.emit(False)
            return

        if write_access is not None:
            self.write_access_signal.emit(write_access)

    def reload_access_state(self):
        read_access = epics.ca.read_access(self.pv.chid)
        write_access = epics.ca.write_access(self.pv.chid)
        self.send_access_state(read_access, write_access)

    def send_connection_state(self, conn=None, *args, **kws):
        self.connected = conn
        self.connection_state_signal.emit(conn)
        if conn:
            self.clear_cache()
            if hasattr(self, "pv"):
                self.reload_access_state()
                self.pv.run_callbacks()

    @Slot(int)
    @Slot(float)
    @Slot(str)
    @Slot(np.ndarray)
    def put_value(self, new_val):
        if is_read_only():
            return

        if self.pv.write_access:
            try:
                self.pv.put(new_val)
            except Exception as e:
                logger.exception("Unable to put %s to %s.  Exception: %s", new_val, self.pv.pvname, str(e))

    def add_listener(self, channel):
        super().add_listener(channel)
        # If we are adding a listener to an already existing PV, we need to
        # manually send the signals indicating that the PV is connected, what the latest value is, etc.
        if epics.ca.isConnected(self.pv.chid):
            self.send_connection_state(conn=True)
            self.pv.run_callbacks()
        else:
            self.send_connection_state(conn=False)
        # If the channel is used for writing to PVs, hook it up to the 'put' methods.
        if channel.value_signal is not None:
            for signal_type in (str, int, float, np.ndarray):
                try:
                    channel.value_signal[signal_type].connect(self.put_value, Qt.QueuedConnection)
                # When signal type can't be found, PyQt5 throws KeyError here, but PySide6 index error.
                # If signal type exists but doesn't match the slot, TypeError gets thrown.
                except (KeyError, IndexError, TypeError):
                    pass

    def close(self):
        try:
            self.pv.clear_callbacks()
            self.pv.access_callbacks = []
            self.pv.connection_callbacks = []
            self.pv.disconnect()
        except KeyError:
            # The PV was no longer available.
            pass


class PyEPICSPlugin(PyDMPlugin):
    # NOTE: protocol is intentionally "None" to keep this plugin from getting directly imported.
    # If this plugin is chosen as the One True EPICS Plugin in epics_plugin.py, the protocol will
    # be properly set before it is used.
    protocol = None
    connection_class = Connection
    thread_pool = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Not the end of the world if this happens twice, but better not to
        if PyEPICSPlugin.thread_pool is None:
            thread_pool = ThreadPoolExecutor()
            if sys.version_info >= (3, 9):
                atexit.register(thread_pool.shutdown, wait=False, cancel_futures=True)
            else:
                atexit.register(thread_pool.shutdown, wait=False)
            # Class variable for connections to use
            # This is the easiest way to share state
            PyEPICSPlugin.thread_pool = thread_pool
