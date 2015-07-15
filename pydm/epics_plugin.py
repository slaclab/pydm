import epics
import numpy as np
import re
from PyQt4.QtCore import pyqtSlot, pyqtSignal, QObject, Qt

class EPICSPlugin:
	def __init__(self):
		self.connections = {}
		
	def add_connection(self, widget):	
		pv = widget.channel.split("ca://")[1]
		if pv in self.connections:
			self.connections[pv].add_listener(widget)
		else:
			self.connections[pv] = Connection(widget, pv)
			
class Connection(QObject):
	new_value_signal = pyqtSignal(str)
	connection_state_signal = pyqtSignal(bool)
	new_severity_signal = pyqtSignal(int)
	def __init__(self, widget, pv, parent=None):
		super(Connection, self).__init__(parent)
		self.add_listener(widget)
		self.pv = epics.PV(pv, callback=self.send_new_value, connection_callback=self.send_connection_state, form='ctrl')
	
	def send_new_value(self, pvname=None, value=None, severity=None, *args, **kws):
		self.new_value_signal.emit(str(value))
		if severity != None:
			self.new_severity_signal.emit(int(severity))
			
	def send_connection_state(self, pvname=None, conn=None, *args, **kws):
		self.connection_state_signal.emit(conn)
	
	@pyqtSlot(str)
	def put_value(self, new_val):
		self.pv.put(new_val)
		
	def add_listener(self, widget):
		self.connection_state_signal.connect(widget.connectionStateChanged, Qt.QueuedConnection)
		self.new_value_signal.connect(widget.recieveValue, Qt.QueuedConnection)
		self.new_severity_signal.connect(widget.alarmSeverityChanged, Qt.QueuedConnection)
		widget.send_value_signal.connect(self.put_value, Qt.QueuedConnection)