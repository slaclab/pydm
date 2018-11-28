import weakref
import threading

from numpy import ndarray

from ..utilities.remove_protocol import protocol_and_address
from qtpy.QtCore import Signal, QObject, Qt
from qtpy.QtWidgets import QApplication


class PyDMConnection(QObject):
    new_value_signal = Signal([float], [int], [str], [ndarray])
    connection_state_signal = Signal(bool)
    new_severity_signal = Signal(int)
    write_access_signal = Signal(bool)
    enum_strings_signal = Signal(tuple)
    unit_signal = Signal(str)
    prec_signal = Signal(int)
    upper_ctrl_limit_signal = Signal([float], [int])
    lower_ctrl_limit_signal = Signal([float], [int])

    def __init__(self, channel, address, protocol=None, parent=None):
        super(PyDMConnection, self).__init__(parent)
        self.protocol = protocol
        self.address = address
        self.connected = False
        self.value = None
        self.listener_count = 0
        self.app = QApplication.instance()

    def add_listener(self, channel):
        self.listener_count = self.listener_count + 1
        if channel.connection_slot is not None:
            self.connection_state_signal.connect(channel.connection_slot, Qt.QueuedConnection)

        if channel.value_slot is not None:
            try:
                self.new_value_signal[int].connect(channel.value_slot, Qt.QueuedConnection)
            except TypeError:
                pass
            try:
                self.new_value_signal[float].connect(channel.value_slot, Qt.QueuedConnection)
            except TypeError:
                pass
            try:
                self.new_value_signal[str].connect(channel.value_slot, Qt.QueuedConnection)
            except TypeError:
                pass
            try:
                self.new_value_signal[ndarray].connect(channel.value_slot, Qt.QueuedConnection)
            except TypeError:
                pass

        if channel.severity_slot is not None:
            self.new_severity_signal.connect(channel.severity_slot, Qt.QueuedConnection)

        if channel.write_access_slot is not None:
            self.write_access_signal.connect(channel.write_access_slot, Qt.QueuedConnection)

        if channel.enum_strings_slot is not None:
            self.enum_strings_signal.connect(channel.enum_strings_slot, Qt.QueuedConnection)

        if channel.unit_slot is not None:
            self.unit_signal.connect(channel.unit_slot, Qt.QueuedConnection)

        if channel.upper_ctrl_limit_slot is not None:
            self.upper_ctrl_limit_signal.connect(channel.upper_ctrl_limit_slot, Qt.QueuedConnection)

        if channel.lower_ctrl_limit_slot is not None:
            self.lower_ctrl_limit_signal.connect(channel.lower_ctrl_limit_slot, Qt.QueuedConnection)

        if channel.prec_slot is not None:
            self.prec_signal.connect(channel.prec_slot, Qt.QueuedConnection)

    def remove_listener(self, channel, destroying=False):
        if not destroying:
            if channel.connection_slot is not None:
                try:
                    self.connection_state_signal.disconnect(channel.connection_slot)
                except TypeError:
                    pass

            if channel.value_slot is not None:
                try:
                    self.new_value_signal[int].disconnect(channel.value_slot)
                except TypeError:
                    pass
                try:
                    self.new_value_signal[float].disconnect(channel.value_slot)
                except TypeError:
                    pass
                try:
                    self.new_value_signal[str].disconnect(channel.value_slot)
                except TypeError:
                    pass
                try:
                    self.new_value_signal[ndarray].disconnect(channel.value_slot)
                except TypeError:
                    pass

            if channel.severity_slot is not None:
                try:
                    self.new_severity_signal.disconnect(channel.severity_slot)
                except (KeyError, TypeError):
                    pass

            if channel.write_access_slot is not None:
                try:
                    self.write_access_signal.disconnect(channel.write_access_slot)
                except (KeyError, TypeError):
                    pass

            if channel.enum_strings_slot is not None:
                try:
                    self.enum_strings_signal.disconnect(channel.enum_strings_slot)
                except (KeyError, TypeError):
                    pass

            if channel.unit_slot is not None:
                try:
                    self.unit_signal.disconnect(channel.unit_slot)
                except (KeyError, TypeError):
                    pass

            if channel.upper_ctrl_limit_slot is not None:
                try:
                    self.upper_ctrl_limit_signal.disconnect(channel.upper_ctrl_limit_slot)
                except (KeyError, TypeError):
                    pass

            if channel.lower_ctrl_limit_slot is not None:
                try:
                    self.lower_ctrl_limit_signal.disconnect(channel.lower_ctrl_limit_slot)
                except (KeyError, TypeError):
                    pass

            if channel.prec_slot is not None:
                try:
                    self.prec_signal.disconnect(channel.prec_slot)
                except (KeyError, TypeError):
                    pass

        self.listener_count = self.listener_count - 1
        if self.listener_count < 1:
            self.close()

    def close(self):
        pass


class PyDMPlugin(object):
    protocol = None
    connection_class = PyDMConnection

    def __init__(self):
        self.connections = {}
        self.channels = weakref.WeakSet()
        self.lock = threading.Lock()

    @staticmethod
    def get_address(channel):
        return protocol_and_address(channel.address)[1]

    def add_connection(self, channel):
        with self.lock:
            address = self.get_address(channel)
            # If this channel is already connected to this plugin lets ignore
            if channel in self.channels:
                return
            self.channels.add(channel)
            if address in self.connections:
                self.connections[address].add_listener(channel)
            else:
                self.connections[address] = self.connection_class(channel, address,
                                                                  self.protocol)

    def remove_connection(self, channel, destroying=False):
        with self.lock:
            address = self.get_address(channel)
            if address in self.connections and channel in self.channels:
                self.connections[address].remove_listener(channel,
                                                          destroying=destroying)
                self.channels.remove(channel)
                if self.connections[address].listener_count < 1:
                    del self.connections[address]