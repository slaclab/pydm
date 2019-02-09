import caproto.threading.pyepics_compat as epics
from caproto import SubscriptionType
import logging
import numpy as np
from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection
from qtpy.QtCore import Slot, Qt
from qtpy.QtWidgets import QApplication
from pydm.data_plugins import is_read_only

logger = logging.getLogger(__name__)

int_types = set((epics.ChannelType.INT, epics.ChannelType.CTRL_INT, epics.ChannelType.TIME_INT,
                 epics.ChannelType.ENUM, epics.ChannelType.CTRL_ENUM, epics.ChannelType.TIME_ENUM,
                 epics.ChannelType.TIME_LONG, epics.ChannelType.LONG, epics.ChannelType.CTRL_LONG,
                 epics.ChannelType.CHAR, epics.ChannelType.TIME_CHAR, epics.ChannelType.CTRL_CHAR))

float_types = set((epics.ChannelType.CTRL_FLOAT, epics.ChannelType.FLOAT, epics.ChannelType.TIME_FLOAT,
                   epics.ChannelType.CTRL_DOUBLE, epics.ChannelType.DOUBLE, epics.ChannelType.TIME_DOUBLE))


class Connection(PyDMConnection):

    def __init__(self, channel, pv, protocol=None, parent=None):
        super(Connection, self).__init__(channel, pv, protocol, parent)
        self.app = QApplication.instance()
        self._value = None
        self._severity = None
        self._precision = None
        self._enum_strs = None
        self._unit = None
        self._upper_ctrl_limit = None
        self._lower_ctrl_limit = None

        self.pv = epics.get_pv(pv, connection_callback=self.send_connection_state, form='ctrl', auto_monitor=SubscriptionType.DBE_VALUE|SubscriptionType.DBE_ALARM|SubscriptionType.DBE_PROPERTY, access_callback=self.send_access_state)
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

    def send_new_value(self, value=None, char_value=None, count=None, typefull=None, type=None, *args, **kws):
        self.update_ctrl_vars(**kws)

        if value is not None and not np.array_equal(value, self._value):
            self._value = value
            if isinstance(value, np.ndarray):
                self.new_value_signal[np.ndarray].emit(value)
            else:
                if typefull in int_types:
                    try:
                        self.new_value_signal[int].emit(int(value))
                    except ValueError:  # This happens when a string is empty
                        # HACK since looks like for PyEpics a 1 element array
                        # is in fact a scalar. =( I will try to address this
                        # with Matt Newville
                        self.new_value_signal[str].emit(char_value)
                elif typefull in float_types:
                    self.new_value_signal[float].emit(float(value))
                else:
                    self.new_value_signal[str].emit(char_value)

    def update_ctrl_vars(self, units=None, enum_strs=None, severity=None, upper_ctrl_limit=None, lower_ctrl_limit=None, precision=None, *args, **kws):
        if severity is not None and self._severity != severity:
            self._severity = severity
            self.new_severity_signal.emit(int(severity))
        if precision is not None and self._precision != precision:
            self._precision = precision
            self.prec_signal.emit(precision)
        if enum_strs is not None and self._enum_strs != enum_strs:
            self._enum_strs = enum_strs
            try:
                enum_strs = tuple(b.decode(encoding='ascii') for b in enum_strs)
            except AttributeError:
                pass
            self.enum_strings_signal.emit(enum_strs)
        if units is not None and len(units) > 0 and self._unit != units:
            if type(units) == bytes:
                units = units.decode()
            self._unit = units
            self.unit_signal.emit(units)
        if upper_ctrl_limit is not None and self._upper_ctrl_limit != upper_ctrl_limit:
            self._upper_ctrl_limit = upper_ctrl_limit
            self.upper_ctrl_limit_signal.emit(upper_ctrl_limit)
        if lower_ctrl_limit is not None and self._lower_ctrl_limit != lower_ctrl_limit:
            self._lower_ctrl_limit = lower_ctrl_limit
            self.lower_ctrl_limit_signal.emit(lower_ctrl_limit)

    def send_access_state(self, read_access, write_access, *args, **kws):
        if is_read_only():
            self.write_access_signal.emit(False)
            return

        if write_access is not None:
            self.write_access_signal.emit(write_access)

    def reload_access_state(self):
        read_access = self.pv.read_access
        write_access = self.pv.write_access
        self.send_access_state(read_access, write_access)

    def send_connection_state(self, conn=None, *args, **kws):
        self.connected = conn
        self.connection_state_signal.emit(conn)
        if conn:
            self.clear_cache()
            if hasattr(self, 'pv'):
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
                logger.exception("Unable to put %s to %s.  Exception: %s",
                                 new_val, self.pv.pvname, str(e))

    def add_listener(self, channel):
        super(Connection, self).add_listener(channel)
        # If we are adding a listener to an already existing PV, we need to
        # manually send the signals indicating that the PV is connected, what the latest value is, etc.
        if self.pv.connected:
            self.send_connection_state(conn=True)
            self.pv.run_callbacks()
        else:
            self.send_connection_state(conn=False)
        # If the channel is used for writing to PVs, hook it up to the 'put' methods.
        if channel.value_signal is not None:
            try:
                channel.value_signal[str].connect(self.put_value, Qt.QueuedConnection)
            except KeyError:
                pass
            try:
                channel.value_signal[int].connect(self.put_value, Qt.QueuedConnection)
            except KeyError:
                pass
            try:
                channel.value_signal[float].connect(self.put_value, Qt.QueuedConnection)
            except KeyError:
                pass
            try:
                channel.value_signal[np.ndarray].connect(self.put_value, Qt.QueuedConnection)
            except KeyError:
                pass

    def close(self):
        self.pv.disconnect()


class CaprotoPlugin(PyDMPlugin):
    # NOTE: protocol is intentionally "None" to keep this plugin from getting directly imported.
    # If this plugin is chosen as the One True EPICS Plugin in epics_plugin.py, the protocol will
    # be properly set before it is used.
    protocol = None
    connection_class = Connection
