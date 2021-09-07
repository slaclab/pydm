import weakref
import threading

from numpy import ndarray

from ..utilities.remove_protocol import protocol_and_address
from qtpy.QtCore import Signal, QObject, Qt
from qtpy.QtWidgets import QApplication
from .. import config


class PyDMConnection(QObject):
    new_value_signal = Signal([float], [int], [str], [ndarray], [bool])
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
            try:
                self.new_value_signal[bool].connect(channel.value_slot, Qt.QueuedConnection)
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
                try:
                    self.new_value_signal[bool].disconnect(channel.value_slot)
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
    designer_online_by_default = False

    def __init__(self):
        self.connections = {}
        self.channels = weakref.WeakSet()
        self.lock = threading.Lock()

    @staticmethod
    def get_address(channel):
        return protocol_and_address(channel.address)[1]

    @staticmethod
    def get_connection_id(channel):
        return PyDMPlugin.get_address(channel)

    def add_connection(self, channel):
        from pydm.utilities import is_qt_designer
        with self.lock:
            connection_id = self.get_connection_id(channel)
            address = self.get_address(channel)
            # If this channel is already connected to this plugin lets ignore
            if channel in self.channels:
                return

            if (is_qt_designer() and not config.DESIGNER_ONLINE and
                    not self.designer_online_by_default):
                return

            self.channels.add(channel)
            if connection_id in self.connections:
                self.connections[connection_id].add_listener(channel)
            else:
                self.connections[connection_id] = self.connection_class(
                    channel, address, self.protocol)

    def remove_connection(self, channel, destroying=False):
        with self.lock:
            connection_id = self.get_connection_id(channel)
            if connection_id in self.connections and channel in self.channels:
                self.connections[connection_id].remove_listener(
                    channel, destroying=destroying)
                self.channels.remove(channel)
                if self.connections[connection_id].listener_count < 1:
                    self.connections[connection_id].deleteLater()
                    del self.connections[connection_id]

