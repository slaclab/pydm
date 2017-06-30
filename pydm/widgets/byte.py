import sys
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient, QPixmap
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, Qt, QPoint, QRect
from .channel import PyDMChannel

class PyDMByte(QWidget):

	#Tell Designer what signals are available.
	__pyqtSignals__ = ("connected_signal()",
                     "disconnected_signal()")
	
	connected_signal = pyqtSignal()
	disconnected_signal = pyqtSignal()

	def __init__(self, parent=None, init_channel=None):
		super(PyDMByte, self).__init__(parent)
		self.value = None
		self._channels = None
		self._connected = False
		self.enum_strings = None
		self._channel = init_channel
		self._byte = ['0', '1']
		self._showLabel = True
		self._label = ['off', 'on']
		self._ledColor = ['red', 'green']
		self._squareLed = False
		self._useImage = False
		self._imagePath = ['']
		self._lineWidth = 1

		self.current_label = ''
		self.default_color = 'grey'
		self.current_color = self.default_color
		self.default_image_path = ''
		self.current_image_path = self.default_image_path
		self.resize(100,100)
		self.show()

	def paintEvent(self, event):
		qp = QPainter()
		qp.begin(self)
		qp.setRenderHint(QPainter.Antialiasing)
		if self._lineWidth > 0:
			qp.setPen(QPen(QColor(0, 0, 0),self._lineWidth))
		else:
			qp.setPen(QPen(Qt.transparent))
		if self._useImage:
			self.drawImage(qp, event)
		else:
			self.drawLed(qp, event)
		if self._showLabel:
			self.drawLabel(qp, event)
		qp.end()

	def drawLabel(self, qp, event):
		qp.setPen(QColor(0, 0, 0))
		qp.setFont(self.font())
		qp.drawText(event.rect(), Qt.AlignCenter, self.current_label)

	def drawLed(self, qp, event):
		# Define main brush
		gradient = QLinearGradient(0, 0, 0, self.height())
		gradient.setColorAt(0.0, QColor(self.current_color))
		gradient.setColorAt(1.0, QColor(255, 255, 255))
		qp.setBrush(QBrush(gradient))
		# Draw led
		if self._squareLed:
			x = 0
			y = 0
			lenx = self.width() - 2*self._lineWidth
			leny = self.height() - 2*self._lineWidth
			qp.drawRect(x, y, lenx, leny)
		else:
			x = self.width()*0.5
			y = self.height()*0.5
			radx = self.width()*0.5 - 2*self._lineWidth
			rady = self.height()*0.5 - 2*self._lineWidth
			center = QPoint(x, y)
			qp.drawEllipse(center, radx, rady)
		# Draw shine brush
		qp.setPen(Qt.transparent)
		shine_gradient = QLinearGradient(0, 0, 0, self.height()*0.4)
		gradient.setColorAt(0.0, QColor(255, 255, 255))
		gradient.setColorAt(1.0, Qt.transparent)
		qp.setBrush(QBrush(gradient))
		# Draw shine
		if self._squareLed:
			x = self.width()*0.1
			y = self.height()*0.1
			lenx = self.width()*0.8
			leny = self.height()*0.4
			qp.drawRect(x, y, lenx, leny)
		else:
			x = self.width()*0.5
			y = self.height()*0.35
			radx = self.width()*0.3
			rady = self.height()*0.2
			center = QPoint(x, y)
			qp.drawEllipse(center, radx, rady)

	def drawImage(self, qp, event):
		if self.current_image_path == self.default_image_path:
			pixmap = QPixmap(self.width(), self.height())
			pixmap.fill(QColor('black'))
		else:
			pixmap = QPixmap(self.current_image_path)
		qp.drawPixmap(event.rect(), pixmap)
		qp.drawRect(QRect(0, 0, self.width()-1, self.height()-1)) # Border

	@pyqtSlot(tuple)
	def enumStringsChanged(self, enum_strings):
		if enum_strings != self.enum_strings:
			self.enum_strings = enum_strings
			self.receiveValue(self.value)

	def updateCurrentLabel(self, new_value):
		if str(new_value) in self._byte:
			try:
				byte_index = self._byte.index(str(new_value))
				self.current_label = self._label[byte_index]
			except:
				self.current_label = ''
		elif isinstance(new_value, int) and self.enum_strings is not None:
		  	self.current_label = self.enum_strings[new_value]
		else:
			self.current_label = str(new_value)

	def updateCurrentColor(self, new_value):
		if str(new_value) in self._byte:
			try:
				byte_index = self._byte.index(str(new_value))
				self.current_color = self._ledColor[byte_index]
			except:
				self.current_label = self.default_color

	def updateCurrentImagePath(self, new_value):
		if str(new_value) in self._byte:
			try:
				byte_index = self._byte.index(str(new_value))
				self.current_image_path = self._imagePath[byte_index]
			except:
				self.current_image_path = self.default_image_path

	@pyqtSlot(float)
	@pyqtSlot(int)
	@pyqtSlot(str)
	def receiveValue(self, new_value):
		self.value = new_value
		if self._useImage:
			self.updateCurrentImagePath(new_value)
		else:
			self.updateCurrentColor(new_value)
		if self._showLabel:
			self.updateCurrentLabel(new_value)
		self.repaint()

	@pyqtSlot(bool)
	def connectionStateChanged(self, connected):
		self._connected = connected
		if connected:
			self.connected_signal.emit()
		else:
			self.disconnected_signal.emit()

	def getChannel(self):
		return str(self._channel)

	def setChannel(self, value):
		if self._channel != value:
  			self._channel = str(value)

	def resetChannel(self):
		self._channel = None

	channel = pyqtProperty(str, getChannel, setChannel, resetChannel)

	def getByte(self):
		return self._byte

	def setByte(self, value):
		if value != self._byte:
			self._byte = value

	def resetByte(self):
		self._byte = ['0', '1']

	byte = pyqtProperty("QStringList", getByte, setByte, resetByte)

	def getShowLabel(self):
		return self._showLabel

	def setShowLabel(self, value):
		if value != self._showLabel:
			self._showLabel = value

	def resetShowLabel(self):
		self._showLabel = True

	showLabel = pyqtProperty(bool, getShowLabel, setShowLabel, resetShowLabel)

	def getLabel(self):
		return self._label

	def setLabel(self, value):
		if value != self._label:
			self._label = value

	def resetLabel(self):
		self._label = ['off', 'on']

	label = pyqtProperty("QStringList", getLabel, setLabel, resetLabel)

	def getLedColor(self):
		return self._ledColor

	def setLedColor(self, value):
		if value != self._ledColor:
			self._ledColor = value

	def resetLedColor(self):
		self._ledColor = ['r', 'g']

	ledColor = pyqtProperty("QStringList", getLedColor, setLedColor, resetLedColor)

	def getSquareLed(self):
		return self._squareLed

	def setSquareLed(self, value):
		if value != self._squareLed:
			self._squareLed = value
			self.repaint()

	def resetSquareLed(self):
		self._squareLed = False

	squareLed = pyqtProperty(bool, getSquareLed, setSquareLed, resetSquareLed)

	def getUseImage(self):
		return self._useImage

	def setUseImage(self, value):
		if value != self._useImage:
			self._useImage = value
			self.repaint()

	def resetUseImage(self):
		self._useImage = False

	useImage = pyqtProperty(bool, getUseImage, setUseImage, resetUseImage)

	def getImagePath(self):
		return self._imagePath

	def setImagePath(self, value):
		if value != self._imagePath:
			self._imagePath = value

	def resetImagePath(self):
		self._imagePath = []

	imagePath = pyqtProperty("QStringList", getImagePath, setImagePath, resetImagePath)

	def getLineWidth(self):
		return self._lineWidth

	def setLineWidth(self, value):
		if value != self._lineWidth:
			self._lineWidth = value
			self.repaint()

	def resetLineWidth(self):
		self._lineWidth = 1

	lineWidth = pyqtProperty(int, getLineWidth, setLineWidth, resetLineWidth)

	def channels(self):
		if self._channels != None:
			return self._channels
		self._channels = [PyDMChannel(address=self.channel, connection_slot=self.connectionStateChanged, value_slot=self.receiveValue, enum_strings_slot=self.enumStringsChanged)]
		return self._channels

if __name__ == '__main__':
	app = QApplication(sys.argv)
	ex = PyDMByte()
	sys.exit(app.exec_())