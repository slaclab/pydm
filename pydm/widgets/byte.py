import sys
import re
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient, QPixmap, QPainterPath,QFontMetrics
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, Qt, QPoint, QRect
from .channel import PyDMChannel
from ..application import PyDMApplication

class PyDMByte(QWidget):

	#Tell Designer what signals are available.
	__pyqtSignals__ = ("connected_signal()",
                     "disconnected_signal()")
	
	connected_signal = pyqtSignal()
	disconnected_signal = pyqtSignal()

	NO_ALARM = 0x0
	ALARM_TEXT = 0x1
	ALARM_BORDER = 0x2

	ALARM_NONE = 0
	ALARM_MINOR = 1
	ALARM_MAJOR = 2
	ALARM_INVALID = 3
	ALARM_DISCONNECTED = 4

	#We put all this in a big dictionary to try to avoid constantly allocating and deallocating new stylesheet strings.
	alarm_style_sheet_map = {
		NO_ALARM: {
			ALARM_NONE: "PyDMByte {}",
			ALARM_MINOR: "PyDMByte {}",
			ALARM_MAJOR: "PyDMByte {}",
			ALARM_INVALID: "PyDMByte {}",
			ALARM_DISCONNECTED: "PyDMByte {}"
		},
		ALARM_TEXT: {
			ALARM_NONE: "PyDMByte {color: black;}",
			ALARM_MINOR: "PyDMByte {color: yellow;}",
			ALARM_MAJOR: "PyDMByte {color: red;}",
			ALARM_INVALID: "PyDMByte {color: purple;}",
			ALARM_DISCONNECTED: "PyDMByte {color: white;}"
		},
		ALARM_BORDER: {
			ALARM_NONE: "PyDMByte {}",
			ALARM_MINOR: "PyDMByte {border: yellow;}",
			ALARM_MAJOR: "PyDMByte {border: red;}",
			ALARM_INVALID: "PyDMByte {border: purple;}",
			ALARM_DISCONNECTED: "PyDMByte {border: white;}"
		},
		ALARM_TEXT | ALARM_BORDER: {
			ALARM_NONE: "PyDMByte {color: black;}",
			ALARM_MINOR: "PyDMByte {color: yellow; border: yellow;}",
			ALARM_MAJOR: "PyDMByte {color: red; border: red;}",
			ALARM_INVALID: "PyDMByte {color: purple; border: purple;}",
			ALARM_DISCONNECTED: "PyDMByte {color: white; border: white;}"
		}
	}

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
		self._lineWidth = 2
		self._alarm_sensitive_text = True
		self._alarm_sensitive_border = True
		self._alarm_flags = (self.ALARM_TEXT * self._alarm_sensitive_text) | (self.ALARM_BORDER * self._alarm_sensitive_border)

		self.current_label = ''
		self.default_color = 'black'
		self.current_color = self.default_color
		self.default_image_path = ''
		self.current_image_path = self.default_image_path
		self.resize(100,100)
		self.setFont(QFont('Arial', pointSize=14, weight=QFont.Bold))	# Default font
		#If this label is inside a PyDMApplication (not Designer) start it in the disconnected state.
		app = QApplication.instance()
		if isinstance(app, PyDMApplication):
			self.alarmSeverityChanged(self.ALARM_DISCONNECTED)

	def getLabelColor(self):
		stylesheet = self.styleSheet()
		stylesheet_raw = stylesheet.replace(' ', '').replace('\n', '')
		reg_ex = '((?<=^color:)|(?<=;color:)|(?<={color:)).*?((?=$)|(?=;)|(?=}))'
		try:
			color_property = re.search(reg_ex, stylesheet_raw).group(0)
		except:
			color_property = 'black'
		return color_property

	def getBorderColor(self):
		stylesheet = self.styleSheet()
		stylesheet_raw = stylesheet.replace(' ', '').replace('\n', '')
		reg_ex = '((?<=^border:)|(?<=;border:)|(?<={border:)).*?((?=$)|(?=;)|(?=}))'
		try:
			border_property = re.search(reg_ex, stylesheet_raw).group(0)
		except:
			border_property = Qt.transparent
		return border_property

	def drawLabel(self, qp, event):
		text_color = self.getLabelColor()
		text_line_width = 1
		qp.setBrush(QColor(text_color))
		qp.setPen(QPen(QColor('black'), text_line_width))
		text_width = QFontMetrics(self.font()).width(self.current_label)
		text_height = QFontMetrics(self.font()).height()
		text_pos_x = (event.rect().width()- text_width)*0.5
		text_pos_y = event.rect().center().y() + text_height*0.5
		qp_path = QPainterPath()
		qp_path.addText(text_pos_x, text_pos_y, self.font(), self.current_label);
		qp.drawPath(qp_path)

	def drawLed(self, qp, event):
		# Define shadow brushgradient = QLinearGradient(0, 0, 0, self.height())
		gradient_shadow = QLinearGradient(0, 0, 0, self.height())
		gradient_shadow.setColorAt(0.0, QColor('darkgrey'))
		gradient_shadow.setColorAt(1.0, QColor('lightgrey'))
		qp.setBrush(QBrush(gradient_shadow))
		# Draw shadow
		if self._squareLed:
			x = 0
			y = 0
			lenx = self.width()
			leny = self.height()
			qp.drawRect(x, y, lenx, leny)
		else:
			x = self.width()*0.5
			y = self.height()*0.5
			radx = self.width()*0.5 - 1
			rady = self.height()*0.5 - 1
			center = QPoint(x, y)
			qp.drawEllipse(center, radx, rady)
		# Define led color brush
		qp.setPen(QPen(QColor('gray'), self.width()*0.02))
		gradient_led = QLinearGradient(0, 0, 0, self.height())
		gradient_led.setColorAt(0.0, QColor(self.current_color))
		gradient_led.setColorAt(1.0, QColor(255, 255, 255))
		qp.setBrush(QBrush(gradient_led))
		# Draw led
		if self._squareLed:
			x = round(self.width()*0.15)
			y = round(self.height()*0.15)
			lenx = self.width() - 2*x
			leny = self.height() - 2*y
			qp.drawRect(x, y, lenx, leny)
		else:
			x = self.width()*0.5
			y = self.height()*0.5
			radx = self.width()*0.35
			rady = self.height()*0.35
			center = QPoint(x, y)
			qp.drawEllipse(center, radx, rady)
		# Define shine brush
		qp.setPen(Qt.transparent)
		gradient_shine = QLinearGradient(0, 0, 0, self.height()*0.4)
		gradient_shine.setColorAt(0.0, QColor('white'))
		gradient_shine.setColorAt(1.0, Qt.transparent)
		qp.setBrush(QBrush(gradient_shine))
		# Draw shine
		if self._squareLed:
			x = round(self.width()*0.23)
			y = round(self.height()*0.23)
			lenx = self.width() - 2*x
			leny = self.height() - 2*y
			radx = self.width()*0.05
			rady = self.height()*0.05
			qp.drawRoundedRect(x, y, lenx, leny, radx, rady)
		else:
			x = self.width()*0.5
			y = self.height()*0.42
			radx = self.width()*0.25
			rady = self.height()*0.2
			center = QPoint(x, y)
			qp.drawEllipse(center, radx, rady)

	def drawImage(self, qp, event):
		if self.current_image_path == self.default_image_path:
			pixmap = QPixmap(self.width(), self.height())
			pixmap.fill(QColor('white'))
		else:
			pixmap = QPixmap(self.current_image_path)
		qp.drawPixmap(event.rect(), pixmap)
		qp.drawRect(QRect(0, 0, self.width()-1, self.height()-1)) # Border

	def paintEvent(self, event):
		qp = QPainter()
		qp.begin(self)
		qp.setRenderHint(QPainter.Antialiasing)
		border_property = self.getBorderColor()
		if self._lineWidth > 0:
			qp.setPen(QPen(QColor(border_property),self._lineWidth))
		else:
			qp.setPen(QPen(Qt.transparent))
		if self._useImage:
			self.drawImage(qp, event)
		else:
			self.drawLed(qp, event)
		if self._showLabel:
			self.drawLabel(qp, event)
		qp.end()

	@pyqtSlot(tuple)
	def enumStringsChanged(self, enum_strings):
		if enum_strings != self.enum_strings:
			self.enum_strings = enum_strings
			self.receiveValue(self.value)

	def updateCurrentLabel(self, new_value):
		try:
			byte_index = self._byte.index(str(new_value))
			self.current_label = self._label[byte_index]
			return
		except:
			pass
		try:
			self.current_label = self.enum_strings[new_value]
		except:
			self.current_label = str(new_value)

	def updateCurrentColor(self, new_value):
		try:
			byte_index = self._byte.index(str(new_value))
			self.current_color = self._ledColor[byte_index]
		except:
			self.current_color = self.default_color

	def updateCurrentImagePath(self, new_value):
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

	# -2 to +2, -2 is LOLO, -1 is LOW, 0 is OK, etc.  
	@pyqtSlot(int)
	def alarmStatusChanged(self, new_alarm_state):
		pass

	#0 = NO_ALARM, 1 = MINOR, 2 = MAJOR, 3 = INVALID  
	@pyqtSlot(int)
	def alarmSeverityChanged(self, new_alarm_severity):
		if not self._connected:
			new_alarm_severity = self.ALARM_DISCONNECTED
		self.setStyleSheet(self.alarm_style_sheet_map[self._alarm_flags][new_alarm_severity])

	# Properties
	@pyqtProperty(bool, doc=
	"""
	Whether or not the label's text color changes when alarm severity changes.
	"""
	)
	def alarmSensitiveText(self):
		return self._alarm_sensitive_text

	@alarmSensitiveText.setter
	def alarmSensitiveText(self, checked):
		self._alarm_sensitive_text = checked
		self._alarm_flags = (self.ALARM_TEXT * self._alarm_sensitive_text) | (self.ALARM_BORDER * self._alarm_sensitive_border)

	@pyqtProperty(bool, doc=
	"""
	Whether or not the label's border color changes when alarm severity changes.
	"""
	)
	def alarmSensitiveBorder(self):
		return self._alarm_sensitive_border

	@alarmSensitiveBorder.setter
	def alarmSensitiveBorder(self, checked):
		self._alarm_sensitive_border = checked
		self._alarm_flags = (self.ALARM_TEXT * self._alarm_sensitive_text) | (self.ALARM_BORDER * self._alarm_sensitive_border)

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
		self._channels = [PyDMChannel(address=self.channel, connection_slot=self.connectionStateChanged, value_slot=self.receiveValue, severity_slot=self.alarmSeverityChanged, enum_strings_slot=self.enumStringsChanged)]
		return self._channels

if __name__ == '__main__':
	app = QApplication(sys.argv)
	ex = PyDMByte()
	sys.exit(app.exec_())