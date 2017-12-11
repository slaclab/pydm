from .base import PyDMWidget, compose_stylesheet
from ..PyQt.QtGui import QFrame, QVBoxLayout, QHBoxLayout, QPainter, QColor, QPolygon, QPen, QLabel, QSizePolicy, QWidget
from ..PyQt.QtCore import Qt, QPoint, pyqtProperty
from .channel import PyDMChannel
import sys


class QScale(QFrame):
    def __init__(self, parent=None):
        super(QScale, self).__init__(parent)
        self._value = 5
        self._lower_limit = 0
        self._upper_limit = 10
        self.position = None # unit: pixel

        self._bg_color = QColor('darkgray')
        self._bg_size_rate = 0.8    # from 0 to 1

        self._indicator_color = QColor('black')
        self._pointer_width_rate = 0.05
        self._barIndicator = False

        self._num_divisions = 10
        self._show_ticks = True
        self._tick_pen = QPen()
        self._tick_color = QColor('black')
        self._tick_width = 0
        self._tick_size_rate = 0.1 # from 0 to 1
        self._painter = QPainter()

        self._painter_rotation = None
        self._painter_translation = None
        self._orientation = None
        self._widget_width = None
        self._widget_height = None
        self.setOrientation(Qt.Horizontal)

        self.setMinimumSize(0, 2)
        self.setPosition()

    def adjustDimensions(self):
        if self._orientation == Qt.Horizontal:
            self._widget_width = self.width()
            self._widget_height = self.height()
            self._painter_translation = 0
            self._painter_rotation = 0
        elif self._orientation == Qt.Vertical:
            # Invert dimensions for paintEvent()
            self._widget_width = self.height()
            self._widget_height = self.width()
            self._painter_translation = self._widget_width
            self._painter_rotation = -90

    def setTickPen(self):
        self._tick_pen.setColor(self._tick_color)
        self._tick_pen.setWidth(self._tick_width)

    def drawTicks(self):
        if not self._show_ticks:
            return
        self.setTickPen()
        self._painter.setPen(self._tick_pen)
        division_size = self._widget_width / self._num_divisions
        tick_y0 = self._widget_height
        tick_yf = (1 - self._tick_size_rate)*self._widget_height
        for i in range(self._num_divisions+1):
            x = i*division_size
            self._painter.drawLine(x, tick_y0, x, tick_yf) # x1, y1, x2, y2

    def drawBar(self):
        # Draw a bar as indicator of current value
        if self.position < 0 or self.position > self._widget_width:
            return
        self.setPosition()
        self._painter.setPen(Qt.transparent)
        self._painter.setBrush(self._indicator_color)
        bar_height = self._bg_size_rate * self._widget_height
        self._painter.drawRect(0, 0, self.position, bar_height)

    def drawPointer(self):
        # Draw a pointer as indicator of current value
        if self.position < 0 or self.position > self._widget_width:
            return
        self.setPosition()
        self._painter.setPen(Qt.transparent)
        self._painter.setBrush(self._indicator_color)
        pointer_width = self._pointer_width_rate * self._widget_width
        pointer_height = self._bg_size_rate * self._widget_height
        points = [
                QPoint(self.position, 0),
                QPoint(self.position + 0.5*pointer_width, 0.5*pointer_height),
                QPoint(self.position, pointer_height),
                QPoint(self.position - 0.5*pointer_width, 0.5*pointer_height)
        ]
        self._painter.drawPolygon(QPolygon(points))

    def drawIndicator(self):
        if self._barIndicator == True:
            self.drawBar()
        else:
            self.drawPointer()

    def drawBackground(self):
        self._painter.setPen(Qt.transparent)
        self._painter.setBrush(self._bg_color)
        bg_width = self._widget_width
        bg_height = self._bg_size_rate * self._widget_height
        self._painter.drawRect(0, 0, bg_width, bg_height)

    def paintEvent(self, event):
        self.adjustDimensions()
        self._painter.begin(self)
        self._painter.translate(0, self._painter_translation)
        self._painter.rotate(self._painter_rotation)
        self._painter.setRenderHint(QPainter.Antialiasing)

        self.drawBackground()
        self.drawTicks()
        self.drawIndicator()
        
        self._painter.end()

    def setPosition(self):
        try:
            proportion = (self._value - self._lower_limit) / (self._upper_limit - self._lower_limit)
        except:
            proportion = -1 # Invalid
        self.position = int(proportion * self._widget_width)

    def updateIndicator(self):
        self.setPosition()
        self.repaint()

    def setValue(self, value):
        self._value = value
        self.updateIndicator()

    def setUpperLimit(self, new_limit):
        self._upper_limit = new_limit

    def setLowerLimit(self, new_limit):
        self._lower_limit = new_limit

    def getShowTicks(self):
        return self._show_ticks

    def setShowTicks(self, checked):
        if self._show_ticks != bool(checked):
            self._show_ticks = checked
            self.repaint()

    def getOrientation(self):
        return self._orientation

    def setOrientation(self, orientation):
        self._orientation = orientation
        self.adjustDimensions()
        self.repaint()

    def getBarIndicator(self):
        return self._barIndicator

    def setBarIndicator(self, checked):
        if self._barIndicator != bool(checked):
            self._barIndicator = checked
            self.repaint()

    def getBackgroundColor(self):
        return self._bg_color

    def setBackgroundColor(self, color):
        if self._show_ticks != bool(checked):
            self._show_ticks = checked
            self.repaint()

    def getIndicatorColor(self):
        return self._indicator_color

    def setIndicatorColor(self, color):
        self._indicator_color = color
        self.repaint()

    def getTickColor(self):
        return self._tick_color

    def setTickColor(self, color):
        self._tick_color = color
        self.repaint()

    def getBackgroundSizeRate(self):
        return self._bg_size_rate

    def setBackgroundSizeRate(self, rate):
        if rate >= 0 and rate <=1 and self._bg_size_rate != rate:
            self._bg_size_rate = rate
            self.repaint()

    def getTickSizeRate(self):
        return self._tick_size_rate

    def setTickSizeRate(self, rate):
        if rate >= 0 and rate <=1 and self._tick_size_rate != rate:
            self._tick_size_rate = rate
            self.repaint()

    def getNumDivisions(self):
        return self._num_divisions

    def setNumDivisions(self, divisions):
        if isinstance(divisions, int) and divisions > 0 and self._num_divisions != divisions:
            self._num_divisions = divisions
            self.repaint()
    
class PyDMScaleIndicator(QFrame, PyDMWidget):

    def __init__(self, parent=None, init_channel=None):
        QFrame.__init__(self, parent)
        PyDMWidget.__init__(self, init_channel=init_channel)
        self._show_value = True
        self._show_limits = True

        self.scale_indicator = QScale()
        self.value_label = QLabel()
        self.lower_label = QLabel()
        self.upper_label = QLabel()

        self.value_label.setText('<val>')
        self.lower_label.setText('<min>')
        self.upper_label.setText('<max>')

        self._orientation = Qt.Horizontal
        self.setup_widgets_for_orientation(self._orientation)

    def updateAll(self):
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

    def setup_widgets_for_orientation(self, new_orientation):
        self.limits_layout = None
        self.widget_layout = None
        if new_orientation == Qt.Horizontal:
            self.limits_layout = QHBoxLayout()
            self.limits_layout.addWidget(self.lower_label)
            self.limits_layout.addWidget(self.upper_label)
            self.widget_layout = QVBoxLayout()
            self.widget_layout.addWidget(self.value_label)
            self.widget_layout.addWidget(self.scale_indicator)
            self.widget_layout.addItem(self.limits_layout)
            self.value_label.setAlignment(Qt.AlignCenter)
            self.lower_label.setAlignment(Qt.AlignLeft)
            self.upper_label.setAlignment(Qt.AlignRight)

        elif new_orientation == Qt.Vertical:
            self.limits_layout = QVBoxLayout()
            self.limits_layout.addWidget(self.upper_label)
            self.limits_layout.addWidget(self.lower_label)
            self.widget_layout = QHBoxLayout()
            self.widget_layout.addWidget(self.value_label)
            self.widget_layout.addWidget(self.scale_indicator)
            self.widget_layout.addItem(self.limits_layout)
            self.value_label.setAlignment(Qt.AlignCenter)
            self.lower_label.setAlignment(Qt.AlignBottom)
            self.upper_label.setAlignment(Qt.AlignTop)
        if self.layout() is not None:
            # Trick to remove the existing layout by re-parenting it in an empty widget.
            QWidget().setLayout(self.layout())
        self.widget_layout.setContentsMargins(1, 1, 1, 1)
        self.setLayout(self.widget_layout)

    @pyqtProperty(bool)
    def showValue(self):
        return self._show_value

    @showValue.setter
    def showValue(self, checked):
        if self._show_value != bool(checked):
            self._show_value = checked
        if checked:
            self.value_label.show()
        else:
            self.value_label.hide()

    @pyqtProperty(bool)
    def showLimits(self):
        return self._show_limits

    @showLimits.setter
    def showLimits(self, checked):
        if self._show_limits != bool(checked):
            self._show_limits = checked
        if checked:
            self.lower_label.show()
            self.upper_label.show()
        else:
            self.lower_label.hide()
            self.upper_label.hide()

    def alarm_severity_changed(self, new_alarm_severity):
        PyDMWidget.alarm_severity_changed(self, new_alarm_severity)
        if self._channels is not None:
            style = compose_stylesheet(style=self._style, obj=self.value_label)
            self.value_label.setStyleSheet(style)
            self.repaint()

    @pyqtProperty(bool)
    def showTicks(self):
        return self.scale_indicator.getShowTicks()

    @showTicks.setter
    def showTicks(self, checked):
        self.scale_indicator.setShowTicks(checked)

    @pyqtProperty(Qt.Orientation)
    def orientation(self):
        return self.scale_indicator.getOrientation()

    @orientation.setter
    def orientation(self, orientation):
        self.scale_indicator.setOrientation(orientation)
        self.setup_widgets_for_orientation(orientation)

    @pyqtProperty(bool)
    def barIndicator(self):
        return self.scale_indicator.getBarIndicator()

    @barIndicator.setter
    def barIndicator(self, checked):
        self.scale_indicator.setBarIndicator(checked)

    @pyqtProperty(QColor)
    def backgroundColor(self):
        return self.scale_indicator.getBackgroundColor()

    @backgroundColor.setter
    def backgroundColor(self, color):
        self.scale_indicator.setBackgroundColor(color)

    @pyqtProperty(QColor)
    def indicatorColor(self):
        return self.scale_indicator.getIndicatorColor()

    @indicatorColor.setter
    def indicatorColor(self, color):
        self.scale_indicator.setIndicatorColor(color)

    @pyqtProperty(QColor)
    def tickColor(self):
        return self.scale_indicator.getTickColor()

    @tickColor.setter
    def tickColor(self, color):
        self.scale_indicator.setTickColor(color)

    @pyqtProperty(float)
    def backgroundSizeRate(self):
        return self.scale_indicator.getBackgroundSizeRate()

    @backgroundSizeRate.setter
    def backgroundSizeRate(self, rate):
        self.scale_indicator.setBackgroundSizeRate(rate)

    @pyqtProperty(float)
    def tickSizeRate(self):
        return self.scale_indicator.getTickSizeRate()

    @tickSizeRate.setter
    def tickSizeRate(self, rate):
        self.scale_indicator.setTickSizeRate(rate)

    @pyqtProperty(int)
    def numDivisions(self):
        return self.scale_indicator.getNumDivisions()

    @numDivisions.setter
    def numDivisions(self, divisions):
        self.scale_indicator.setNumDivisions(divisions)

