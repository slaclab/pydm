"""
Module to define do-nothing widgets to test plugins with.
These widgets do not have draw routines or analogues in designer, they simply
send and recieve signals and store values in their fields.
"""
import numpy as np
from PyQt4.QtGui import QWidget
from PyQt4.QtCore import pyqtSignal, pyqtSlot
from pydm.widgets.channel import PyDMChannel as Channel

class BasicValueWidget(QWidget):
    """
    Generic PyDM Widget for testing plugins. Contains a basic value Channel.
    """
    __pyqtSignals__ = ("send_value_signal([int], [float], [str])",
                       "value_updated_signal()",)

    send_value_signal = pyqtSignal([int], [float], [str])
    value_updated_signal = pyqtSignal()

    def __init__(self, channel=None, parent=None):
        """
        Initialize channel and parent. Start value at "None".

        :param channel: string channel address to use
        :type channel:  str
        :param parent: parent QWidget
        :type parent:  QWidget or None
        """
        super(BasicValueWidget, self).__init__(parent=parent)
        self.channel = channel
        self.value = None

    @pyqtSlot(int)
    @pyqtSlot(float)
    @pyqtSlot(str)
    def recv_value(self, value):
        """
        Recieve value from plugin signal. Store in self.value.

        :param value: value to store
        :type value:  int, float, or str
        """
        self.value = value
        self.value_updated_signal.emit()

    @pyqtSlot(int)
    @pyqtSlot(float)
    @pyqtSlot(str)
    def send_value(self, value):
        """
        Send desired value to plugin slot.

        :param value: value to send
        :type value: int, float, or str
        """
        self.send_value_signal[type(value)].emit(value)

    def channels(self):
        """
        Return list of channels, in this case just a basic value channel.

        :rtyp: list of :class:Channel
        """
        return [Channel(address=self.channel,
                        value_slot=self.recv_value,
                        value_signal=self.send_value_signal)]

class ValueWidget(BasicValueWidget):
    """
    Generic PyDM Widget for testing plugins. Contains a more thorough value
    Channel.
    """
    __pyqtSignals__ = ("send_value_signal([int], [float], [str])",
                       "value_updated_signal()",
                       "conn_updated_signal()",
                       "sevr_updated_signal()",
                       "rwacc_updated_signal()",
                       "enums_updated_signal()",
                       "units_updated_signal()",
                       "prec_updated_signal()",)

    conn_updated_signal = pyqtSignal()
    sevr_updated_signal = pyqtSignal()
    rwacc_updated_signal = pyqtSignal()
    enums_updated_signal = pyqtSignal()
    units_updated_signal = pyqtSignal()
    prec_updated_signal = pyqtSignal()

    def __init__(self, channel=None, parent=None):
        """
        Initialize channel and parent. Start all fields as None.

        :param channel: string channel address to use
        :type channel:  str
        :param parent: parent QWidget
        :type parent:  QWidget or None
        """
        super(ValueWidget, self).__init__(channel=channel, parent=parent)
        self.conn = None
        self.sevr = None
        self.rwacc = None
        self.enums = None
        self.units = None
        self.prec = None

    @pyqtSlot(bool)
    def recv_conn(self, conn):
        """
        Get connection state signal

        :param conn: connection state
        :type conn:  bool
        """
        self.conn = conn
        self.conn_updated_signal.emit()

    @pyqtSlot(int)
    def recv_sevr(self, sevr):
        """
        Get alarm state signal

        :param sevr: alarm state
        :type sevr:  int
        """
        self.sevr = sevr
        self.sevr_updated_signal.emit()

    @pyqtSlot(bool)
    def recv_rwacc(self, rwacc):
        """
        Get write access signal

        :param rwacc: write access state
        :type rwacc:  bool
        """
        self.rwacc = rwacc
        self.rwacc_updated_signal.emit()

    @pyqtSlot(tuple)
    def recv_enums(self, enums):
        """
        Get enum strings signal

        :param enums: enum strings
        :type enums:  tuple of str
        """
        self.enums = enums
        self.enums_updated_signal.emit()

    @pyqtSlot(str)
    def recv_units(self, units):
        """
        Get units signal

        :param units: engineering units
        :type units:  str
        """
        self.units = units
        self.units_updated_signal.emit()

    @pyqtSlot(int)
    def recv_prec(self, prec):
        """
        Get precision signal

        :param prec: data precision
        :type prec:  int
        """
        self.prec = prec
        self.prec_updated_signal.emit()

    def channels(self):
        """
        Return list of channels, in this case one channel with every field
        filled except for the waveform fields.

        :rtyp: list of :class:Channel
        """
        return [Channel(address=self.channel,
                        value_slot=self.recv_value,
                        value_signal=self.send_value_signal,
                        connection_slot=self.recv_conn,
                        severity_slot=self.recv_sevr,
                        write_access_slot=self.recv_rwacc,
                        enum_strings_slot=self.recv_enums,
                        unit_slot=self.recv_units,
                        prec_slot=self.recv_prec)]

class BasicWaveformWidget(BasicValueWidget):
    """
    Generic PyDM Widget for testing plugins. Contains a basic waveform Channel.
    """
    __pyqtSignals__ = ("send_waveform_signal(np.ndarray)",
                       "waveform_updated_signal()",)

    send_waveform_signal = pyqtSignal(np.ndarray)
    waveform_updated_signal = pyqtSignal()

    def __init__(self, channel=None, parent=None):
        """
        Initialize channel and parent. Start value at "None".

        :param channel: string channel address to use
        :type channel:  str
        :param parent: parent QWidget
        :type parent:  QWidget or None
        """
        super(BasicWaveformWidget, self).__init__(channel=channel, parent=parent)

    @pyqtSlot(np.ndarray)
    def recv_waveform(self, waveform):
        """
        Recieve waveform from plugin signal. Store in self.value.

        :param waveform: waveform
        :type waveform:  np.ndarray
        """
        self.value = waveform
        self.waveform_updated_signal.emit()

    @pyqtSlot(np.ndarray)
    def send_waveform(self, waveform):
        """
        Send desired waveform to plugin slot.

        :param value: waveform to send
        :type value: np.ndarray
        """
        self.send_waveform_signal.emit(waveform)

    def channels(self):
        """
        Return list of channels, in this case just a basic waveform channel.

        :rtyp: list of :class:Channel
        """
        return [Channel(address=self.channel,
                        waveform_slot=self.recv_waveform,
                        waveform_signal=self.send_waveform_signal)]

class WaveformWidget(ValueWidget):
    """
    Generic PyDM Widget for testing plugins. Contains a more thorough waveform
    Channel.

    Lots of copy/paste because pyqt multiple inheritance is broken.
    """
    __pyqtSignals__ = ("send_waveform_signal(np.ndarray)",
                       "waveform_updated_signal()",
                       "conn_updated_signal()",
                       "sevr_updated_signal()",
                       "rwacc_updated_signal()",
                       "enums_updated_signal()",
                       "units_updated_signal()",
                       "prec_updated_signal()",)

    send_waveform_signal = pyqtSignal(np.ndarray)
    waveform_updated_signal = pyqtSignal()

    def __init__(self, channel=None, parent=None):
        super(WaveformWidget, self).__init__(channel=channel, parent=parent)

    @pyqtSlot(np.ndarray)
    def recv_waveform(self, waveform):
        """
        Recieve waveform from plugin signal. Store in self.value.

        :param waveform: waveform
        :type waveform:  np.ndarray
        """
        self.value = waveform
        self.waveform_updated_signal.emit()

    @pyqtSlot(np.ndarray)
    def send_waveform(self, waveform):
        """
        Send desired waveform to plugin slot.

        :param value: waveform to send
        :type value: np.ndarray
        """
        self.send_waveform_signal.emit(waveform)

    def channels(self):
        """
        Return list of channels, in this case one channel with every field
        filled except for the value fields.

        :rtyp: list of :class:Channel
        """
        return [Channel(address=self.channel,
                        waveform_slot=self.recv_waveform,
                        waveform_signal=self.send_waveform_signal,
                        connection_slot=self.recv_conn,
                        severity_slot=self.recv_sevr,
                        write_access_slot=self.recv_rwacc,
                        enum_strings_slot=self.recv_enums,
                        unit_slot=self.recv_units,
                        prec_slot=self.recv_prec)]
