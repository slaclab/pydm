from .base import PyDMWidget
from ..PyQt.QtGui import QWidget, QVBoxLayout, QHBoxLayout, QPainter, QColor, QPolygon, QPen, QLabel
from ..PyQt.QtCore import Qt, QPoint, pyqtSlot, pyqtProperty
from .channel import PyDMChannel
import sys


class QScale(QWidget):
	def __init__(self, parent=None):
		super(QScale, self).__init__(parent)
		self._value = 0
		self._lower_limit = 0
		self._upper_limit = 10
		#self._orientation = 'horizontal'
		self.position = 0 # unit: pixel

		self._bg_color = QColor('black')
		self._pointer_color = QColor('white')
		self._pointer_proportion = 0.05
		self._bg_proportion = 0.8

		self._divisions = 10
		self._tick_pen = QPen()
		self.tick_color = QColor('black')
		self._tick_width = 0
		self._painter = QPainter()


	def setTickPen(self):
		self._tick_pen.setColor(self.tick_color)
		self._tick_pen.setWidth(self._tick_width)

	def drawTicks(self):
		self._painter.setPen(self._tick_pen)
		division_size = self.width() / self._divisions
		tick_y0 = self._bg_proportion*self.height()
		tick_yf = self.height()
		# Draw ticks
		for i in range(self._divisions+1):
			self._painter.drawLine(i*division_size, tick_y0, i*division_size, tick_yf) # x1, y1, x2, y2

	def drawIndicator(self):
		# Draw a pointer as indicator
		if self.position < 0 or self.position > self.width():
			return
		self.setPosition()
		self._painter.setPen(Qt.transparent)
		self._painter.setBrush(self._pointer_color)
		pointer_width = self._pointer_proportion * self.width()
		pointer_height = self._bg_proportion * self.height()
		points = [
                QPoint(self.position, 0),
                QPoint(self.position + 0.5*pointer_width, 0.5*pointer_height),
                QPoint(self.position, pointer_height),
                QPoint(self.position - 0.5*pointer_width, 0.5*pointer_height)
        ]
		self._painter.drawPolygon(QPolygon(points))

	def drawBackground(self):
		self._painter.setPen(Qt.transparent)
		self._painter.setBrush(self._bg_color)
		bg_width = self.width()
		bg_height = self._bg_proportion * self.height()
		self._painter.drawRect(0, 0, bg_width, bg_height)

	def paintEvent(self, event):
		self._painter.begin(self)
		#self._painter.rotate(-90)
		self._painter.setRenderHint(QPainter.Antialiasing)
		self.drawBackground()
		self.drawTicks()
		self.drawIndicator()
		self._painter.end()

	def setPosition(self):
		try:
			proportion = (self._value - self._lower_limit) / (self._upper_limit - self._lower_limit)
		except:
			proportion = -1 # Invalid value
		#self.bar.setValue(proportion)
		#self.value = proportion
		self.position = int(proportion * self.width())

	def updateIndicator(self):
		self.setPosition()

	def setValue(self, value):
		self._value = value
		self.updateIndicator()
		self.repaint()

	def setUpperLimit(self, new_limit):
		self._upper_limit = new_limit

	def setLowerLimit(self, new_limit):
		self._lower_limit = new_limit
	
class PyDMScaleIndicator(PyDMWidget, QWidget):

	def __init__(self, parent=None, init_channel=None):
		#QScale.__init__(self, parent)
		PyDMWidget.__init__(self, init_channel=init_channel)
		self._show_value = True
		self._show_limits = True

		self.scale_indicator = QScale()
		self.value_label = QLabel()
		self.lower_label = QLabel()
		self.upper_label = QLabel()

		self.value_label.setText('<val>')
		self.lower_label.setText('<lopr>')
		self.upper_label.setText('<hopr>')
		
		self.value_label.setAlignment(Qt.AlignCenter)
		self.lower_label.setAlignment(Qt.AlignLeft)
		self.upper_label.setAlignment(Qt.AlignRight)

		self.buildLayout()

	def updateAll(self):
		if self._show_limits:
			self.lower_label.setText(str(self.scale_indicator._lower_limit))
			self.upper_label.setText(str(self.scale_indicator._upper_limit))
			self.value_label.setText(self.format_string.format(self.scale_indicator._value))

	def value_changed(self, new_value):
		super(PyDMScaleIndicator, self).value_changed(new_value)
		self.scale_indicator.setValue(new_value)
		self.updateAll()

	def upperCtrlLimitChanged(self, new_limit):
		super(PyDMScaleIndicator, self).upperCtrlLimitChanged(new_limit)
		self.scale_indicator.setUpperLimit(new_limit)
		self.updateAll()

	def lowerCtrlLimitChanged(self, new_limit):
		super(PyDMScaleIndicator, self).lowerCtrlLimitChanged(new_limit)
		self.scale_indicator.setLowerLimit(new_limit)
		self.updateAll()

	def buildLayout(self):
		self.limits_layout = QHBoxLayout()
		self.limits_layout.addWidget(self.lower_label)
		self.limits_layout.addWidget(self.upper_label)

		self.layout = QVBoxLayout()
		self.layout.addWidget(self.value_label)
		self.layout.addWidget(self.scale_indicator)
		self.layout.setContentsMargins(1, 1, 1, 1)
		self.layout.addItem(self.limits_layout)
		self.setLayout(self.layout)
