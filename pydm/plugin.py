from PyQt4.QtCore import pyqtSlot, pyqtSignal, QObject, Qt
from numpy import ndarray
class PyDMConnection(QObject):
	new_value_signal = pyqtSignal(str)
	new_waveform_signal = pyqtSignal(ndarray)
	connection_state_signal = pyqtSignal(bool)
	new_severity_signal = pyqtSignal(int)
	def __init__(self, widget, address, parent=None):
		super(PyDMConnection, self).__init__(parent)
	
	def add_listener(self, widget):
		self.connection_state_signal.connect(widget.connectionStateChanged, Qt.QueuedConnection)
		try:
			self.new_value_signal.connect(widget.recieveValue, Qt.QueuedConnection)
		except:
			pass

		try:
			self.new_waveform_signal.connect(widget.recieveWaveform, Qt.QueuedConnection)
		except:
			pass
		self.new_severity_signal.connect(widget.alarmSeverityChanged, Qt.QueuedConnection)

class PyDMPlugin:
	protocol = None
	connection_class = PyDMConnection
	def __init__(self):
		self.connections = {}
		
	def add_connection(self, widget):	
		address = str(widget.channel.split(self.protocol)[1])
		if address in self.connections:
			self.connections[address].add_listener(widget)
		else:
			self.connections[address] = self.connection_class(widget, address)
			
