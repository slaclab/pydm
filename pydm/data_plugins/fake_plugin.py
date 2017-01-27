from .plugin import PyDMPlugin, PyDMConnection
from ..PyQt.QtCore import QTimer, pyqtSignal, Qt
import random
import time
class Connection(PyDMConnection):
	protocol = "fake://"
	def __init__(self, channel_name, parent=None):
		super(Connection, self).__init__(channel_name, parent)
		self.add_listener()
		self.value = self.address
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.send_new_value)
		self.timer.start(100)
		
	def send_new_value(self):
		#val_to_send = "{0}-{1}".format(self.value, random.randint(0,9))
		val_to_send = "{0}".format(random.randint(0,9))
		self.data_message_signal.emit(self.new_value_message(str(val_to_send), time.time()))
		
	def send_connection_state(self, conn):
		self.data_message_signal.emit(self.connection_state_message(conn, time.time()))

	def send_severity(self, sevr):
		self.data_message_signal.emit(self.severity_message(sevr, time.time()))
		
	def add_listener(self):
		self.send_connection_state(True)
		self.send_severity(0)
		super(Connection, self).add_listener()

class FakePlugin(PyDMPlugin):
	protocol = "fake://"
	connection_class = Connection
