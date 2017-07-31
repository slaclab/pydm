from .plugin import PyDMPlugin, PyDMConnection
from ..PyQt.QtCore import QTimer, pyqtSignal, Qt
import random

class Connection(PyDMConnection):
	def __init__(self, widget, address, parent=None):
		super(Connection, self).__init__(widget, address, parent)
		self.add_listener(widget)
		self.value = address
		self.rand = 0
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.send_new_value)
		self.timer.start(1000)
		self.send_connection_state(True)

	def send_new_value(self):
		val_to_send = "{0}-{1}".format(self.value, random.randint(0,9))
		self.new_value_signal.emit(str(val_to_send))
		
	def send_connection_state(self, conn):
		self.connection_state_signal.emit(conn)

class FakePlugin(PyDMPlugin):
	protocol = "fake"
	connection_class = Connection
			
