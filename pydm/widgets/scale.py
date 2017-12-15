from .base import PyDMWidget, compose_stylesheet
from ..PyQt.QtGui import QFrame, QVBoxLayout, QHBoxLayout, QPainter, QColor, QPolygon, QPen, QLabel, QSizePolicy, QWidget
from ..PyQt.QtCore import Qt, QPoint, pyqtProperty
from .channel import PyDMChannel
import sys


class QScale(QFrame):
    """
    A bar-shaped indicator for scalar value.
    Configurable features include indicator type (bar/pointer), scale tick 
    marks and orientation (horizontal/vertical).

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Scale
    """
    def __init__(self, parent=None):
        super(QScale, self).__init__(parent)
        self._value = 4
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
        self._painter_translation_y = None
        self._painter_translation_x = None
        self._painter_scale_x = None
        self._flip_traslation_y = None
        self._flip_scale_y = None
        self._orientation = None
        self._widget_width = None
        self._widget_height = None
        self._inverted_appearance = False
        self._flip_scale = False
        self.set_orientation(Qt.Horizontal)

        self.setMinimumSize(2, 2)
        self.set_position()

    def adjust_transformation(self):
        """
        This method sets parameters for the widget transformations (needed to for
        orientation, flipping and appearance inversion).

        """
        if self._orientation == Qt.Horizontal:
            self._widget_width = self.width()
            self._widget_height = self.height()
            self._painter_translation_y = 0
            self._painter_rotation = 0
        elif self._orientation == Qt.Vertical:
            # Invert dimensions for paintEvent()
            self._widget_width = self.height()
            self._widget_height = self.width()
            self._painter_translation_y = self._widget_width
            self._painter_rotation = -90
            self._painter_translation_x = None
            self._painter_scale_x = None

        if self._inverted_appearance == True:
            self._painter_translation_x = self._widget_width
            self._painter_scale_x = -1
        else:
            self._painter_translation_x = 0
            self._painter_scale_x = 1

        if self._flip_scale == True:
            self._flip_traslation_y = self._widget_height
            self._flip_scale_y = -1
        else:
            self._flip_traslation_y = 0
            self._flip_scale_y = 1

    def set_tick_pen(self):
        """
        Define pen style for drawing scale tick marks.
        """
        self._tick_pen.setColor(self._tick_color)
        self._tick_pen.setWidth(self._tick_width)

    def draw_ticks(self):
        """
        Draw tick marks on the scale.
        """
        if not self._show_ticks:
            return
        self.set_tick_pen()
        self._painter.setPen(self._tick_pen)
        division_size = self._widget_width / self._num_divisions
        tick_y0 = self._widget_height
        tick_yf = (1 - self._tick_size_rate)*self._widget_height
        for i in range(self._num_divisions+1):
            x = i*division_size
            self._painter.drawLine(x, tick_y0, x, tick_yf) # x1, y1, x2, y2

    def draw_bar(self):
        """
        Draw a bar as indicator of current value.
        """
        self.set_position()
        if self.position < 0 or self.position > self._widget_width:
            return
        self._painter.setPen(Qt.transparent)
        self._painter.setBrush(self._indicator_color)
        bar_height = self._bg_size_rate * self._widget_height
        self._painter.drawRect(0, 0, self.position, bar_height)

    def draw_pointer(self):
        """
        Draw a pointer as indicator of current value.
        """
        self.set_position()
        if self.position < 0 or self.position > self._widget_width:
            return
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

    def draw_indicator(self):
        """
        Draw the selected indicator for current value.
        """
        if self._barIndicator == True:
            self.draw_bar()
        else:
            self.draw_pointer()

    def draw_background(self):
        """
        Draw the background of the scale.
        """
        self._painter.setPen(Qt.transparent)
        self._painter.setBrush(self._bg_color)
        bg_width = self._widget_width
        bg_height = self._bg_size_rate * self._widget_height
        self._painter.drawRect(0, 0, bg_width, bg_height)

    def paintEvent(self, event):
        """
        Paint events are sent to widgets that need to update themselves,
        for instance when part of a widget is exposed because a covering
        widget was moved.

        Parameters
        ----------
        event : QPaintEvent
        """
        self.adjust_transformation()
        self._painter.begin(self)
        self._painter.translate(0, self._painter_translation_y) # Draw vertically if needed
        self._painter.rotate(self._painter_rotation)
        self._painter.translate(self._painter_translation_x, 0) # Invert appearance if needed
        self._painter.scale(self._painter_scale_x, 1)

        self._painter.translate(0, self._flip_traslation_y)     # Invert scale if needed
        self._painter.scale(1, self._flip_scale_y)

        self._painter.setRenderHint(QPainter.Antialiasing)

        self.draw_background()
        self.draw_ticks()
        self.draw_indicator()
        
        self._painter.end()

    def set_position(self):
        """
        Calculate the position (pixel) in which the pointer should be drawn.
        """
        try:
            proportion = (self._value - self._lower_limit) / (self._upper_limit - self._lower_limit)
        except:
            proportion = -1 # Invalid
        self.position = int(proportion * self._widget_width)

    def update_indicator(self):
        """
        Update the position and the drawing of indicator.
        """
        self.set_position()
        self.repaint()

    def set_value(self, value):
        """
        Set a new current value for the indicator.
        """
        self._value = value
        self.update_indicator()

    def set_upper_limit(self, new_limit):
        """
        Set the scale upper limit.

        Parameters
        ----------
        new_limit : float
            The upper limit of the scale.
        """
        self._upper_limit = new_limit

    def set_lower_limit(self, new_limit):
        """
        Set the scale lower limit.

        Parameters
        ----------
        new_limit : float
            The lower limit of the scale.
        """
        self._lower_limit = new_limit

    def get_show_ticks(self):
        return self._show_ticks

    def set_show_ticks(self, checked):
        if self._show_ticks != bool(checked):
            self._show_ticks = checked
            self.repaint()

    def get_orientation(self):
        return self._orientation

    def set_orientation(self, orientation):
        self._orientation = orientation
        self.adjust_transformation()
        self.repaint()

    def get_flip_scale(self):
        return self._flip_scale

    def set_flip_scale(self, checked):
        self._flip_scale = checked
        self.adjust_transformation()
        self.repaint()

    def get_inverted_appearance(self):
        return self._inverted_appearance

    def set_inverted_appearance(self, inverted):
        self._inverted_appearance = inverted
        self.adjust_transformation()
        self.repaint()

    def get_bar_indicator(self):
        return self._barIndicator

    def set_bar_indicator(self, checked):
        if self._barIndicator != bool(checked):
            self._barIndicator = checked
            self.repaint()

    def get_background_color(self):
        return self._bg_color

    def set_background_color(self, color):
        self._bg_color = color
        self.repaint()

    def get_indicator_color(self):
        return self._indicator_color

    def set_indicator_color(self, color):
        self._indicator_color = color
        self.repaint()

    def get_tick_color(self):
        return self._tick_color

    def set_tick_color(self, color):
        self._tick_color = color
        self.repaint()

    def get_background_size_rate(self):
        return self._bg_size_rate

    def set_background_size_rate(self, rate):
        if rate >= 0 and rate <=1 and self._bg_size_rate != rate:
            self._bg_size_rate = rate
            self.repaint()

    def get_tick_size_rate(self):
        return self._tick_size_rate

    def set_tick_size_rate(self, rate):
        if rate >= 0 and rate <=1 and self._tick_size_rate != rate:
            self._tick_size_rate = rate
            self.repaint()

    def get_num_divisions(self):
        return self._num_divisions

    def set_num_divisions(self, divisions):
        if isinstance(divisions, int) and divisions > 0 and self._num_divisions != divisions:
            self._num_divisions = divisions
            self.repaint()
    
class PyDMScaleIndicator(QFrame, PyDMWidget):
    """
    A bar-shaped indicator for scalar value with support for Channels and
    more from PyDM.
    Configurable features include indicator type (bar/pointer), scale tick 
    marks and orientation (horizontal/vertical).

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Scale
    init_channel : str, optional
        The channel to be used by the widget.
    """

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

        self.setup_widgets_for_orientation(Qt.Horizontal, False, False)

    def update_labels(self):
        """
        Update the limits and value labels with the correct values.
        """
        self.lower_label.setText(str(self.scale_indicator._lower_limit))
        self.upper_label.setText(str(self.scale_indicator._upper_limit))
        self.value_label.setText(self.format_string.format(self.scale_indicator._value))

    def value_changed(self, new_value):
        """
        Callback invoked when the Channel value is changed.

        Parameters
        ----------
        new_val : int or float
            The new value from the channel.
        """
        super(PyDMScaleIndicator, self).value_changed(new_value)
        self.scale_indicator.set_value(new_value)
        self.update_labels()

    def upperCtrlLimitChanged(self, new_limit):
        """
        PyQT Slot for changes on the upper control limit value of the Channel
        This slot sends the new limit value to the
        ```ctrl_limit_changed``` callback.

        Parameters
        ----------
        new_limit : float
        """
        super(PyDMScaleIndicator, self).upperCtrlLimitChanged(new_limit)
        self.scale_indicator.set_upper_limit(new_limit)
        self.update_labels()

    def lowerCtrlLimitChanged(self, new_limit):
        """
        PyQT Slot for changes on the lower control limit value of the Channel
        This slot sends the new limit value to the
        ```ctrl_limit_changed``` callback.

        Parameters
        ----------
        new_limit : float
        """
        super(PyDMScaleIndicator, self).lowerCtrlLimitChanged(new_limit)
        self.scale_indicator.set_lower_limit(new_limit)
        self.update_labels()

    def setup_widgets_for_orientation(self, new_orientation, flipped, inverted):
        """
        Reconstruct the widget given the orientation.

        Parameters
        ----------
        new_orientation : int
            Qt.Horizontal or Qt.Vertical
        flipped : bool
            Indicates if scale tick marks are flipped to the other side
        inverted : bool
            Indicates if scale appearance is inverted
        """
        self.limits_layout = None
        self.widget_layout = None
        if new_orientation == Qt.Horizontal:
            self.limits_layout = QHBoxLayout()
            if inverted == False:
                self.limits_layout.addWidget(self.lower_label)
                self.limits_layout.addWidget(self.upper_label)
                self.lower_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.upper_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            else:
                self.limits_layout.addWidget(self.upper_label)
                self.limits_layout.addWidget(self.lower_label)
                self.lower_label.setAlignment(Qt.AlignRight |Qt.AlignVCenter)
                self.upper_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            self.widget_layout = QVBoxLayout()
            if flipped == False:
                self.widget_layout.addWidget(self.value_label)
                self.widget_layout.addWidget(self.scale_indicator)
                self.widget_layout.addItem(self.limits_layout)
            else:
                self.widget_layout.addItem(self.limits_layout)
                self.widget_layout.addWidget(self.scale_indicator)
                self.widget_layout.addWidget(self.value_label)

        elif new_orientation == Qt.Vertical:
            self.limits_layout = QVBoxLayout()
            if inverted == False:
                self.limits_layout.addWidget(self.upper_label)
                self.limits_layout.addWidget(self.lower_label)
                self.lower_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
                self.upper_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            else:
                self.limits_layout.addWidget(self.lower_label)
                self.limits_layout.addWidget(self.upper_label)
                self.lower_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
                self.upper_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)

            self.widget_layout = QHBoxLayout()
            if flipped == False:
                self.widget_layout.addWidget(self.value_label)
                self.widget_layout.addWidget(self.scale_indicator)
                self.widget_layout.addItem(self.limits_layout)
            else:
                self.widget_layout.addItem(self.limits_layout)
                self.widget_layout.addWidget(self.scale_indicator)
                self.widget_layout.addWidget(self.value_label)
        self.value_label.setAlignment(Qt.AlignCenter)

        if self.layout() is not None:
            # Trick to remove the existing layout by re-parenting it in an empty widget.
            QWidget().setLayout(self.layout())
        self.widget_layout.setContentsMargins(1, 1, 1, 1)
        self.setLayout(self.widget_layout)

    @pyqtProperty(bool)
    def showValue(self):
        """
        Whether or not the current value should be displayed on the scale.

        Returns
        -------
        bool
        """
        return self._show_value

    @showValue.setter
    def showValue(self, checked):
        """
        Whether or not the current value should be displayed on the scale.

        Parameters
        ----------
        checked : bool
        """
        if self._show_value != bool(checked):
            self._show_value = checked
        if checked:
            self.value_label.show()
        else:
            self.value_label.hide()

    @pyqtProperty(bool)
    def showLimits(self):
        """
        Whether or not the high and low limits should be displayed on the scale.

        Returns
        -------
        bool
        """
        return self._show_limits

    @showLimits.setter
    def showLimits(self, checked):
        """
        Whether or not the high and low limits should be displayed on the scale.

        Parameters
        ----------
        checked : bool
        """
        if self._show_limits != bool(checked):
            self._show_limits = checked
        if checked:
            self.lower_label.show()
            self.upper_label.show()
        else:
            self.lower_label.hide()
            self.upper_label.hide()

    def alarm_severity_changed(self, new_alarm_severity):
        """
        Callback invoked when the Channel alarm severity is changed.
        This callback is not processed if the widget has no channel
        associated with it.
        This callback handles the composition of the stylesheet to be
        applied and the call
        to update to redraw the widget with the needed changes for the
        new state.

        Parameters
        ----------
        new_alarm_severity : int
            The new severity where 0 = NO_ALARM, 1 = MINOR, 2 = MAJOR
            and 3 = INVALID
        """
        PyDMWidget.alarm_severity_changed(self, new_alarm_severity)
        if self._channels is not None:
            style = compose_stylesheet(style=self._style, obj=self.value_label)
            self.value_label.setStyleSheet(style)
            self.repaint()

    @pyqtProperty(bool)
    def showTicks(self):
        """
        Whether or not the tick marks should be displayed on the scale.

        Returns
        -------
        bool
        """
        return self.scale_indicator.get_show_ticks()

    @showTicks.setter
    def showTicks(self, checked):
        """
        Whether or not the tick marks should be displayed on the scale.

        Parameters
        ----------
        checked : bool
        """
        self.scale_indicator.set_show_ticks(checked)

    @pyqtProperty(Qt.Orientation)
    def orientation(self):
        """
        The scale orientation (Horizontal or Vertical)

        Returns
        -------
        int
            Qt.Horizontal or Qt.Vertical
        """
        return self.scale_indicator.get_orientation()

    @orientation.setter
    def orientation(self, orientation):
        """
        The scale orientation (Horizontal or Vertical)

        Parameters
        ----------
        new_orientation : int
            Qt.Horizontal or Qt.Vertical
        """
        self.scale_indicator.set_orientation(orientation)
        self.setup_widgets_for_orientation(orientation, self.flipScale, self.invertedAppearance)

    @pyqtProperty(bool)
    def flipScale(self):
        """
        Whether or not the scale should be flipped.

        Returns
        -------
        bool
        """
        return self.scale_indicator.get_flip_scale()

    @flipScale.setter
    def flipScale(self, checked):
        """
        Whether or not the scale should be flipped.

        Parameters
        ----------
        checked : bool
        """
        self.scale_indicator.set_flip_scale(checked)
        self.setup_widgets_for_orientation(self.orientation, checked, self.invertedAppearance)

    @pyqtProperty(bool)
    def invertedAppearance(self):
        """
        Whether or not the scale appearence should be inverted.

        Returns
        -------
        bool
        """
        return self.scale_indicator.get_inverted_appearance()

    @invertedAppearance.setter
    def invertedAppearance(self, inverted):
        """
        Whether or not the scale appearence should be inverted.

        Parameters
        ----------
        inverted : bool
        """
        self.scale_indicator.set_inverted_appearance(inverted)
        self.setup_widgets_for_orientation(self.orientation, self.flipScale, inverted)

    @pyqtProperty(bool)
    def barIndicator(self):
        """
        Whether or not the scale indicator should be a bar instead of a pointer.

        Returns
        -------
        bool
        """
        return self.scale_indicator.get_bar_indicator()

    @barIndicator.setter
    def barIndicator(self, checked):
        """
        Whether or not the scale indicator should be a bar instead of a pointer.

        Parameters
        ----------
        checked : bool
        """
        self.scale_indicator.set_bar_indicator(checked)

    @pyqtProperty(QColor)
    def backgroundColor(self):
        """
        The color of the scale background.

        Returns
        -------
        QColor
        """
        return self.scale_indicator.get_background_color()

    @backgroundColor.setter
    def backgroundColor(self, color):
        """
        The color of the scale background.

        Parameters
        -------
        color : QColor
        """
        self.scale_indicator.set_background_color(color)

    @pyqtProperty(QColor)
    def indicatorColor(self):
        """
        The color of the scale indicator.

        Returns
        -------
        QColor
        """
        return self.scale_indicator.get_indicator_color()

    @indicatorColor.setter
    def indicatorColor(self, color):
        """
        The color of the scale indicator.

        Parameters
        -------
        color : QColor
        """
        self.scale_indicator.set_indicator_color(color)

    @pyqtProperty(QColor)
    def tickColor(self):
        """
        The color of the scale tick marks.

        Returns
        -------
        QColor
        """
        return self.scale_indicator.get_tick_color()

    @tickColor.setter
    def tickColor(self, color):
        """
        The color of the scale tick marks.

        Parameters
        -------
        color : QColor
        """
        self.scale_indicator.set_tick_color(color)

    @pyqtProperty(float)
    def backgroundSizeRate(self):
        """
        The rate of background height size (from top to bottom).

        Returns
        -------
        float
        """
        return self.scale_indicator.get_background_size_rate()

    @backgroundSizeRate.setter
    def backgroundSizeRate(self, rate):
        """
        The rate of background height size (from top to bottom).

        Parameters
        -------
        rate : float
            Between 0 and 1.
        """
        self.scale_indicator.set_background_size_rate(rate)

    @pyqtProperty(float)
    def tickSizeRate(self):
        """
        The rate of tick marks height size (from bottom to top).

        Returns
        -------
        float
        """
        return self.scale_indicator.get_tick_size_rate()

    @tickSizeRate.setter
    def tickSizeRate(self, rate):
        """
        The rate of tick marks height size (from bottom to top).

        Returns
        -------
        rate : float
            Between 0 and 1.
        """
        self.scale_indicator.set_tick_size_rate(rate)

    @pyqtProperty(int)
    def numDivisions(self):
        """
        The number in which the scale is divided.

        Returns
        -------
        int
        """
        return self.scale_indicator.get_num_divisions()

    @numDivisions.setter
    def numDivisions(self, divisions):
        """
        The number in which the scale is divided.

        Returns
        -------
        divisions : int
            The number of scale divisions.
        """
        self.scale_indicator.set_num_divisions(divisions)

