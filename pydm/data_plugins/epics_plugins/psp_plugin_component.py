"""
Plugin to handle EPICS connections using pyca through psp.Pv.
This is used instead of pyepics for better performance.
"""

import numpy as np
import pyca
from psp.Pv import Pv
from qtpy.QtCore import Slot, Qt, QTimer
from pydm import data_plugins
from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection

# Map how we will interpret EPICS types in python.
type_map = dict(
    DBF_STRING=str,
    DBF_CHAR=str,
    DBF_UCHAR=str,
    DBF_SHORT=int,
    DBF_USHORT=int,
    DBF_LONG=int,
    DBF_ULONG=int,
    DBF_FLOAT=float,
    DBF_DOUBLE=float,
    DBF_ENUM=int,
    DBF_MENU=None,
    DBF_DEVICE=None,
    DBF_INLINK=None,
    DBF_OUTLINK=None,
    DBF_FWDLINK=None,
    DBF_NOACCESS=None,
)

# .SCAN mapping to override throttle
scan_list = [
    float("inf"),  # passive
    float("inf"),  # event
    float("inf"),  # IO Intr
    10.0,
    5.0,
    2.0,
    1.0,
    0.5,
    0.2,
    0.1,
]


def generic_con_cb(pv_obj):
    """
    Create a generic callback to set up a monitor on connection.

    :param pv_obj: Object representing the EPICS PV data source. This object
                   needs to have not been connected yet.
    :type pv_obj:  Pv
    :rtype: function(is_connected)
    """

    def cb(is_connected):
        if is_connected and not pv_obj.ismonitored:
            pv_obj.monitor()

    return cb


def generic_mon_cb(source, signal):
    """
    Create a generic callback for sending a signal from source value.

    :param source: Object representing the EPICS PV data source. This object
                   needs to be properly initialized and monitored.
    :type source:  Pv
    :param signal: Signal to send the value out on. Check the base
                   :class:`PyDMConnection` class for available signals.
    :type signal:  Signal
    :rtype: function(errors=None)
    """

    def cb(e=None):
        if e is None:
            try:
                signal.emit(source.value)
            except AttributeError:
                raise

    return cb


def setup_pv(pvname, con_cb=None, mon_cb=None, rwaccess_cb=None, signal=None, mon_cb_once=False, control=False):
    """
    Initialize an EPICS PV using psp with proper callbacks.

    :param pvname: EPICS PV name
    :type pvname:  str
    :param con_cb: Connection callback. If left as None and provided with
                    signal, emit our value from signal as the callback.
    :type con_cb:  function(isconnected=None)
    :param mon_cb: Monitor callback. If left as None and provided with signal,
                   emit our value from signal as the callback.
    :type mon_cb:  function(errors=None)
    :param rwaccess_cb: Read/write access state callback.
    :type rwaccess_cb: function(access_state)
    :param signal: Signal to emit our value on as the default callback when
                   con_cb or mon_cb are left as None. Check the base
                   :class:`PyDMConnection` class for available signals.
    :type signal:  Signal
    :param mon_cb_once: True if we only want the monitor callback to run once.
    :type mon_cb_once: bool
    :param control: True if we want to monitor control values
    :type control: bool
    :rtype: Pv
    """
    pv = Pv(pvname, use_numpy=True, control=control)

    if signal is None:

        def default_mon_cb(e):
            return None

    else:
        default_mon_cb = generic_mon_cb(pv, signal)

    pv.add_connection_callback(con_cb or generic_con_cb(pv))
    pv.add_monitor_callback(mon_cb or default_mon_cb, once=mon_cb_once)
    if rwaccess_cb:
        pv.add_rwaccess_callback(rwaccess_cb)
    pv.connect(None)
    return pv


class Connection(PyDMConnection):
    """
    Class that manages channel access connections using pyca through psp.
    See :class:`PyDMConnection` class.
    """

    def __init__(self, channel, pv, protocol=None, parent=None):
        """
        Instantiate Pv object and set up the channel access connections.

        :param channel: :class:`PyDMChannel` object as the first listener.
        :type channel:  :class:`PyDMChannel`
        :param pv: Name of the pv to connect to.
        :type pv:  str
        :param parent: PyQt widget that this widget is inside of.
        :type parent:  QWidget
        """
        super().__init__(channel, pv, protocol, parent)
        self.python_type = None
        self.pv = setup_pv(
            pv, con_cb=self.connected_cb, mon_cb=self.monitor_cb, rwaccess_cb=self.rwaccess_cb, control=True
        )
        self.enums = None
        self.sevr = None
        self.ctrl_llim = None
        self.ctrl_hlim = None
        self.alarm_hlim = None
        self.alarm_llim = None
        self.warn_hlim = None
        self.warn_llim = None

        self.units = None
        self.prec = None
        self.time = None
        self.count = None
        self.epics_type = None
        self.read_access = False
        self.write_access = False
        # Auxiliary info to help with throttling
        self.scan_pv = setup_pv(pv + ".SCAN", mon_cb=self.scan_pv_cb, mon_cb_once=True)
        self.throttle = QTimer(self)
        self.throttle.timeout.connect(self.throttle_cb)

        self.add_listener(channel)

    def connected_cb(self, isconnected):
        """
        Callback to run whenever the connection state of our pv changes.

        :param isconnected: True if we are connected, False otherwise.
        :type isconnected:  bool
        """
        self.connected = isconnected
        self.send_connection_state(isconnected)
        if isconnected:
            self.epics_type = self.pv.type()
            self.count = self.pv.count or 1

            # Get the control info for the PV.
            self.pv.get_data(True, -1.0, self.count)
            pyca.flush_io()
            if self.epics_type == "DBF_ENUM":
                self.pv.get_enum_strings(-1.0)
            if not self.pv.ismonitored:
                self.pv.monitor()
            self.python_type = type_map.get(self.epics_type)
            if self.python_type is None:
                raise Exception("Unsupported EPICS type {0} for pv {1}".format(self.epics_type, self.pv.name))

    def monitor_cb(self, e=None):
        """
        Callback to run whenever the value of our pv changes.

        :param e: Error state. Should be None under normal circumstances.
        """
        if e is None:
            self.send_new_value(self.pv.value)

    def rwaccess_cb(self, read_access, write_access):
        """
        Callback to run when the access state of our pv changes.

        :param read_access: Whether or not the PV is readable.
        :param write_access: Whether or not the PV is writeable.
        """
        self.read_access = read_access
        self.write_access = write_access
        self.send_access_state()

    def throttle_cb(self):
        """
        Callback to run when the throttle timer times out.
        """
        self.send_new_value(self.pv.get())

    def timestamp(self):
        try:
            secs, nanos = self.pv.timestamp()
        except KeyError:
            return None
        return float(secs + nanos / 1.0e9)

    def send_new_value(self, value=None):
        """
        Send a value to every channel listening for our Pv.

        :param value: Value to emit to our listeners.
        :type value:  int, float, str, or np.ndarray, depending on our record
                      type.
        """
        if self.python_type is None:
            return

        if self.enums is None:
            try:
                self.update_enums()
            except KeyError:
                self.pv.get_enum_strings(-1.0)

        if self.pv.severity is not None and self.pv.severity != self.sevr:
            self.sevr = self.pv.severity
            self.new_severity_signal.emit(self.sevr)

        try:
            prec = self.pv.data["precision"]
        except KeyError:
            pass
        else:
            if self.prec != prec:
                self.prec = prec
                self.prec_signal.emit(int(self.prec))

        try:
            units = self.pv.data["units"]
        except KeyError:
            pass
        else:
            if self.units != units:
                self.units = units
                self.unit_signal.emit(
                    self.units.decode(encoding="ascii") if isinstance(self.units, bytes) else self.units
                )

        time = self.timestamp()

        if time is not None and self.time != time:
            self.time = time
            self.timestamp_signal.emit(self.time)

        try:
            ctrl_llim = self.pv.data["ctrl_llim"]
        except KeyError:
            pass
        else:
            if self.ctrl_llim != ctrl_llim:
                self.ctrl_llim = ctrl_llim
                self.lower_ctrl_limit_signal.emit(self.ctrl_llim)

        try:
            ctrl_hlim = self.pv.data["ctrl_hlim"]
        except KeyError:
            pass
        else:
            if self.ctrl_hlim != ctrl_hlim:
                self.ctrl_hlim = ctrl_hlim
                self.upper_ctrl_limit_signal.emit(self.ctrl_hlim)

        try:
            alarm_hlim = self.pv.data["alarm_hlim"]
        except KeyError:
            pass
        else:
            if self.alarm_hlim != alarm_hlim:
                self.alarm_hlim = alarm_hlim
                self.upper_alarm_limit_signal.emit(self.alarm_hlim)

        try:
            alarm_llim = self.pv.data["alarm_llim"]
        except KeyError:
            pass
        else:
            if self.alarm_llim != alarm_llim:
                self.alarm_llim = alarm_llim
                self.lower_alarm_limit_signal.emit(self.alarm_llim)

        try:
            warn_hlim = self.pv.data["warn_hlim"]
        except KeyError:
            pass
        else:
            if self.warn_hlim != warn_hlim:
                self.warn_hlim = warn_hlim
                self.upper_warning_limit_signal.emit(self.warn_hlim)

        try:
            warn_llim = self.pv.data["warn_llim"]
        except KeyError:
            pass
        else:
            if self.warn_llim != warn_llim:
                self.warn_llim = warn_llim
                self.lower_warning_limit_signal.emit(self.warn_llim)

        if self.count > 1:
            self.new_value_signal[np.ndarray].emit(value)
        else:
            self.new_value_signal[self.python_type].emit(self.python_type(value))

    def send_ctrl_vars(self):
        if self.enums is None:
            try:
                self.update_enums()
            except KeyError:
                self.pv.get_enum_strings(-1.0)
        else:
            self.enum_strings_signal.emit(self.enums)

        if self.pv.severity != self.sevr:
            self.sevr = self.pv.severity
        self.new_severity_signal.emit(self.sevr)

        if self.prec is None:
            try:
                self.prec = self.pv.data["precision"]
            except KeyError:
                pass
        if self.prec is not None:
            self.prec_signal.emit(int(self.prec))

        if self.time is None:
            self.time = self.timestamp()

        if self.time is not None:
            self.timestamp_signal.emit(self.time)

        if self.units is None:
            try:
                self.units = self.pv.data["units"]
            except KeyError:
                pass
        if self.units:
            if isinstance(self.units, bytes):
                self.units = self.units.decode(encoding="ascii")
            self.unit_signal.emit(self.units)

        if self.ctrl_llim is None:
            try:
                self.ctrl_llim = self.pv.data["ctrl_llim"]
            except KeyError:
                pass
        if self.ctrl_llim is not None:
            self.lower_ctrl_limit_signal.emit(self.ctrl_llim)

        if self.ctrl_hlim is None:
            try:
                self.ctrl_hlim = self.pv.data["ctrl_hlim"]
            except KeyError:
                pass
        if self.ctrl_hlim is not None:
            self.upper_ctrl_limit_signal.emit(self.ctrl_hlim)

        if self.alarm_hlim is None:
            try:
                self.alarm_hlim = self.pv.data["alarm_hlim"]
            except KeyError:
                pass
        if self.alarm_hlim is not None:
            self.upper_alarm_limit_signal.emit(self.alarm_hlim)

        if self.alarm_llim is None:
            try:
                self.alarm_llim = self.pv.data["alarm_llim"]
            except KeyError:
                pass
        if self.alarm_llim is not None:
            self.lower_alarm_limit_signal.emit(self.alarm_llim)

        if self.warn_hlim is None:
            try:
                self.warn_hlim = self.pv.data["warn_hlim"]
            except KeyError:
                pass
        if self.warn_hlim is not None:
            self.upper_warning_limit_signal.emit(self.warn_hlim)

        if self.warn_llim is None:
            try:
                self.warn_llim = self.pv.data["warn_llim"]
            except KeyError:
                pass
        if self.warn_llim is not None:
            self.lower_warning_limit_signal.emit(self.warn_llim)

    def send_connection_state(self, conn=None):
        """
        Send an update on our connection state to every listener.

        :param conn: True if we are connected, False if we are disconnected.
        :type conn:  bool
        """
        self.connection_state_signal.emit(conn)

    def send_access_state(self):
        if data_plugins.is_read_only():
            self.write_access_signal.emit(False)
            return
        self.write_access_signal.emit(self.write_access)

    def update_enums(self):
        """
        Send an update on our enum strings to every listener, if this is an
        enum record.
        """
        if self.epics_type == "DBF_ENUM":
            if self.enums is None:
                self.enums = tuple(
                    b.decode(encoding="ascii") if isinstance(b, bytes) else b for b in self.pv.data["enum_set"]
                )
            self.enum_strings_signal.emit(self.enums)

    @Slot(int)
    @Slot(float)
    @Slot(str)
    @Slot(np.ndarray)
    def put_value(self, value):
        """
        Set our PV's value in EPICS.

        :param value: The value we'd like to put to our PV.
        :type value:  int or float or str or np.ndarray, depending on our
                      record type.
        """
        if self.count == 1:
            value = self.python_type(value)
        try:
            self.pv.put(value)
        except pyca.caexc as e:
            print("pyca error: {}".format(e))

    @Slot(np.ndarray)
    def put_waveform(self, value):
        """
        Set a PV's waveform value in EPICS. This is a deprecated function kept
        temporarily for compatibility with old code.

        :param value: The waveform value we'd like to put to our PV.
        :type value:  np.ndarray
        """
        self.put_value(value)

    def scan_pv_cb(self, e=None):
        """
        Call set_throttle once we have a value from the scan_pv. We need this
        value inside set_throttle to decide if we can ignore the throttle
        request (i.e. our pv updates more slowly than our throttle)

        :param e: Error state. Should be None under normal circumstances.
        """
        if e is None:
            self.pv.wait_ready()
            count = self.pv.count or 1
            if count > 1:
                max_data_rate = 1000000.0  # bytes/s
                bytes = self.pv.value.itemsize  # bytes
                throttle = max_data_rate / (bytes * count)  # Hz
                if throttle < 120:
                    self.set_throttle(throttle)

    @Slot(int)
    @Slot(float)
    def set_throttle(self, refresh_rate):
        """
        Throttle our update rate. This is useful when the data is large (e.g.
        image waveforms). Set to zero to disable throttling.

        :param delay: frequency of pv updates
        :type delay:  float or int
        """
        try:
            scan = scan_list[self.scan_pv.value]
        except Exception:
            scan = float("inf")
        if 0 < refresh_rate < 1 / scan:
            self.pv.monitor_stop()
            self.throttle.setInterval(1000.0 / refresh_rate)
            self.throttle.start()
        else:
            self.throttle.stop()
            if not self.pv.ismonitored:
                self.pv.monitor()

    def add_listener(self, channel):
        """
        Connect a channel's signals and slots with this object's signals and slots.

        :param channel: The channel to connect.
        :type channel:  :class:`PyDMChannel`
        """
        super().add_listener(channel)
        # If we are adding a listener to an already existing PV, we need to
        # manually send the signals indicating that the PV is connected, what
        # the latest value is, etc.
        if self.pv.isconnected and self.pv.isinitialized:
            self.send_connection_state(conn=True)
            self.monitor_cb()
            try:
                self.update_enums()
            except KeyError:
                self.pv.get_enum_strings(-1.0)
            self.send_access_state()
            self.send_ctrl_vars()
        if channel.value_signal is not None:
            for signal_type in (str, int, float, np.ndarray):
                try:
                    channel.value_signal[signal_type].connect(self.put_value, Qt.QueuedConnection)
                # When signal type can't be found, PyQt5 throws KeyError here, but PySide6 index error.
                # If signal type exists but doesn't match the slot, TypeError gets thrown.
                except (KeyError, IndexError, TypeError):
                    pass

    def close(self):
        """
        Clean up.
        """
        self.throttle.stop()
        self.pv.monitor_stop()
        self.pv.disconnect()
        self.scan_pv.monitor_stop()
        self.scan_pv.disconnect()


class PSPPlugin(PyDMPlugin):
    """
    Class to define our protocol and point to our :class:`Connection` Class
    """

    # NOTE: protocol is intentionally "None" to keep this plugin from getting directly imported.
    # If this plugin is chosen as the One True EPICS Plugin in epics_plugin.py, the protocol will
    # be properly set before it is used.
    protocol = None
    connection_class = Connection
