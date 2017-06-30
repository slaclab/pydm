import sys
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient
from PyQt5.QtCore import pyqtProperty, Qt, QPoint

class PyDMByte(QWidget):
	def __init__(self, parent=None):
		super(PyDMByte, self).__init__(parent)
		self._ledColor = []
		self._text = []
		self._squareLed = False
		self._lineWidth = 1
		self._imagePath = []
		self._useImage = False

		self.resize(100,100)
		self._text.append('on')
		self.show()

	def getSquareLed(self):
		return self._squareLed

	def setSquareLed(self, value):
		if value != self._squareLed:
			self._squareLed = value
			self.repaint()

	def resetSquareLed(self):
		if self._squareLed != False:
			self._squareLed = False

	squareLed = pyqtProperty(bool, getSquareLed, setSquareLed, resetSquareLed)

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


if __name__ == '__main__':
	app = QApplication(sys.argv)
	ex = PyDMByte()
	sys.exit(app.exec_())