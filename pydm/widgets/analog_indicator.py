from .base import PyDMWidget
from qtpy.QtGui import QColor, QPolygon, QPainter, QFontMetrics
from qtpy.QtWidgets import QFrame, QSizePolicy
from qtpy.QtCore import Qt, QPoint, Property, QSize
from .scale import QScale, PyDMScaleIndicator


class QScaleAlarmed(QScale):
    """
    Adds alarm regions and features for QScale.
    Additional configurable features include indicator type (bar/pointer),
    scale tick marks and orientation (horizontal/vertical).
    Parameters
    ----------
    parent : QWidget
        The parent widget for the PyDMAnalogIndicator
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lower_minor_alarm = 0
        self._upper_minor_alarm = 0
        self._lower_major_alarm = 0
        self._upper_major_alarm = 0

        """
        self._cannot_draw_*_flag variables are used so draw errors only printout once.
        False = last time the paint event was called the element was able to draw
        True = last time the paint event was called the element was not able to draw because of an error
        """
        self._cannot_draw_background_flag = False
        self._cannot_draw_major_alarm_region_flag = False
        self._cannot_draw_minor_alarm_region_flag = False
        self._cannot_draw_ticks_flag = False
        self._cannot_draw_indicator_flag = False

        self._bg_color = QColor("lightblue")
        self._minor_alarm_region_color = QColor("white")
        self._minor_alarm_color = QColor("yellow")
        self._major_alarm_region_color = QColor("grey")
        self._major_alarm_color = QColor("red")
        self._bg_size_rate = 0.5  # from 0 to 1
        self._scale_height = 40

        self._show_ticks = False

        self.set_position()

    def adjust_transformation(self):
        """
        This method sets parameters for the widget transformations
        (needed to for orientation, flipping and appearance inversion).
        Rewritten to expand scale when in horizontal position and value
        displayed on left/right
        also helpful for use in layouts
        """

        # We originally used QWIDGETSIZE_MAX here but the macro is only defined in PyQt and not PySide.
        # Instead we use it's direct value from the docs: https://doc.qt.io/qt-6/qwidget.html#QWIDGETSIZE_MAX
        self.setMaximumSize(16777215, 16777215)  # Unset fixed size
        if self._orientation == Qt.Horizontal:
            self._widget_width = self.width()
            self._widget_height = self.height()
            self._painter_translation_y = 0
            self._painter_rotation = 0
            # expands scale in horizontal position
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
            self._flip_translation_y = self._widget_height
            self._flip_scale_y = -1
        else:
            self._flip_translation_y = 0
            self._flip_scale_y = 1

    def draw_ticks(self):
        """
        Draw tick marks on the scale.
        Rewrote to draw them in a different place.
        """
        if not self._show_ticks:
            return
        self.set_tick_pen()
        self._painter.setPen(self._tick_pen)
        division_size = self._widget_width / self._num_divisions
        tick_y0 = self._scale_height * self._bg_size_rate
        tick_yf = tick_y0 + self._scale_height * self._tick_size_rate * 0.25
        for i in range(self._num_divisions + 1):
            x = i * division_size
            self._painter.drawLine(x, tick_y0, x, tick_yf)  # x1, y1, x2, y2

    """
    Currently unused, needs pulling in a second PV to be fully implemented
    def draw_set_point(self):

        #Draw a pointer as indicator of current value.

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
    """

    def draw_indicator(self):
        """
        Draw the indicator for current value.
        """
        self.set_position()
        if self.position < 0 or self.position > self._widget_width:
            return
        self._painter.setPen(Qt.transparent)
        self._painter.setBrush(self._indicator_color)
        pointer_width = self._pointer_width_rate * self._widget_width
        pointer_height = self._bg_size_rate * self._scale_height * 1.5
        points = [
            QPoint(int(self.position + 0.5 * pointer_width), 0),
            QPoint(int(self.position - 0.5 * pointer_width), 0),
            QPoint(int(self.position), int(pointer_height)),
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
        self._painter.drawRect(0, int(pointer_height), int(bg_width), int(bg_height))

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

        """
        sets the pen color to alarm if the value is in the lower minor alarm region
        """
        if self._value <= self._lower_minor_alarm and self._value > self._lower_major_alarm:
            self._painter.setBrush(self._minor_alarm_color)
        else:
            self._painter.setBrush(self._minor_alarm_region_color)
        if self._lower_minor_alarm > self._lower_limit:
            self._painter.drawRect(
                0,
                int(pointer_height),
                int(lower_minor_alarm_width),
                int(minor_alarm_height),
            )
        """
        sets the pen color to alarm if the value is in the upper minor alarm region
        """
        if self._value >= self._upper_minor_alarm and self._value < self._upper_major_alarm:
            self._painter.setBrush(self._minor_alarm_color)
        else:
            self._painter.setBrush(self._minor_alarm_region_color)
        if self._upper_minor_alarm < self._upper_limit:
            self._painter.drawRect(
                int(upper_minor_alarm_start),
                int(pointer_height),
                int(upper_minor_alarm_width),
                int(minor_alarm_height),
            )

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

        major_alarm_height = self._bg_size_rate * self._widget_height - 2

        """
        sets the pen color to alarm if the value is in the lower major alarm region
        """
        if self._value <= self._lower_major_alarm:
            self._painter.setBrush(self._major_alarm_color)
        else:
            self._painter.setBrush(self._major_alarm_region_color)
        # makes sure alarm value is in range
        if self._lower_major_alarm > self._lower_limit:
            self._painter.drawRect(
                0,
                int(pointer_height),
                int(lower_major_alarm_width),
                int(major_alarm_height),
            )

        """
        sets the pen color to alarm if the value is in the upper major alarm region
        """
        if self._value >= self._upper_major_alarm:
            self._painter.setBrush(self._major_alarm_color)
        else:
            self._painter.setBrush(self._major_alarm_region_color)
        # makes sure alarm value is in range
        if self._upper_major_alarm < self._upper_limit:
            self._painter.drawRect(
                int(upper_major_alarm_start),
                int(pointer_height),
                int(upper_major_alarm_width),
                int(major_alarm_height),
            )

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
        self._painter.translate(0, self._painter_translation_y)  # Draw vertically if needed
        self._painter.rotate(self._painter_rotation)
        self._painter.translate(self._painter_translation_x, 0)  # Invert appearance if needed
        self._painter.scale(self._painter_scale_x, 1)

        self._painter.translate(0, self._flip_translation_y)  # Invert scale if needed
        self._painter.scale(1, self._flip_scale_y)

        self._painter.setRenderHint(QPainter.Antialiasing)

        """
        bad metadata or user input can cause designer or pydm to crash when drawing the widget,
        hence the try except block.
        self._cannot_draw_*_flag variables are so that the errors only print once,
        otherwise they would print on each redraw.
        flags are reset when the element can draw without error.
        """
        try:
            self.draw_background()
        except Exception:
            if not self._cannot_draw_background_flag:
                print("Error: PyDMAlalogIndicator can't draw background, check upper and lower limits")
            self._cannot_draw_background_flag = True
        else:
            self._cannot_draw_background_flag = False
        try:
            if not self._upper_minor_alarm == self._lower_minor_alarm == 0:
                self.draw_minor_alarm_region()
        except Exception:
            if not self._cannot_draw_minor_alarm_region_flag:
                print("Error: PyDMAlalogIndicator can't draw minor alarm region, check minor alarm values and limits")
                self._cannot_draw_minor_alarm_region_flag = True
        else:
            self._cannot_draw_minor_alarm_region_flag = False
        try:
            if not self._upper_major_alarm == self._lower_major_alarm == 0:
                self.draw_major_alarm_region()
        except Exception:
            if not self._cannot_draw_major_alarm_region_flag:
                print("Error: PyDMAlalogIndicator can't draw major alarm region, check major alarm values and limits")
                self._cannot_draw_major_alarm_region_flag = True
        else:
            self._cannot_draw_major_alarm_region_flag = False
        try:
            self.draw_ticks()
        except Exception:
            if not self._cannot_draw_ticks_flag:
                print("Error: PyDMAlalogIndicator can't draw ticks")
                self._cannot_draw_ticks_flag = True
        else:
            self._cannot_draw_ticks_flag = False
        try:
            self.draw_indicator()
        except Exception:
            if not self._cannot_draw_indicator_flag:
                print("Error: PyDMAlalogIndicator can't draw_indicator")
                self._cannot_draw_indicator_flag = True
        else:
            self._cannot_draw_indicator_flag = False

        self._painter.end()

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

    def minimumSizeHint(self):
        fm = QFontMetrics(self.font())
        return QSize(fm.height(), fm.height())

    # reject some inherited things here


class PyDMAnalogIndicator(PyDMScaleIndicator):
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
        PyDMScaleIndicator.__init__(self, parent)
        self._show_limits = False
        self.scale_indicator = QScaleAlarmed()

        self._value_position = Qt.RightEdge
        self._minor_alarm_from_channel = True
        self._major_alarm_from_channel = True
        self._user_lower_minor_alarm = 0
        self._user_upper_minor_alarm = 0
        self._user_lower_major_alarm = 0
        self._user_upper_major_alarm = 0

        self.value_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setup_widgets_for_orientation(Qt.Horizontal, False, False, self._value_position)
        self.lower_label.hide()
        self.upper_label.hide()

    def sizeHint(self):
        """
        makes default size nice when dragging into designer nice
        """
        return QSize(250, 70)

    def lower_warning_limit_changed(self, new_minor_alarm):
        """
        Callback updates the lower minor alarm boundary
        """
        super().lower_warning_limit_changed(new_minor_alarm)
        if self.minorAlarmFromChannel:
            self.scale_indicator.set_lower_minor_alarm(new_minor_alarm)
            self.update_labels()

    def upper_warning_limit_changed(self, new_minor_alarm):
        """
        Callback updates the upper minor alarm boundary
        """
        super().upper_warning_limit_changed(new_minor_alarm)
        if self.minorAlarmFromChannel:
            self.scale_indicator.set_upper_minor_alarm(new_minor_alarm)
            self.update_labels()

    def lower_alarm_limit_changed(self, new_major_alarm):
        """
        Callback updates the lower major alarm boundary
        """
        super().lower_alarm_limit_changed(new_major_alarm)
        if self.majorAlarmFromChannel:
            self.scale_indicator.set_lower_major_alarm(new_major_alarm)
            self.update_labels()

    def upper_alarm_limit_changed(self, new_major_alarm):
        """
        Callback updates the upper major alarm boundary
        """
        super().upper_alarm_limit_changed(new_major_alarm)
        if self.majorAlarmFromChannel:
            self.scale_indicator.set_upper_major_alarm(new_major_alarm)
            self.update_labels()

    # Reject barIndicator setter and getter

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
        if self._major_alarm_from_channel != checked:
            self._major_alarm_from_channel = checked

            if checked:
                if self.lower_alarm_limit:
                    self.scale_indicator.set_lower_major_alarm(self.lower_alarm_limit)
                if self.upper_alarm_limit:
                    self.scale_indicator.set_upper_major_alarm(self.upper_alarm_limit)
            else:
                self.scale_indicator.set_lower_major_alarm(self._user_lower_major_alarm)
                self.scale_indicator.set_upper_major_alarm(self._user_upper_major_alarm)

            self.scale_indicator.set_lower_major_alarm(self.lower_alarm_limit)
            self.scale_indicator.set_upper_major_alarm(self.upper_alarm_limit)
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

    # Two properties available on PyDMScaleIndicator we don't support for PyDMAnalogIndicator
    originAtZero = Property(bool, None, None, designable=False)
    barIndicator = Property(bool, None, None, designable=False)
