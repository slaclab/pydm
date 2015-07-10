from PyQt4 import QtCore, QtGui
import re
from epics_plugin import EPICSPlugin

class PyDMLabel(QtGui.QLabel):
	send_value_signal = QtCore.pyqtSignal(float)
	def __init__(self, channel, parent=None):
		super(PyDMLabel, self).__init__(parent)
		self.channel = channel
		
	@QtCore.pyqtSlot(float)
	def recieveValue(self, newValue):
		self.setText(str(newValue))
		
class PyDMApplication(QtGui.QApplication):
	plugins = { "ca": EPICSPlugin() }
	
	def start_connections(self):
		for widget in self.allWidgets():
			if hasattr(widget, 'channel'):
				self.add_connection(widget)
	
	def add_connection(self, widget):
		match = re.match('.*://', widget.channel)
		if match:
			try:
				protocol = match.group(0)[:-3]
				plugin_to_use = self.plugins[protocol]
				plugin_to_use.add_connection(widget)
			except KeyError:
				print "Couldn't find plugin: {0}".format(match.group(0)[:-3])