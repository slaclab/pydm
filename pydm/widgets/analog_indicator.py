from PyQt5.QtCore import QPointF

from .base import PyDMWidget, TextFormatter
from qtpy.QtGui import QColor, QPolygon, QPen, QPainter
from qtpy.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QWidget, QGridLayout
from qtpy.QtCore import Qt, QPoint, Property
from qtpy.QtWidgets import QWIDGETSIZE_MAX
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
        self._value = 1
        self._lower_limit = -5
        self._upper_limit = 5
        self._lower_minor_alarm = -5
        self._upper_minor_alarm = 5
        self._lower_major_alarm = -5
        self._upper_major_alarm = 5
        self.position = None  # unit: pixel

        self._bg_color = QColor('lightblue')
        self._minor_alarm_region_color = QColor('white')
        self._minor_alarm_color = QColor('yellow')
        self._major_alarm_region_color = QColor('grey')
        self._major_alarm_color = QColor('red')
        self._bg_size_rate = 0.5    # from 0 to 1

        self._indicator_color = QColor('black')
        self._pointer_width_rate = 0.05
        self._barIndicator = False

        self._num_divisions = 10
        self._show_ticks = False
        self._tick_pen = QPen()
        self._tick_color = QColor('black')
        self._tick_width = 0
        self._tick_size_rate = 0.1  # from 0 to 1
        self._painter = QPainter()

        self._painter_rotation = None
        self._painter_translation_y = None
        self._painter_translation_x = None
        self._painter_scale_x = None
        self._flip_traslation_y = None
        self._flip_scale_y = None

        self._widget_width = self.width()
        self._widget_height = self.height()

        self._orientation = Qt.Horizontal
        self._inverted_appearance = False
        self._flip_scale = False
        self._scale_height = 40
        self._origin_at_zero = False
        self._origin_position = 0

        self.set_position()

    def adjust_transformation(self):
        """
        This method sets parameters for the widget transformations (needed to for
        orientation, flipping and appearance inversion).
        """
        self.setMaximumSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)  # Unset fixed size
        if self._orientation == Qt.Horizontal:
            self._widget_width = self.width()
            self._widget_height = self.height()
            self._painter_translation_y = 0
            self._painter_rotation = 0
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.setFixedHeight(self._scale_height)
        elif self._orientation == Qt.Vertical:
            # Invert dimensions for paintEvent()
            self._widget_width = self.height()
            self._widget_height = self.width()
            self._painter_translation_y = self._widget_width
            self._painter_rotation = -90
            self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
            self.setFixedWidth(self._scale_height)

        if self._inverted_appearance:
            self._painter_translation_x = self._widget_width
            self._painter_scale_x = -1
        else:
            self._painter_translation_x = 0
            self._painter_scale_x = 1

        if self._flip_scale:
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
        #tick_y0 = self._widget_height
        tick_y0 = self._scale_height * self._bg_size_rate
        tick_yf = tick_y0 + self._scale_height * self._tick_size_rate * .25
        for i in range(self._num_divisions+1):
            x = i*division_size
            self._painter.drawLine(x, tick_y0, x, tick_yf) # x1, y1, x2, y2

    def draw_set_point(self):
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
            QPoint(self.position, 15),
            QPoint(self.position + 0.5*pointer_width, 0.5*pointer_height+15),
            QPoint(self.position, pointer_height),
            QPoint(self.position - 0.5*pointer_width, 0.5*pointer_height+15)
        ]
        self._painter.drawPolygon(QPolygon(points))

    def draw_indicator(self):
        """
        Draw the selected indicator for current value.
        """
        self.set_position()
        if self.position < 0 or self.position > self._widget_width:
            return
        self._painter.setPen(Qt.transparent)
        self._painter.setBrush(self._indicator_color)
        pointer_width = self._pointer_width_rate * self._widget_width
        pointer_height = self._bg_size_rate * self._scale_height * 1.5
        points = [
            QPoint(self.position + 0.5 * pointer_width, 0),
            QPoint(self.position - 0.5 * pointer_width, 0),
            QPoint(self.position, pointer_height)
        ]
        self._painter.drawPolygon(QPolygon(points))

    def draw_background(self):
        """
        Draw the background of the scale.
        """
        self._painter.setPen(Qt.black)
        self._painter.setBrush(self._bg_color)
        pointer_height = self._bg_size_rate * self._scale_height
        bg_width = self._widget_width
        bg_height = self._bg_size_rate * self._widget_height - 2
        #bg_height = self._scale_height - 5
        self._painter.drawRect(0, pointer_height, bg_width, bg_height)

    def draw_minor_alarm_region(self):
        """
        Draw the minor alarm areas on the scale
        """

        self._painter.setPen(Qt.black)
        self._painter.setBrush(self._minor_alarm_region_color)
        lower_minor_alarm_width = self.calculate_position_for_value(self._lower_minor_alarm)

        upper_minor_alarm_start = self.calculate_position_for_value(self._upper_minor_alarm)
        upper_minor_alarm_width = self._widget_width - upper_minor_alarm_start
        pointer_height = self._bg_size_rate * self._scale_height
        minor_alarm_height = self._bg_size_rate * self._widget_height - 2
        #minor_alarm_height = self._scale_height - 5


        """
        sets the pen color to alarm if the value is in the lower minor alarm region
        """
        if self._value < self._lower_minor_alarm and self._value > self._lower_major_alarm:
            self._painter.setBrush(self._minor_alarm_color)
        else:
            self._painter.setBrush(self._minor_alarm_region_color)

        self._painter.drawRect(0, pointer_height, lower_minor_alarm_width, minor_alarm_height)
        """
        sets the pen color to alarm if the value is in the upper minor alarm region
        """
        if self._value > self._upper_minor_alarm and self._value < self._upper_major_alarm:
            self._painter.setBrush(self._minor_alarm_color)
        else:
            self._painter.setBrush(self._minor_alarm_region_color)

        self._painter.drawRect(upper_minor_alarm_start, pointer_height, upper_minor_alarm_width, minor_alarm_height)

    def draw_major_alarm_region(self):
        """
        Draw the minor alarm areas on the scale
        """

        self._painter.setPen(Qt.black)
        self._painter.setBrush(self._major_alarm_region_color)
        lower_major_alarm_width = self.calculate_position_for_value(self._lower_major_alarm)

        upper_major_alarm_start = self.calculate_position_for_value(self._upper_major_alarm)
        upper_major_alarm_width = self._widget_width - upper_major_alarm_start
        pointer_height = self._bg_size_rate * self._scale_height

        major_alarm_height = self._bg_size_rate * self._widget_height -2
        #major_alarm_height = self._scale_height - 5


        """
        sets the pen color to alarm if the value is in the lower major alarm region
        """
        if self._value < self._lower_major_alarm:
            self._painter.setBrush(self._major_alarm_color)
        else:
            self._painter.setBrush(self._major_alarm_region_color)


        self._painter.drawRect(0, pointer_height, lower_major_alarm_width, major_alarm_height)

        """
        sets the pen color to alarm if the value is in the upper major alarm region
        """
        if self._value > self._upper_major_alarm:
            self._painter.setBrush(self._major_alarm_color)
        else:
            self._painter.setBrush(self._major_alarm_region_color)

        self._painter.drawRect(upper_major_alarm_start, pointer_height, upper_major_alarm_width, major_alarm_height)

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

        """
        self.draw_indicator() -> draws a triangle outside of the scale, used as the value indicator
        self.draw_background() -> draws the background of the scale
        self.draw_major() -> draws the major alarm area
        self.draw_minor() -> draws the minor alarm area
        self.draw_ticks() -> draws scale ticks
        self.draw_set_point -> draws diamond in the middle of the scale. can use current self.draw_indicator() for this
        """
        self.draw_background()
        self.draw_minor_alarm_region()
        self.draw_major_alarm_region()
        self.draw_ticks()
        self.draw_indicator()
        #self.draw_set_point()

        self._painter.end()

    def calculate_position_for_value(self, value):
        """
        Calculate the position (pixel) in which the pointer should be drawn for a given value.
        """
        if value is None or value < self._lower_limit or value > self._upper_limit or \
           self._upper_limit - self._lower_limit == 0:
            proportion = -1 # Invalid
        else:
            proportion = (value - self._lower_limit) / (self._upper_limit - self._lower_limit)

        position = int(proportion * self._widget_width)
        return position

    def set_origin(self):
        """
        Set the position (pixel) in which the origin should be drawn.
        """
        if self._origin_at_zero:
            self._origin_position = self.calculate_position_for_value(0)
        else:
            self._origin_position = 0

    def set_position(self):
        """
        Set the position (pixel) in which the pointer should be drawn.
        """
        self.position = self.calculate_position_for_value(self._value)

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

    def set_upper_minor_alarm(self, new_minor_alarm):
        """
        Set the scale upper minor alarm.

        Parameters
        ----------
        new_minor_alarm : float
            The upper minor alarm of the scale.
        """
        self._upper_minor_alarm = new_minor_alarm

    def set_lower_minor_alarm(self, new_minor_alarm):
        """
        Set the scale lower minor alarm.

        Parameters
        ----------
        new_minor_alarm : float
            The lower minor alarm of the scale.
        """
        self._lower_minor_alarm = new_minor_alarm

    def set_upper_major_alarm(self, new_major_alarm):
        """
        Set the scale upper major alarm.

        Parameters
        ----------
        new_major_alarm : float
            The upper major alarm of the scale.
        """
        self._upper_major_alarm = new_major_alarm

    def set_lower_major_alarm(self, new_major_alarm):
        """
        Set the scale lower major alarm.

        Parameters
        ----------
        new_major_alarm : float
            The lower major alarm of the scale.
        """
        self._lower_major_alarm = new_major_alarm

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
        self._flip_scale = bool(checked)
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

    def get_minor_alarm_region_color(self):
        return self._minor_alarm_region_color

    def set_minor_alarm_region_color(self, color):
        self._minor_alarm_region_color = color
        self.repaint()

    def get_minor_alarm_color(self):
        return self._minor_alarm_color

    def set_minor_alarm_color(self, color):
        self._minor_alarm_color = color
        self.repaint()

    def get_major_alarm_region_color(self):
        return self._major_alarm_region_color

    def set_major_alarm_region_color(self, color):
        self._major_alarm_region_color = color
        self.repaint()

    def get_major_alarm_color(self):
        return self._major_alarm_color

    def set_major_alarm_color(self, color):
        self._major_alarm_color = color
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

    def get_scale_height(self):
        return self._scale_height

    def set_scale_height(self, value):
        self._scale_height = int(value)
        self.adjust_transformation()
        self.repaint()

    def get_origin_at_zero(self):
        return self._origin_at_zero

    def set_origin_at_zero(self, checked):
        if self._origin_at_zero != bool(checked):
            self._origin_at_zero = checked
            self.repaint()


class PyDMAnalogIndicator(QFrame, TextFormatter, PyDMWidget):
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

        self._value_position = Qt.TopEdge
        self._limits_from_channel = True
        self._minor_alarm_from_channel = True
        self._major_alarm_from_channel = True
        self._user_lower_limit = 0
        self._user_upper_limit = 0
        self._user_lower_minor_alarm = 0
        self._user_upper_minor_alarm = 0
        self._user_lower_major_alarm = 0
        self._user_upper_major_alarm = 0

        self.value_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setup_widgets_for_orientation(Qt.Horizontal, False, False, self._value_position)


    def update_labels(self):
        """
        Update the limits and value labels with the correct values.
        """
        self.lower_label.setText(str(self.scale_indicator._lower_limit))
        self.upper_label.setText(str(self.scale_indicator._upper_limit))
        self.value_label.setText(self.format_string.format(self.scale_indicator._value))

    def lower_warning_limit_changed(self, new_minor_alarm):
        """
        Updates the minor and major alarm boundaries
        """
        super(PyDMAnalogIndicator, self).lower_warning_limit_changed(new_minor_alarm)
        if self.minorAlarmFromChannel:
            self.scale_indicator.set_lower_minor_alarm(new_minor_alarm)
            self.update_labels()

    def upper_warning_limit_changed(self, new_minor_alarm):
        """
        Updates the minor and major alarm boundaries
        """
        super(PyDMAnalogIndicator, self).upper_warning_limit_changed(new_minor_alarm)
        if self.minorAlarmFromChannel:
            self.scale_indicator.set_upper_minor_alarm(new_minor_alarm)
            self.update_labels()

    def lower_alarm_limit_changed(self, new_major_alarm):
        """
        Updates the minor and major alarm boundaries
        """
        super(PyDMAnalogIndicator, self).lower_alarm_limit_changed(new_major_alarm)
        if self.majorAlarmFromChannel:
            self.scale_indicator.set_lower_major_alarm(new_major_alarm)
            self.update_labels()

    def upper_alarm_limit_changed(self, new_major_alarm):
        """
        Updates the minor and major alarm boundaries
        """
        super(PyDMAnalogIndicator, self).upper_alarm_limit_changed(new_major_alarm)
        if self.majorAlarmFromChannel:
            self.scale_indicator.set_upper_major_alarm(new_major_alarm)
            self.update_labels()

    def value_changed(self, new_value):
        """
        Callback invoked when the Channel value is changed.

        Parameters
        ----------
        new_val : int or float
            The new value from the channel.
        """
        super(PyDMAnalogIndicator, self).value_changed(new_value)
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
        super(PyDMAnalogIndicator, self).upperCtrlLimitChanged(new_limit)
        if self.limitsFromChannel:
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
        super(PyDMAnalogIndicator, self).lowerCtrlLimitChanged(new_limit)
        if self.limitsFromChannel:
            self.scale_indicator.set_lower_limit(new_limit)
            self.update_labels()

    def setup_widgets_for_orientation(self, new_orientation, flipped, inverted,
                                      value_position):
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
            if not inverted:
                self.limits_layout.addWidget(self.lower_label)
                self.limits_layout.addWidget(self.upper_label)
            else:
                self.limits_layout.addWidget(self.upper_label)
                self.limits_layout.addWidget(self.lower_label)

            self.widget_layout = QGridLayout()
            if not flipped:
                if value_position == Qt.LeftEdge:
                    self.widget_layout.addWidget(self.value_label, 0, 0)
                    self.widget_layout.addWidget(self.scale_indicator, 0, 1)
                    self.widget_layout.addItem(self.limits_layout, 1, 1)
                elif value_position == Qt.RightEdge:
                    self.widget_layout.addWidget(self.value_label, 0, 1)
                    self.widget_layout.addWidget(self.scale_indicator, 0, 0)
                    self.widget_layout.addItem(self.limits_layout, 1, 0)
                elif value_position == Qt.TopEdge:
                    self.widget_layout.addWidget(self.value_label, 0, 0)
                    self.widget_layout.addWidget(self.scale_indicator, 1, 0)
                    self.widget_layout.addItem(self.limits_layout, 2, 0)
                elif value_position == Qt.BottomEdge:
                    self.widget_layout.addWidget(self.scale_indicator, 0, 0)
                    self.widget_layout.addItem(self.limits_layout, 1, 0)
                    self.widget_layout.addWidget(self.value_label, 2, 0)

                if not inverted:
                    self.lower_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
                    self.upper_label.setAlignment(Qt.AlignTop | Qt.AlignRight)
                elif inverted:
                    self.lower_label.setAlignment(Qt.AlignTop | Qt.AlignRight)
                    self.upper_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            else:
                if value_position == Qt.LeftEdge:
                    self.widget_layout.addItem(self.limits_layout, 0, 1)
                    self.widget_layout.addWidget(self.scale_indicator, 1, 1)
                    self.widget_layout.addWidget(self.value_label, 1, 0)
                elif value_position == Qt.RightEdge:
                    self.widget_layout.addItem(self.limits_layout, 0, 0)
                    self.widget_layout.addWidget(self.scale_indicator, 1, 0)
                    self.widget_layout.addWidget(self.value_label, 1, 1)
                elif value_position == Qt.TopEdge:
                    self.widget_layout.addWidget(self.value_label, 0, 0)
                    self.widget_layout.addItem(self.limits_layout, 1, 0)
                    self.widget_layout.addWidget(self.scale_indicator, 2, 0)
                elif value_position == Qt.BottomEdge:
                    self.widget_layout.addItem(self.limits_layout, 0, 0)
                    self.widget_layout.addWidget(self.scale_indicator, 1, 0)
                    self.widget_layout.addWidget(self.value_label, 2, 0)

                if not inverted:
                    self.lower_label.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
                    self.upper_label.setAlignment(Qt.AlignBottom | Qt.AlignRight)
                elif inverted:
                    self.lower_label.setAlignment(Qt.AlignBottom | Qt.AlignRight)
                    self.upper_label.setAlignment(Qt.AlignBottom | Qt.AlignLeft)

        elif new_orientation == Qt.Vertical:
            self.limits_layout = QVBoxLayout()
            if (value_position == Qt.RightEdge and flipped == False) or \
                   (value_position == Qt.LeftEdge and flipped == True):
                add_value_between_limits = True
            else:
                add_value_between_limits = False
            if not inverted:
                self.limits_layout.addWidget(self.upper_label)
                if add_value_between_limits:
                    self.limits_layout.addWidget(self.value_label)
                self.limits_layout.addWidget(self.lower_label)
                self.lower_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
                self.upper_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            else:
                self.limits_layout.addWidget(self.lower_label)
                if add_value_between_limits:
                    self.limits_layout.addWidget(self.value_label)
                self.limits_layout.addWidget(self.upper_label)
                self.lower_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
                self.upper_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)

            self.widget_layout = QGridLayout()
            if not flipped:
                if value_position == Qt.LeftEdge:
                    self.widget_layout.addWidget(self.value_label, 0, 0)
                    self.widget_layout.addWidget(self.scale_indicator, 0, 1)
                    self.widget_layout.addItem(self.limits_layout, 0, 2)
                elif value_position == Qt.RightEdge:
                    self.widget_layout.addWidget(self.scale_indicator, 0, 0)
                    self.widget_layout.addItem(self.limits_layout, 0, 1)
                elif value_position == Qt.TopEdge:
                    self.widget_layout.addWidget(self.value_label, 0, 0, 1, 2)
                    self.widget_layout.addWidget(self.scale_indicator, 1, 0)
                    self.widget_layout.addItem(self.limits_layout, 1, 1)
                elif value_position == Qt.BottomEdge:
                    self.widget_layout.addWidget(self.scale_indicator, 0, 0)
                    self.widget_layout.addItem(self.limits_layout, 0, 1)
                    self.widget_layout.addWidget(self.value_label, 1, 0, 1, 2)

                if not inverted:
                    self.lower_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
                    self.upper_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                elif inverted:
                    self.lower_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                    self.upper_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
            else:
                if value_position == Qt.LeftEdge:
                    self.widget_layout.addItem(self.limits_layout, 0, 1)
                    self.widget_layout.addWidget(self.scale_indicator, 0, 2)
                elif value_position == Qt.RightEdge:
                    self.widget_layout.addItem(self.limits_layout, 0, 0)
                    self.widget_layout.addWidget(self.scale_indicator, 0, 1)
                    self.widget_layout.addWidget(self.value_label, 0, 2)
                elif value_position == Qt.TopEdge:
                    self.widget_layout.addWidget(self.value_label, 0, 0, 1, 2)
                    self.widget_layout.addItem(self.limits_layout, 1, 0)
                    self.widget_layout.addWidget(self.scale_indicator, 1, 1)
                elif value_position == Qt.BottomEdge:
                    self.widget_layout.addItem(self.limits_layout, 0, 0)
                    self.widget_layout.addWidget(self.scale_indicator, 0, 1)
                    self.widget_layout.addWidget(self.value_label, 1, 0, 1, 2)

                if not inverted:
                    self.lower_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
                    self.upper_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
                elif inverted:
                    self.lower_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
                    self.upper_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        self.value_label.setAlignment(Qt.AlignCenter)

        if self.layout() is not None:
            # Trick to remove the existing layout by re-parenting it in an empty widget.
            QWidget().setLayout(self.layout())
        self.widget_layout.setContentsMargins(1, 1, 1, 1)
        self.setLayout(self.widget_layout)

    @Property(bool)
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

    @Property(bool)
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

    @Property(bool)
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

    @Property(Qt.Orientation)
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
        self.setup_widgets_for_orientation(orientation, self.flipScale, self.invertedAppearance, self._value_position)

    @Property(bool)
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
        self.setup_widgets_for_orientation(self.orientation, checked, self.invertedAppearance, self._value_position)

    @Property(bool)
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
        self.setup_widgets_for_orientation(self.orientation, self.flipScale, inverted, self._value_position)

    @Property(bool)
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

    @Property(QColor)
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

    @Property(QColor)
    def minorAlarmRegionColor(self):
        """
        The color of the scale background.

        Returns
        -------
        QColor
        """
        return self.scale_indicator.get_minor_alarm_region_color()

    @minorAlarmRegionColor.setter
    def minorAlarmRegionColor(self, color):
        """
        The color of the scale background.

        Parameters
        -------
        color : QColor
        """
        self.scale_indicator.set_minor_alarm_region_color(color)

    @Property(QColor)
    def minorAlarmColor(self):
        """
        The color of the scale background.

        Returns
        -------
        QColor
        """
        return self.scale_indicator.get_minor_alarm_color()

    @minorAlarmColor.setter
    def minorAlarmColor(self, color):
        """
        The color of the scale background.

        Parameters
        -------
        color : QColor
        """
        self.scale_indicator.set_minor_alarm_color(color)

    @Property(QColor)
    def majorAlarmRegionColor(self):
        """
        The color of the scale background.

        Returns
        -------
        QColor
        """
        return self.scale_indicator.get_major_alarm_region_color()

    @majorAlarmRegionColor.setter
    def majorAlarmRegionColor(self, color):
        """
        The color of the scale background.

        Parameters
        -------
        color : QColor
        """
        self.scale_indicator.set_major_alarm_region_color(color)

    @Property(QColor)
    def majorAlarmColor(self):
        """
        The color of the scale background.

        Returns
        -------
        QColor
        """
        return self.scale_indicator.get_major_alarm_color()

    @majorAlarmColor.setter
    def majorAlarmColor(self, color):
        """
        The color of the scale background.

        Parameters
        -------
        color : QColor
        """
        self.scale_indicator.set_major_alarm_color(color)

    @Property(QColor)
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

    @Property(QColor)
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

    @Property(float)
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

    @Property(float)
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

        Parameters
        -------
        rate : float
            Between 0 and 1.
        """
        self.scale_indicator.set_tick_size_rate(rate)

    @Property(int)
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

        Parameters
        -------
        divisions : int
            The number of scale divisions.
        """
        self.scale_indicator.set_num_divisions(divisions)

    @Property(int)
    def scaleHeight(self):
        """
        The scale height, fixed so it do not wiggle when value label resizes.

        Returns
        -------
        int
        """
        return self.scale_indicator.get_scale_height()

    @scaleHeight.setter
    def scaleHeight(self, value):
        """
        The scale height, fixed so it do not wiggle when value label resizes.

        Parameters
        -------
        divisions : int
            The scale height.
        """
        self.scale_indicator.set_scale_height(value)

    @Property(Qt.Edge)
    def valuePosition(self):
        """
        The position of the value label (Top, Bottom, Left or Right).

        Returns
        -------
        int
            Qt.TopEdge, Qt.BottomEdge, Qt.LeftEdge or Qt.RightEdge
        """
        return self._value_position

    @valuePosition.setter
    def valuePosition(self, position):
        """
       The position of the value label (Top, Bottom, Left or Right).

        Parameters
        ----------
        position : int
            Qt.TopEdge, Qt.BottomEdge, Qt.LeftEdge or Qt.RightEdge
        """
        self._value_position = position
        self.setup_widgets_for_orientation(self.orientation, self.flipScale, self.invertedAppearance, position)

    @Property(bool)
    def originAtZero(self):
        """
        Whether or not the scale indicator should start at zero value.
        Applies only for bar indicator.

        Returns
        -------
        bool
        """
        return self.scale_indicator.get_origin_at_zero()

    @originAtZero.setter
    def originAtZero(self, checked):
        """
        Whether or not the scale indicator should start at zero value.
        Applies only for bar indicator.

        Parameters
        ----------
        checked : bool
        """
        self.scale_indicator.set_origin_at_zero(checked)

    @Property(bool)
    def limitsFromChannel(self):
        """
        Whether or not the scale indicator should use the limits information
        from the channel.

        Returns
        -------
        bool
        """
        return self._limits_from_channel

    @limitsFromChannel.setter
    def limitsFromChannel(self, checked):
        """
        Whether or not the scale indicator should use the limits information
        from the channel.

        Parameters
        ----------
        checked : bool
            True to use the limits from the Channel, False to use the user-defined
            values.
        """
        print("_limits_from_channel")
        print(self._limits_from_channel)
        print("checked outside of if (limits)")
        print(checked)
        print("_lower_ctrl_limit")
        print(self._lower_ctrl_limit)
        if self._limits_from_channel != checked:
            print("inside limists if")
            self._limits_from_channel = checked
            if checked:
                if self._lower_ctrl_limit:
                    self.scale_indicator.set_lower_limit(self._lower_ctrl_limit)
                if self._upper_ctrl_limit:
                    self.scale_indicator.set_upper_limit(self._upper_ctrl_limit)
            else:
                self.scale_indicator.set_lower_limit(self._user_lower_limit)
                self.scale_indicator.set_upper_limit(self._user_upper_limit)
            self.update_labels()



    @Property(float)
    def userUpperLimit(self):
        """
        The user-defined upper limit for the scale.

        Returns
        -------
        float
        """
        return self._user_upper_limit

    @userUpperLimit.setter
    def userUpperLimit(self, value):
        """
        The user-defined upper limit for the scale.

        Parameters
        ----------
        value : float
            The new upper limit value.
        """
        if self._limits_from_channel:
            return
        self._user_upper_limit = value
        self.scale_indicator.set_upper_limit(self._user_upper_limit)
        self.update_labels()

    @Property(float)
    def userLowerLimit(self):
        """
        The user-defined lower limit for the scale.

        Returns
        -------
        float
        """
        return self._user_lower_limit

    @userLowerLimit.setter
    def userLowerLimit(self, value):
        """
        The user-defined lower limit for the scale.

        Parameters
        ----------
        value : float
            The new lower limit value.
        """
        if self._limits_from_channel:
            return
        self._user_lower_limit = value
        self.scale_indicator.set_lower_limit(self._user_lower_limit)
        self.update_labels()

    @Property(bool)
    def minorAlarmFromChannel(self):
        """
        Whether or not the scale indicator should use the minor alarm information
        from the channel.

        Returns
        -------
        bool
        """
        return self._minor_alarm_from_channel


    @minorAlarmFromChannel.setter
    def minorAlarmFromChannel(self, checked):
        """
        Whether or not the scale indicator should use the minor alarm information
        from the channel.

        Parameters
        ----------
        checked : bool
            True to use the minor alarm from the Channel, False to use the user-defined
            values.
        """
        if self._minor_alarm_from_channel != checked:
            self._minor_alarm_from_channel = checked
            if checked:
                if self.lower_warning_limit:
                    self.scale_indicator.set_lower_minor_alarm(self.lower_warning_limit)
                if self.upper_warning_limit:
                    self.scale_indicator.set_upper_minor_alarm(self.upper_warning_limit)
            else:
                self.scale_indicator.set_lower_minor_alarm(self._user_lower_minor_alarm)
                self.scale_indicator.set_upper_minor_alarm(self._user_upper_minor_alarm)
            self.update_labels()



    @Property(float)
    def userUpperMinorAlarm(self):
        """
        The user-defined upper minor alarm for the scale.

        Returns
        -------
        float
        """
        return self._user_upper_minor_alarm

    @userUpperMinorAlarm.setter
    def userUpperMinorAlarm(self, value):
        """
        The user-defined upper minor alarm for the scale.

        Parameters
        ----------
        value : float
            The new lower minor alarm value.
        """

        if self._minor_alarm_from_channel:
            return

        self._user_upper_minor_alarm = value
        self.scale_indicator.set_upper_minor_alarm(self._user_upper_minor_alarm)
        self.update_labels()
    @Property(float)
    def userLowerMinorAlarm(self):
        """
        The user-defined lower minor alarm for the scale.

        Returns
        -------
        float
        """
        return self._user_lower_minor_alarm

    @userLowerMinorAlarm.setter
    def userLowerMinorAlarm(self, value):
        """
        The user-defined lower minor alarm for the scale.

        Parameters
        ----------
        value : float
            The new lower minor alarm value.
        """

        if self._minor_alarm_from_channel:
            return

        self._user_lower_minor_alarm = value
        self.scale_indicator.set_lower_minor_alarm(self._user_lower_minor_alarm)
        self.update_labels()

    @Property(bool)
    def majorAlarmFromChannel(self):
        """
        Whether or not the scale indicator should use the major alarm information
        from the channel.

        Returns
        -------
        bool
        """
        return self._major_alarm_from_channel

    @majorAlarmFromChannel.setter
    def majorAlarmFromChannel(self, checked):
        """
        Whether or not the scale indicator should use the minor alarm information
        from the channel.

        Parameters
        ----------
        checked : bool
            True to use the major alarms from the Channel, False to use the user-defined
            values.
        """
        print("_major_alarm_from_channel")
        print(self._major_alarm_from_channel)
        print("checked outside of if")
        print(checked)
        if self._major_alarm_from_channel != checked:
            self._major_alarm_from_channel = checked
            print("checked inside of if")
            print(checked)

            if checked:
                print("new limit")
                if self.lower_alarm_limit:
                    self.scale_indicator.set_lower_major_alarm(self.lower_alarm_limit)
                if self.upper_alarm_limit:
                    self.scale_indicator.set_upper_major_alarm(self.upper_alarm_limit)
            else:
                print("major alarm from user")
                self.scale_indicator.set_lower_major_alarm(self._user_lower_major_alarm)
                self.scale_indicator.set_upper_major_alarm(self._user_upper_major_alarm)

            self.scale_indicator.set_lower_major_alarm(self.lower_alarm_limit)
            self.scale_indicator.set_upper_major_alarm(self.upper_alarm_limit)
            print(self.upper_alarm_limit)
            self.update_labels()




    @Property(float)
    def userUpperMajorAlarm(self):
        """
        The user-defined upper major alarm for the scale.

        Returns
        -------
        float
        """
        return self._user_upper_major_alarm

    @userUpperMajorAlarm.setter
    def userUpperMajorAlarm(self, value):
        """
        The user-defined upper major alarm for the scale.

        Parameters
        ----------
        value : float
            The new lower major alarm value.
        """

        if self._major_alarm_from_channel:
            return

        self._user_upper_major_alarm = value
        self.scale_indicator.set_upper_major_alarm(self._user_upper_major_alarm)
        #self.update_labels()

    @Property(float)
    def userLowerMajorAlarm(self):
        """
        The user-defined lower major alarm for the scale.

        Returns
        -------
        float
        """
        return self._user_lower_major_alarm

    @userLowerMajorAlarm.setter
    def userLowerMajorAlarm(self, value):
        """
        The user-defined lower major alarm for the scale.

        Parameters
        ----------
        value : float
            The new lower major alarm value.
        """

        if self._major_alarm_from_channel:
            return

        self._user_lower_major_alarm = value
        self.scale_indicator.set_lower_major_alarm(self._user_lower_major_alarm)
        #self.update_labels()