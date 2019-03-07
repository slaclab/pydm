import threading
import weakref

from qtpy.QtCore import Slot, Signal, QObject, Qt
from qtpy.QtWidgets import QApplication

from .data_store import DataStore, DEFAULT_INTROSPECTION
from ..utilities.remove_protocol import protocol_and_address


class PyDMConnection(QObject):
    notify = Signal()

    def __init__(self, channel, address, protocol=None, parent=None):
        super(PyDMConnection, self).__init__(parent)
        self.data = {}
        self.introspection = DEFAULT_INTROSPECTION
        self.channel = channel
        self.protocol = protocol
        self.address = address
        self.listener_count = 0
        self.app = QApplication.instance()
        self.add_listener(channel)

    def add_listener(self, channel):
        print('Called Add_Listener for: ', channel)
        self.listener_count = self.listener_count + 1
        self.notify.connect(channel.notified, Qt.QueuedConnection)
        channel.transmit.connect(self._validate_data_from_channel,
                                 Qt.QueuedConnection)

    def remove_listener(self, channel, destroying=False):
        if not destroying:
            self.notify.disconnect(channel.notified)
            self.channel.transmit.disconnect(self._validate_data_from_channel)

        self.listener_count = self.listener_count - 1
        if self.listener_count < 1:
            self.close()

    def close(self):
        DataStore().remove(self.address)

    @Slot(dict)
    def _validate_data_from_channel(self, payload):
        # if is_read_only():
        #     return
        self.receive_from_channel(payload)

    def receive_from_channel(self, payload):
        pass

    def send_to_channel(self):
        DataStore()[self.channel.address] = (self.data, self.introspection)
        self.notify.emit()


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
        print('Invoked add_connection for: ', channel.address )
        with self.lock:
            address = self.get_address(channel)
            # If this channel is already connected to this plugin lets ignore
            if channel in self.channels:
                print('ABORT... Channel in self.channels')
                return
            self.channels.add(channel)
            if address in self.connections:
                self.connections[address].add_listener(channel)
            else:
                self.connections[address] = self.connection_class(
                    channel, address, self.protocol
                )

    def remove_connection(self, channel, destroying=False):
        with self.lock:
            address = self.get_address(channel)
            if address in self.connections and channel in self.channels:
                self.connections[address].remove_listener(
                    channel,
                    destroying=destroying)
                self.channels.remove(channel)
                if self.connections[address].listener_count < 1:
                    del self.connections[address]
