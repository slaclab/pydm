import sys
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, Qt, QPoint
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
		self._channel = init_channel
		self._byte = ['0', '1']
		self._text = ['off', 'on']
		self._ledColor = ['r', 'g']
		self._squareLed = False
		self._useImage = False
		self._imagePath = []
		self._lineWidth = 1

		self.resize(100,100)
		self.show()

	def paintEvent(self, event):
		qp = QPainter()
		qp.begin(self)
		qp.setRenderHint(QPainter.Antialiasing)
		self.drawLedIndicator(qp, event)
		self.drawText(qp, event)
		qp.end()

	def drawText(self, qp, event):
		qp.setPen(QColor(0, 0, 0))
		qp.setFont(self.font())
		qp.drawText(event.rect(), Qt.AlignCenter, self._text[0])

	def drawLedIndicator(self, qp, event):
		# Define main brush
		if self._lineWidth > 0:
			qp.setPen(QPen(QColor(0, 0, 0),self._lineWidth))
		else:
			qp.setPen(QPen(Qt.transparent))
		gradient = QLinearGradient(0, 0, 0, self.height())
		gradient.setColorAt(0.0, QColor(0, 255, 0))
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
		#gradient.setColorAt(0.7, Qt.transparent)
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

	@pyqtSlot(float)
	@pyqtSlot(int)
	@pyqtSlot(str)
	def receiveValue(self, new_value):
		self.value = new_value
		'''
		if isinstance(new_value, str):
		  self.setText(new_value)
		  return
		if isinstance(new_value, float):
		  if self.format_string:
		    self.setText(self.format_string.format(new_value))
		    return
		if self.enum_strings is not None and isinstance(new_value, int):
		  self.setText(self.enum_strings[new_value])
		  return
		self.setText(str(new_value))
		'''

	@pyqtSlot(bool)
	def connectionStateChanged(self, connected):
		print('connected = ' + str(connected))
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

	def getText(self):
		return self._text

	def setText(self, value):
		if value != self._text:
			self._text = value

	def resetText(self):
		self._text = ['off', 'on']

	text = pyqtProperty("QStringList", getText, setText, resetText)

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

	def channels(self):
		if self._channels != None:
			return self._channels
		self._channels = [PyDMChannel(address=self.channel, connection_slot=self.connectionStateChanged, value_slot=self.receiveValue)]
		return self._channels

if __name__ == '__main__':
	app = QApplication(sys.argv)
	ex = PyDMByte()
	sys.exit(app.exec_())