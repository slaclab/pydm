"""
Plugin to handle EPICS connections using pyca through psp.Pv.
This is used instead of pyepics for better performance.
"""
import numpy as np
from psp.Pv import Pv
from ..PyQt.QtCore import pyqtSlot, pyqtSignal, Qt, QTimer
from pydm.plugin import PyDMPlugin, PyDMConnection

import datetime

# Map how we will interpret EPICS types in python.
type_map = dict(
    DBF_STRING = str,
    DBF_CHAR = str,
    DBF_UCHAR = str,
    DBF_SHORT = int,
    DBF_USHORT = int,
    DBF_LONG = int,
    DBF_ULONG = int,
    DBF_FLOAT = float,
    DBF_DOUBLE = float,
    DBF_ENUM = str,
    DBF_MENU = None,
    DBF_DEVICE = None,
    DBF_INLINK = None,
    DBF_OUTLINK = None,
    DBF_FWDLINK = None,
    DBF_NOACCESS = None,
)

# .SCAN mapping to override throttle
scan_list = [
    float("inf"), #passive
    float("inf"), #event
    float("inf"), #IO Intr
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
    :type signal:  pyqtSignal
    :rtype: function(errors=None)
    """
    def cb(e=None):
        if e is None:
            try:
                signal.emit(source.value)
            except AttributeError:
                raise
    return cb

def setup_pv(pvname, con_cb=None, mon_cb=None, signal=None, mon_cb_once=False):
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
    :param signal: Signal to emit our value on as the default callback when
                   con_cb or mon_cb are left as None. Check the base
                   :class:`PyDMConnection` class for available signals.
    :type signal:  pyqtSignal
    :param mon_cb_once: True if we only want the monitor callback to run once.
    :type mon_cb_once: bool
    :rtype: Pv
    """
    pv = Pv(pvname, use_numpy=True)

    if signal is None:
        default_mon_cb = lambda e: None
    else:
        default_mon_cb = generic_mon_cb(pv, signal)

    pv.add_connection_callback(con_cb or generic_con_cb(pv))
    pv.add_monitor_callback(mon_cb or default_mon_cb, once=mon_cb_once)
    pv.connect(None)
    return pv


class Connection(PyDMConnection):
    protocol = "ca://"
    """
    Class that manages channel access connections using pyca through psp.
    See :class:`PyDMConnection` class.
    """
    def __init__(self, channel_name, parent=None):
        """
        Instantiate Pv object and set up the channel access connections.

        :param channel_name: Name of the pv to connect to (ca://PV_NAME_HERE).
        :type channel_name:  str
        :param parent: PyQt object that owns this connection.
        :type parent:  QObject
        """
        super(Connection,self).__init__(channel_name, parent)
        pv = self.address
        self.python_type = None
        self.pv = setup_pv(pv, self.connected_cb, self.monitor_cb)
        self.enums = None
        self.rwacc = None

        # No pyca support for units, so we'll take from .EGU if it exists.
        self.units_pv = setup_pv(pv + ".EGU", mon_cb=self.send_units)

        # Ditto for precision
        self.prec_pv = setup_pv(pv + ".PREC", mon_cb=self.send_prec)

        # Sevr is just broken in pyca, .state() always returns 2...
        self.sevr_pv = setup_pv(pv + ".SEVR", mon_cb=self.send_sevr)

        # Auxilliary info to help with throttling
        self.scan_pv = setup_pv(pv + ".SCAN", mon_cb=self.scan_pv_cb,
            mon_cb_once=True)
        self.throttle = QTimer(self)
        self.throttle.timeout.connect(self.throttle_cb)

        self.add_listener()

    def connected_cb(self, isconnected):
        """
        Callback to run whenever the connection state of our pv changes.

        :param isconnected: True if we are connected, False otherwise.
        :type isconnected:  bool
        """
        self.send_connection_state(isconnected)
        if isconnected:
            self.epics_type = self.pv.type()
            if self.epics_type == "DBF_ENUM":
                self.pv.set_string_enum(True)
            self.count = self.pv.count or 1
            if not self.pv.ismonitored:
                self.pv.monitor()
            self.python_type = type_map.get(self.epics_type)
            if self.python_type is None:
                raise Exception("Unsupported EPICS type {0} for pv {1}".format(
                                self.epics_type, self.pv.name))

    def monitor_cb(self, e=None):
        """
        Callback to run whenever the value of our pv changes.

        :param e: Error state. Should be None under normal circumstances.
        """
        if e is None:
            self.send_new_value(self.pv.value)

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
        return float(secs + nanos/1.0e9)

    def send_units(self, e=None):
        if e is None:
            unit_val = self.units_pv.value
            self.data_message_signal.emit(self.unit_message(unit_val, self.timestamp()))
    
    def send_prec(self, e=None):
        if e is None:
            prec_val = self.prec_pv.value
            self.data_message_signal.emit(self.precision_message(prec_val, self.timestamp()))
    
    def send_sevr(self, e=None):
        if e is None:
            sevr_val = self.sevr_pv.value
            self.data_message_signal.emit(self.severity_message(sevr_val, self.timestamp()))

    def send_new_value(self, value=None):
        """
        Send a value to every channel listening for our Pv.

        :param value: Value to emit to our listeners.
        :type value:  int, float, str, or np.ndarray, depending on our record
                      type.
        """
        if self.python_type is None:
            return
        try:
            rwacc = self.pv.rwaccess()
        except:
            rwacc = None
        if rwacc is not None:
            # Two bit binary number, 11 = read and write, 01 = read-only
            # presumably this could be other numbers, but in practice it is
            # either 3 for read and write or 1 for just read.
            # Only send the write access state if it has changed, don't send it every time the PV updates.
            if rwacc != self.rwacc:
                self.rwacc = rwacc
                self.data_message_signal.emit(self.write_access_message(rwacc==3, self.timestamp()))

        if self.count > 1:
            self.data_message_signal.emit(self.new_value_message(value, self.timestamp()))
        else:
            self.data_message_signal.emit(self.new_value_message(self.python_type(value), self.timestamp()))

    def send_connection_state(self, conn=None):
        """
        Send an update on our connection state to every listener.

        :param conn: True if we are connected, False if we are disconnected.
        :type conn:  bool
        """
        self.data_message_signal.emit(self.connection_state_message(conn, self.timestamp()))
        
    def update_enums(self):
        """
        Send an update on our enum strings to every listener, if this is an
        enum record.
        """
        if self.epics_type == "DBF_ENUM":
            if self.enums is None:
                self.enums = tuple(b.decode(encoding='ascii') for b in self.pv.get_enum_set())
            self.data_message_signal.emit(self.enum_strings_message(self.enums, self.timestamp()))

    @pyqtSlot(int)
    @pyqtSlot(float)
    @pyqtSlot(str)
    @pyqtSlot(np.ndarray)
    def put_value(self, value):
        """
        Set our PV's value in EPICS.

        :param value: The value we'd like to put to our PV.
        :type value:  int or float or str or np.ndarray, depending on our
                      record type.
        """
        if self.count == 1:
            value = self.python_type(value)
        self.pv.put(value)

    @pyqtSlot(np.ndarray)
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
                max_data_rate = 1000000. # bytes/s
                bytes = self.pv.value.itemsize # bytes
                throttle = max_data_rate/(bytes*count) # Hz
                if throttle < 120:
                    self.set_throttle(throttle)

    @pyqtSlot(int)
    @pyqtSlot(float)
    def set_throttle(self, refresh_rate):
        """
        Throttle our update rate. This is useful when the data is large (e.g.
        image waveforms). Set to zero to disable throttling.

        :param delay: frequency of pv updates
        :type delay:  float or int
        """
        try:
            scan = scan_list[self.scan_pv.value]
        except:
            scan = float("inf")
        if 0 < refresh_rate < 1/scan:
            self.pv.monitor_stop()
            self.throttle.setInterval(1000.0/refresh_rate)
            self.throttle.start()
        else:
            self.throttle.stop()
            if not self.pv.ismonitored:
                self.pv.monitor()

    def add_listener(self):
        """
        Connect a channel's signals and slots with this object's signals and slots.

        :param channel: The channel to connect.
        :type channel:  :class:`PyDMChannel`
        """
        super(Connection, self).add_listener()
        #If we are adding a listener to an already existing PV, we need to
        #manually send the signals indicating that the PV is connected, what the latest value is, etc.
        if self.pv.isconnected and self.pv.isinitialized:
            self.send_connection_state(conn=True)
            self.monitor_cb()
            self.update_enums()
        #try:
        #    channel.value_signal[str].connect(self.put_value, Qt.QueuedConnection)
        #    channel.value_signal[int].connect(self.put_value, Qt.QueuedConnection)
        #    channel.value_signal[float].connect(self.put_value, Qt.QueuedConnection)
        #except:
        #    pass
        #try:
        #    channel.waveform_signal.connect(self.put_value, Qt.QueuedConnection)
        #except:
        #    pass

    def close(self):
        """
        Clean up.
        """
        self.throttle.stop()
        self.pv.monitor_stop()
        self.pv.disconnect()
        self.units_pv.monitor_stop()
        self.units_pv.disconnect()
        self.prec_pv.monitor_stop()
        self.prec_pv.disconnect()
        self.sevr_pv.monitor_stop()
        self.sevr_pv.disconnect()
        self.scan_pv.monitor_stop()
        self.scan_pv.disconnect()

class PSPPlugin(PyDMPlugin):
    """
    Class to define our protocol and point to our :class:`Connection` Class
    """
    protocol = "ca://"
    connection_class = Connection
