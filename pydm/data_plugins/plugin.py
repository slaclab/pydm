import threading
import weakref

from qtpy.QtCore import Slot, Signal, QObject, Qt
from qtpy import QtWidgets

from ..data_store import DataStore, DataKeys, DEFAULT_INTROSPECTION
from ..utilities.remove_protocol import protocol_and_address
from ..utilities.channel import parse_channel_config


def safe_disconnect_signal(signal, slot):
    try:
        if slot is not None:
            signal.disconnect(slot)
        else:
            signal.disconnect()
    except TypeError:
        pass

class BaseParameterEditor(QtWidgets.QWidget):
    def __init__(self, parent=None, *args, **kwargs):
        super(BaseParameterEditor, self).__init__(parent, *args, **kwargs)

    @property
    def parameters(self):
        raise NotImplementedError

    @parameters.setter
    def parameters(self, params):
        raise NotImplementedError

    def validate(self):
        raise NotImplementedError


class DefaultParameterEditor(BaseParameterEditor):
    def __init__(self, parent=None):
        super(DefaultParameterEditor, self).__init__(parent)
        self.setLayout(QtWidgets.QFormLayout())
        self.edit_address = QtWidgets.QLineEdit(self)
        self.layout().setFieldGrowthPolicy(
            QtWidgets.QFormLayout.AllNonFixedFieldsGrow
        )

        self.layout().addRow(QtWidgets.QLabel('Address:'), self.edit_address)

    @property
    def parameters(self):
        return {'address': self.edit_address.text()}

    @parameters.setter
    def parameters(self, params):
        address = params.get('address', '')
        self.edit_address.setText(address)

    def validate(self):
        return True, ''

    def clear(self):
        self.edit_address.setText('')

    @staticmethod
    def get_repr(parameters):
        return parameters.get('address', '')


class PyDMConnection(QObject):
    notify = Signal()

    def __init__(self, channel, address, protocol=None, parent=None):
        super(PyDMConnection, self).__init__(parent)
        self.connected = False
        self.data = {}
        self.introspection = DEFAULT_INTROSPECTION
        self.channel = channel
        self.protocol = protocol
        self.address = address
        self.listener_count = 0
        self.app = QtWidgets.QApplication.instance()
        self.add_listener(channel)

    def add_listener(self, channel):
        self.listener_count = self.listener_count + 1
        self.notify.connect(channel.notified, Qt.QueuedConnection)
        channel.transmit.connect(self._validate_data_from_channel,
                                 Qt.QueuedConnection)

    def remove_listener(self, channel, destroying=False):
        if not channel.connected():
            return
        if not destroying:
            safe_disconnect_signal(self.notify, channel.notified)
            safe_disconnect_signal(self.channel.transmit, self._validate_data_from_channel)

        self.listener_count = self.listener_count - 1
        if self.listener_count < 1:
            self.close()

    def close(self):
        DataStore.remove(self.address)

    @Slot(dict)
    def _validate_data_from_channel(self, payload):
        # if is_read_only():
        #     return
        self.receive_from_channel(payload)

    def receive_from_channel(self, payload):
        pass

    def send_to_channel(self):
        self.introspection.get(DataKeys.CONNECTION, 'CONNECTION')
        self.connected = self.data.get('CONNECTION', False)
        DataStore[self.channel.address] = (self.data, self.introspection)
        self.notify.emit()


class PyDMPlugin(object):
    protocol = None
    connection_class = PyDMConnection
    param_editor = DefaultParameterEditor

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

    def get_repr(self, channel):
        config = parse_channel_config(channel, force_dict=True)
        conn = config.get('connection', {})
        params = conn.get('parameters', {})
        suffix = self.param_editor.get_repr(params)
        return '{}://{}'.format(self.protocol, suffix)