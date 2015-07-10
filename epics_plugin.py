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
			self.connections.listeners.append(widget)
		else:
			self.connections[pv] = Connection(widget, pv)
			
class Connection(QObject):
	new_value_signal = pyqtSignal(float)
	def __init__(self, widget, pv, parent=None):
		super(Connection, self).__init__(parent)
		self.listeners = [widget]
		self.new_value_signal.connect(widget.recieveValue, Qt.QueuedConnection)
		widget.send_value_signal.connect(self.put_value, Qt.QueuedConnection)
		self.pv = epics.PV(pv, callback=self.send_new_value)
	
	def send_new_value(self, pvname=None, value=None, **kw):
		self.new_value_signal.emit(float(value))
	
	@pyqtSlot(float)
	def put_value(self, new_val):
		self.pv.put(new_val)