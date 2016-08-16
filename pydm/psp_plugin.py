"""
Plugin to handle EPICS connections using pyca through psp.Pv.
This is used instead of pyepics for better performance.
"""
import numpy as np
from psp.Pv import Pv
from PyQt4.QtCore import pyqtSlot, pyqtSignal, Qt
from .plugin import PyDMPlugin, PyDMConnection

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

def generic_cb(source, signal):
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
    def cb(self, e=None):
        if e is True:
            source.monitor()
        if e or e is None:
            try:
                val = source.value
            except:
                val = None
            if val is not None:
                signal.emit(val)
    return cb

def setup_pv(pvname, conn_cb=None, mon_cb=None, signal=None):
    """
    Initialize an EPICS PV using psp with proper callbacks.

    :param pvname: EPICS PV name
    :type pvname:  str
    :param conn_cb: Connection callback. If left as None and provided with
                    signal, emit our value from signal as the callback.
    :type conn_cb:  function(isconnected=None)
    :param mon_cb: Monitor callback. If left as None and provided with signal,
                   emit our value from signal as the callback.
    :type mon_cb:  function(errors=None)
    :param signal: Signal to emit our value on as the default callback when
                   conn_cb or mon_cb are left as None. Check the base
                   :class:`PyDMConnection` class for available signals.
    :type signal:  pyqtSignal
    :rtype: Pv
    """
    pv = Pv(pvname, monitor=True)

    if signal is None:
        default_cb = lambda e: None
    else:
        default_cb = generic_cb(pv, signal)

    pv.add_connection_callback(conn_cb or default_cb)
    pv.add_monitor_callback(mon_cb or default_cb)
    pv.connect(None)
    return pv

class Connection(PyDMConnection):
    """
    Class that manages channel access connections using pyca through psp.
    See :class:`PyDMConnection` class.
    """
    def __init__(self, channel, pv, parent=None):
        """
        Instantiate Pv object and set up the channel access connections.

        :param channel: :class:`PyDMChannel` object as the first listener.
        :type channel:  :class:`PyDMChannel`
        :param pv: Name of the pv to connect to.
        :type pv:  str
        :param parent: PyQt widget that this widget is inside of.
        :type parent:  QWidget
        """
        super(Connection,self).__init__(channel, pv, parent)

        self.enum_strings = None
        self.pv = setup_pv(pv, self.connected_cb, self.monitor_cb)

        # No pyca support for units, so we'll take from .EGU if it exists.
        self.units_pv = setup_pv(pv + ".EGU", signal=self.unit_signal)

        # Ditto for precision
        self.prec_pv = setup_pv(pv + ".PREC", signal=self.prec_signal)

        # Sevr is just broken in pyca, .state() always returns 2...
        self.sevr_pv = setup_pv(pv + ".SEVR", signal=self.new_severity_signal)

        self.add_listener(channel)

    def connected_cb(self, isconnected):
        """
        Callback to run whenever the connection state of our pv changes.

        :param isconnected: True if we are connected, False otherwise.
        :type isconnected:  bool
        """
        self.send_connection_state(isconnected)
        if isconnected:
            self.pv.monitor()
            self.epics_type = self.pv.type()
            if self.epics_type == "DBF_ENUM":
                self.enum_strings = self.pv.get_enum_set()
            self.python_type = type_map.get(self.epics_type)
            self.count = self.pv.count or 1
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
            self.write_access_signal.emit(rwacc)

        if self.enum_strings is not None:
            try:
                value = self.enum_strings[int(value)]
            except IndexError:
                value = ""

        if self.count > 1:
            self.new_waveform_signal.emit(value)
        else:
            self.new_value_signal[self.python_type].emit(self.python_type(value))

    def send_connection_state(self, conn=None):
        """
        Send an update on our connection state to every listener.

        :param conn: True if we are connected, False if we are disconnected.
        :type conn:  bool
        """
        self.connection_state_signal.emit(conn)

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
        if self.count > 1:
            value = np.asarray(value)
        else:
            if self.enum_strings is None:
                value = self.python_type(value)
            else:
                if isinstance(value, str):
                    if value not in self.enum_strings:
                        return
                else:
                    try:
                        value = self.enum_strings[int(value)]
                    except IndexError:
                        return
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

    def add_listener(self, channel):
        """
        Connect a channel's signals and slots with this object's signals and slots.

        :param channel: The channel to connect.
        :type channel:  :class:`PyDMChannel`
        """
        super(Connection, self).add_listener(channel)
        #If we are adding a listener to an already existing PV, we need to
        #manually send the signals indicating that the PV is connected, what the latest value is, etc.
        if self.pv.isconnected:
            self.send_connection_state(conn=True)
            self.monitor_cb()
        try:
            channel.value_signal[str].connect(self.put_value, Qt.QueuedConnection)
            channel.value_signal[int].connect(self.put_value, Qt.QueuedConnection)
            channel.value_signal[float].connect(self.put_value, Qt.QueuedConnection)
        except:
            pass
        try:
            channel.waveform_signal.connect(self.put_value, Qt.QueuedConnection)
        except:
            pass

    def close(self):
        """
        Clean up all open Pv objects.
        """
        self.pv.disconnect()
        self.units_pv.disconnect()
        self.prec_pv.disconnect()
        self.sevr_pv.disconnect()

class PSPPlugin(PyDMPlugin):
    """
    Class to define our protocol and point to our :class:`Connection` Class
    """
    protocol = "ca://"
    connection_class = Connection
