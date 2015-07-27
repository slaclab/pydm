from PyQt4.QtGui import QApplication, QColor
import re
from .epics_plugin import EPICSPlugin
from .fake_plugin import FakePlugin

class PyDMApplication(QApplication):
	plugins = { "ca": EPICSPlugin(), "fake": FakePlugin() }
	
	#HACK. To be replaced with some stylesheet stuff eventually.
	alarm_severity_color_map = {
		0: QColor(0, 0, 0), #NO_ALARM
		1: QColor(200, 200, 20), #MINOR_ALARM
		2: QColor(240, 0, 0), #MAJOR_ALARM
		3: QColor(240, 240, 0) #INVALID_ALARM
	}
	
	#HACK. To be replaced with some stylesheet stuff eventually.
	connection_status_color_map = {
		False: QColor(255, 255, 255),
		True: QColor(0, 0, 0,)
	}
	
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