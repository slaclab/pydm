import random
from qtpy.QtCore import QTimer

from pydm.data_store import DataKeys
from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection

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
        self.data[DataKeys.CONNECTION] = True
        self.send_to_channel()


    def send_new_value(self):
        val_to_send = "{0}-{1}".format(self.value, random.randint(0, 9))
        self.data[DataKeys.VALUE] = (str(val_to_send))
        self.send_to_channel()


class FakePlugin(PyDMPlugin):
    protocol = "fake"
    connection_class = Connection

