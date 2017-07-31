from ..PyQt.QtGui import QFrame, QApplication, QLabel, QVBoxLayout
from ..PyQt.QtCore import Qt
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty
import json
import os.path
from ..application import PyDMApplication

class PyDMEmbeddedDisplay(QFrame):
	def __init__(self, parent=None):
		super(PyDMEmbeddedDisplay, self).__init__(parent=parent)
		self.app = QApplication.instance()
		self._filename = None
		self._macros = None
		self._embedded_widget = None
		self._disconnect_when_hidden = True
		self._is_connected = False
		self.layout = QVBoxLayout(self)
		self.err_label = QLabel(self)
		self.err_label.setAlignment(Qt.AlignHCenter)
		self.layout.addWidget(self.err_label)
		self.layout.setContentsMargins(0,0,0,0)
		self.err_label.hide()
		if not isinstance(self.app, PyDMApplication):
			self.setFrameShape(QFrame.Box)
		else:
			self.setFrameShape(QFrame.NoFrame)
	
	@pyqtProperty(str, doc=
	"""
	JSON-formatted string containing macro variables to pass to the embedded file.
	""")
	def macros(self):
		if self._macros is None:
			return ""
		return self._macros
	
	@macros.setter
	def macros(self, new_macros):
		self._macros = str(new_macros)
	
	# WARNING:  If the macros property is not defined before the filename property,
	# The widget will not have any macros defined when it loads the embedded file.
	# Yeah, this is stupid.  It needs to be fixed.
	
	@pyqtProperty(str, doc=
	"""
	Filename of the display to embed.
	"""
	)
	def filename(self):
		if self._filename is None:
			return ""
		return self._filename

	@filename.setter
	def filename(self, filename):
		filename = str(filename)
		if filename != self._filename:
			self._filename = filename
			#If we arent in a PyDMApplication (usually that means we are in Qt Designer),
			# don't try to load the file, just show text with the filename.
			if not isinstance(self.app, PyDMApplication):
				self.err_label.setText(self._filename)
				self.err_label.show()
				return				
			try:
				self.embedded_widget = self.open_file()					
			except ValueError as e:
				self.err_label.setText("Could not parse macro string.\nError: {}".format(e))
				self.err_label.show()
			except IOError as e:
				self.err_label.setText("Could not open {filename}.\nError: {err}".format(filename=self._filename, err=e))
				self.err_label.show()
		
	def open_file(self):
		"""
		Opens the widget specified in the widget's filename property.
		:rtyp: QWidget
		"""
		parsed_macros = None
		if self.macros is not None and len(self.macros) > 0:
			parsed_macros = json.loads(self.macros)
		if os.path.isabs(self.filename):
			return self.app.open_file(self.filename, macros=parsed_macros)
		else:
			return self.app.open_relative(self.filename, self, macros=parsed_macros)
	
	@property
	def embedded_widget(self):
		return self._embedded_widget
	
	@embedded_widget.setter
	def embedded_widget(self, new_widget):
		if new_widget is self._embedded_widget:
			return
		if self._embedded_widget is not None:
			self.layout.removeWidget(self._embedded_widget)
			self.app.close_widget_connections(self._embedded_widget)
			self._embedded_widget.deleteLater()
			self._embedded_widget = None
		self._embedded_widget = new_widget
		self._embedded_widget.setParent(self)
		self.layout.addWidget(self._embedded_widget)
		self.err_label.hide()
		self._embedded_widget.show()
		self.app.establish_widget_connections(self._embedded_widget)
		self._is_connected = True
	
	def connect(self):
		if self._is_connected or self.embedded_widget is None:
			return
		self.app.establish_widget_connections(self.embedded_widget)
	
	def disconnect(self):
		if not self._is_connected or self.embedded_widget is None:
			return
		self.app.close_widget_connections(self.embedded_widget)
	
	@pyqtProperty(bool, doc="""Disconnect from PVs when this widget is not visible.""")
	def disconnectWhenHidden(self):
		return self._disconnect_when_hidden
	
	@disconnectWhenHidden.setter
	def disconnectWhenHidden(self, disconnect_when_hidden):
		self._disconnect_when_hidden = disconnect_when_hidden
		
	def showEvent(self, e):
		if self.disconnectWhenHidden:
			self.connect()
	
	def hideEvent(self, e):
		if self.disconnectWhenHidden:
			self.disconnect()
		
