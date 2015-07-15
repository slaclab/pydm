import re
from PyQt4.QtCore import pyqtSlot, pyqtSignal, QObject, Qt, QTimer
import random

class FakePlugin:
	def __init__(self):
		self.connections = {}
		
	def add_connection(self, widget):	
		value = widget.channel.split("fake://")[1]
		if value in self.connections:
			self.connections[value].add_listener(widget)
		else:
			self.connections[value] = Connection(widget, value)
			
class Connection(QObject):
	new_value_signal = pyqtSignal(str)
	connection_state_signal = pyqtSignal(bool)
	new_severity_signal = pyqtSignal(int)
	def __init__(self, widget, value, parent=None):
		super(Connection, self).__init__(parent)
		self.add_listener(widget)
		self.value = value
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
		
	def add_listener(self, widget):
		self.connection_state_signal.connect(widget.connectionStateChanged, Qt.QueuedConnection)
		self.new_value_signal.connect(widget.recieveValue, Qt.QueuedConnection)
		self.new_severity_signal.connect(widget.alarmSeverityChanged, Qt.QueuedConnection)