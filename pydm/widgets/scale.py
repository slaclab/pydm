from .base import PyDMWidget
from ..PyQt.QtGui import QWidget, QVBoxLayout, QHBoxLayout, QPainter, QColor, QPolygon, QPen, QLabel
from ..PyQt.QtCore import Qt, QPoint, pyqtSlot, pyqtProperty
from .channel import PyDMChannel
import sys

class Scale(QWidget):

	def __init__(self, parent=None):
		super(Scale, self).__init__(parent)
		self._orientation = 'horizontal'
		self._divisions = 10
		self._painter = QPainter()
		self._pen = QPen()
		self._color = QColor('black')
		self._tick_width = 0

		self.setPen()
		self.show()

	def setPen(self):
		self._pen.setColor(self._color)
		self._pen.setWidth(self._tick_width)

	def drawScale(self):
		self._painter.setPen(self._pen)
		#self._painter.setBrush(QColor('green'))
		division_size = self.width() / self._divisions
		tick_size = self.height()
		# Draw ticks
		for i in range(self._divisions+1):
			self._painter.drawLine(i*division_size, 0, i*division_size, tick_size) # x1, y1, x2, y2

	def paintEvent(self, event):
		self._painter.begin(self)
		self._painter.setRenderHint(QPainter.Antialiasing)
		self.drawScale()
		self._painter.end()

class Bar(QWidget):

	def __init__(self, parent=None):
		super(Bar, self).__init__(parent)
		self._bar_color = 'lightgray'
		self._pointer_color = 'black'
		self._pointer_proportion = 0.05
		self.value = 0
		self.position = 0
		self._painter = QPainter()

	def setPosition(self):
		self.position = int(self.value * self.width())

	def setValue(self, proportion):
		self.value = proportion
		self.repaint()

	def drawIndicator(self):
		self.drawPointer()

	def drawPointer(self):
		if self.value < 0 or self.value > 1:
			return
		self.setPosition()
		self._painter.setPen(Qt.transparent)
		self._painter.setBrush(QColor(self._pointer_color))
		pointer_width = self._pointer_proportion * self.width()
		pointer_height = self.height()
		points = [
                QPoint(self.position, 0),
                QPoint(self.position + 0.5*pointer_width, 0.5*self.height()),
                QPoint(self.position, self.height()),
                QPoint(self.position - 0.5*pointer_width, 0.5*self.height())
        ]
		self._painter.drawPolygon(QPolygon(points))

	def drawBackground(self):
		self._painter.setPen(Qt.transparent)
		self._painter.setBrush(QColor(self._bar_color))
		self._painter.drawRect(0, 0, self.width(), self.height())

	def paintEvent(self, event):
		self._painter.begin(self)
		#self._painter.rotate(-90)
		self._painter.setRenderHint(QPainter.Antialiasing)
		self.drawBackground()
		self.drawIndicator()
		self._painter.end()

class QAbstractIndicator(QWidget):
	def __init__(self, parent=None):
		super(QAbstractIndicator, self).__init__(parent)
		self.bar = Bar()
		self.scale = Scale()

		self.value_label = QLabel()
		self.value_label.setAlignment(Qt.AlignCenter)
		self.value_label.setText('<val>')
		self.lower_label = QLabel()
		self.lower_label.setAlignment(Qt.AlignLeft)
		self.lower_label.setText('<lopr>')
		self.upper_label = QLabel()
		self.upper_label.setAlignment(Qt.AlignRight)
		self.upper_label.setText('<hopr>')

		self._lower_limit = 0
		self._upper_limit = 10
		self._value = 5
		self._show_value = True
		self._show_limits = True

		self.limits_layout = QHBoxLayout()
		self.limits_layout.addWidget(self.lower_label)
		self.limits_layout.addWidget(self.upper_label)

		self.layout = QVBoxLayout()
		self.layout.addWidget(self.value_label)
		self.layout.addWidget(self.bar)
		self.layout.addWidget(self.scale)
		self.layout.setContentsMargins(1, 1, 1, 1)
		self.layout.addItem(self.limits_layout)
		self.setLayout(self.layout)
		self.setValue(self.value)
		self.show()

	def update_indicator(self):
		try:
			proportion = (self.value - self._lower_limit) / (self._upper_limit - self._lower_limit)
		except:
			proportion = -1 # Invalid value
		self.bar.setValue(proportion)
		if self._show_limits:
			self.lower_label.setText(str(self._lower_limit))
			self.upper_label.setText(str(self._upper_limit))
			self.value_label.setText(str(self._value))

	def setUpperLimit(self, new_limit):
		self._upper_limit = new_limit

	def setLowerLimit(self, new_limit):
		self._lower_limit = new_limit

	def setValue(self, value):
		self._value = value
		self.update_indicator()
	
class PyDMScaleIndicator(QAbstractIndicator, PyDMWidget):

	def __init__(self, parent=None, init_channel=None):
		QAbstractIndicator.__init__(self, parent)
		PyDMWidget.__init__(self, init_channel=init_channel)
		self._lower_limit = -1
		self._upper_limit = 20

	def value_changed(self, new_value):
		super(PyDMScaleIndicator, self).value_changed(new_value)

		self.update_indicator()

	def upperCtrlLimitChanged(self, new_limit):
		super(PyDMScaleIndicator, self).upperCtrlLimitChanged(new_limit)
		upper = self.get_ctrl_limits()[1]
		self.setUpperLimit(upper)
		self.update_indicator()

	def lowerCtrlLimitChanged(self, new_limit):
		super(PyDMScaleIndicator, self).lowerCtrlLimitChanged(new_limit)
		lower = self.get_ctrl_limits()[0]
		self.setLowerLimit(lower)
		self.update_indicator()
