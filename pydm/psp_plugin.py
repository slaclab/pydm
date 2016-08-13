import numpy as np
from psp.Pv import Pv
from PyQt4.QtCore import pyqtSlot, pyqtSignal, Qt
from .plugin import PyDMPlugin, PyDMConnection

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

class Connection(PyDMConnection):
    """
    Channel access connection using psp (pyca)
    """

    def __init__(self, channel, pv, parent=None):
        super(Connection,self).__init__(channel, pv, parent)

        self.enum_strings = None

        self.pv = Pv(pv)
        self.pv.add_connection_callback(self.connected_cb)
        self.pv.add_monitor_callback(self.monitor_cb)
        self.pv.monitor()

        # No pyca support for units, so we'll take from .EGU if it exists.
        self.units_pv = Pv(pv + ".EGU")
        self.units_pv.add_connection_callback(self.units_cb)
        self.units_pv.monitor()

        # Ditto for precision
        self.prec_pv = Pv(pv + ".PREC")
        self.prec_pv.add_connection_callback(self.prec_cb)
        self.prec_pv.monitor()

        # Sevr is just broken in pyca, .state() always returns 2...
        self.sevr_pv = Pv(pv + ".SEVR")
        self.sevr_pv.add_connection_callback(self.sevr_cb)
        self.sevr_pv.monitor()

        self.add_listener(channel)

    def connected_cb(self, isconnected):
        """
        Run this when we connect
        """
        self.send_connection_state(isconnected)
        if isconnected:
            self.epics_type = self.pv.type()
            if self.epics_type == "DBF_ENUM":
                self.enum_strings = self.pv.get_enum_set()
            self.python_type = type_map.get(self.epics_type)
            self.count = self.pv.count or 1
            if self.python_type is None:
                raise Exception("Unsupported EPICS type {0} for pv {1}".format(self.epics_type, self.pv.name))

    def monitor_cb(self, e=None):
        """
        Run this when the value changes
        """
        if e is None:
            self.send_new_value(self.pv.value)

    def sevr_cb(self, e=None):
        """
        We need this because pv.state() always returns 2 ("major" alarm...)
        """
        if e is None:
            try:
                sevr = self.sevr_pv.value
            except:
                sevr = None
            if sevr is not None:
                self.new_severity_signal.emit(sevr)

    def units_cb(self, e=None):
        """
        Run this with the rest of the monitor_cb in normal operation,
        but keep separate to run later if units takes a while to connect.
        """
        if e is None:
            try:
                units = self.units_pv.value
            except:
                units = None
            if units is not None:
                self.unit_signal.emit(units)

    def prec_cb(self, e=None):
        """
        See units_cb
        """
        if e is None:
            try:
                prec = self.prec_pv.value
            except:
                prec = None
            if prec is not None:
                self.prec_signal.emit(prec)

    def send_new_value(self, value=None):
        """
        Send new value to listeners
        """
        if self.python_type is None:
            return

        self.sevr_cb()

        try:
            rwacc = self.pv.rwaccess()
        except:
            rwacc = None
        if rwacc is not None:
            self.write_access_signal.emit(rwacc)

        self.units_cb()
        self.prec_cb()

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
        Send connected/disconnected state to listeners
        """
        self.connection_state_signal.emit(conn)

    @pyqtSlot(int)
    @pyqtSlot(float)
    @pyqtSlot(str)
    @pyqtSlot(np.ndarray)
    def put_value(self, value):
        """
        Set a value in epics
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
        Same as put_value, but for waveforms only. Temporary for compatibility.
        """
        self.put_value(value)

    def add_listener(self, channel):
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
        self.pv.disconnect()
        self.units_pv.disconnect()
        self.prec_pv.disconnect()

class PSPPlugin(PyDMPlugin):
    protocol = "ca://"
    connection_class = Connection   
