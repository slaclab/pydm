from PyQt4.QtCore import pyqtSlot, pyqtSignal, QObject, Qt

class PyDMConnection(QObject):
	new_value_signal = pyqtSignal(str)
	connection_state_signal = pyqtSignal(bool)
	new_severity_signal = pyqtSignal(int)
	def __init__(self, widget, address, parent=None):
		super(PyDMConnection, self).__init__(parent)
	
	def add_listener(self, widget):
		pass

class PyDMPlugin:
	protocol = None
	connection_class = PyDMConnection
	def __init__(self):
		self.connections = {}
		
	def add_connection(self, widget):	
		address = widget.channel.split(self.protocol)[1]
		if address in self.connections:
			self.connections[address].add_listener(widget)
		else:
			self.connections[address] = self.connection_class(widget, address)
			
