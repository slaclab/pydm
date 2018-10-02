from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection
from qtpy.QtCore import QTimer
import random


class Connection(PyDMConnection):

    def __init__(self, widget, address, protocol=None, parent=None):
        super(Connection, self).__init__(widget, address, protocol, parent)
        self.add_listener(widget)
        self.value = address
        self.rand = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.send_new_value)
        self.timer.start(1000)
        self.connected = True

    def send_new_value(self):
        val_to_send = "{0}-{1}".format(self.value, random.randint(0, 9))
        self.new_value_signal[str].emit(str(val_to_send))

    def send_connection_state(self, conn):
        self.connection_state_signal.emit(conn)

    def add_listener(self, widget):
        super(Connection, self).add_listener(widget)
        self.send_connection_state(True)


class FakePlugin(PyDMPlugin):
    protocol = "fake"
    connection_class = Connection

