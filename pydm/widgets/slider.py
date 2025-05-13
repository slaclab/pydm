import logging
import numpy as np
from decimal import Decimal
from qtpy.QtCore import Qt, Signal, Slot, Property, QRect, QPoint, QSize
from qtpy.QtWidgets import (
    QFrame,
    QLabel,
    QSlider,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QWidget,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QComboBox,
)
from pydm.widgets import PyDMLabel
from .base import PyDMWritableWidget, TextFormatter, is_channel_valid
from .channel import PyDMChannel

logger = logging.getLogger(__name__)
_step_size_properties = {
    "Set Step Size ": ["step_size", float],
}


class PyDMPrimitiveSlider(QSlider):
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.isDraggingHandle = False
        self.dragStartPos = None
        self.dragStartValue = None

    def mousePressEvent(self, event):
        """
        Handle mouse press events on the slider.

        Parameters
        ----------
        event : QMouseEvent
            The mouse event containing information about the press.
        """
        if event.button() == Qt.MiddleButton:
            return

        if event.button() == Qt.RightButton:
            super().mousePressEvent(event)
            return

        if event.button() == Qt.LeftButton:
            handle_rect = self.getHandleRect()

            if handle_rect.contains(event.pos()):
                self.isDraggingHandle = True
                self.dragStartPos = event.pos()
                self.dragStartValue = self.value()
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
            else:
                handle_pos, click_pos = self.getPositions(event)

                if self.shouldIncrement(handle_pos, click_pos):
                    self.setValue(self.value() + self.singleStep())
                else:
                    self.setValue(self.value() - self.singleStep())

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events to update the slider value during dragging.

        Parameters
        ----------
        event : QMouseEvent
            The mouse event containing information about the movement.
        """
        if self.isDraggingHandle:
            delta = event.pos() - self.dragStartPos

            if self.orientation() == Qt.Horizontal:
                delta_value = round((delta.x() / self.getSliderLength()) * (self.maximum() - self.minimum()))
            else:
                delta_value = round((-delta.y() / self.getSliderLength()) * (self.maximum() - self.minimum()))
            new_value = self.dragStartValue + delta_value
            new_value = min(max(self.minimum(), new_value), self.maximum())
            self.setValue(new_value)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events to stop dragging.

        Parameters
        ----------
        event : QMouseEvent
            The mouse event containing information about the release.
        """
        if event.button() == Qt.LeftButton and self.isDraggingHandle:
            self.isDraggingHandle = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def getHandleRect(self):
        """
        Calculate the rectangle representing the slider handle's position and size.

        Returns
        -------
        QRect
            The rectangle of the slider handle.
        """
        handle_size = self.getHandleSize()
        slider_pos = self.getSliderPosition()

        if self.orientation() == Qt.Horizontal:
            x = slider_pos - handle_size.width() / 2
            y = (self.height() - handle_size.height()) / 2
            rect = QRect(QPoint(int(x), int(y)), handle_size)
        else:
            x = (self.width() - handle_size.width()) / 2
            y = slider_pos - handle_size.height() / 2
            rect = QRect(QPoint(int(x), int(y)), handle_size)

        return rect

    def getPositions(self, event):
        """
        Retrieve the handle position and the click position based on the orientation.

        Parameters
        ----------
        event : QMouseEvent
            The mouse event containing information about the press.

        Returns
        -------
        tuple of float
            A tuple containing the handle position and the click position.
        """
        slider_pos = self.getSliderPosition()
        handle_pos = slider_pos

        if self.orientation() == Qt.Horizontal:
            click_pos = event.pos().x()
        else:
            click_pos = event.pos().y()

        return handle_pos, click_pos

    def shouldIncrement(self, handle_pos, click_pos):
        """
        Determine whether the slider value should be incremented based on positions.

        Parameters
        ----------
        handle_pos : float
            The position of the slider handle.
        click_pos : float
            The position where the user clicked.

        Returns
        -------
        bool
            True if the slider value should be incremented, False otherwise.
        """
        if self.orientation() == Qt.Horizontal:
            return click_pos > handle_pos
        else:
            return click_pos < handle_pos

    def getHandleSize(self):
        """
        Compute the size of the slider handle.

        Returns
        -------
        QSize
            The size of the slider handle.
        """
        handle_length = 20  # Fixed length for the handle
        if self.orientation() == Qt.Horizontal:
            return QSize(handle_length, self.height() // 2)
        else:
            return QSize(self.width() // 2, handle_length)

    def getSliderLength(self):
        """
        Calculate the usable length of the slider track excluding the handle size.

        Returns
        -------
        float
            The length of the slider track.
        """
        handle_size = self.getHandleSize()
        if self.orientation() == Qt.Horizontal:
            return self.width() - handle_size.width()
        else:
            return self.height() - handle_size.height()

    def getSliderPosition(self):
        """
        Compute the position of the slider handle along the track.

        Returns
        -------
        float
            The position of the slider handle along the slider track.
        """
        slider_min = self.minimum()
        slider_max = self.maximum()
        slider_range = slider_max - slider_min
        slider_value = self.value() - slider_min

        if slider_range == 0:
            proportion = 0
        else:
            proportion = slider_value / slider_range

        if self.orientation() == Qt.Horizontal:
            slider_length = self.getSliderLength()
            return proportion * slider_length + self.getHandleSize().width() / 2
        else:
            slider_length = self.getSliderLength()
            # 1 - proportion, because the largest positional value is at the bottom of the slider.
            return (1 - proportion) * slider_length + self.getHandleSize().height() / 2


class PyDMSlider(QFrame, TextFormatter, PyDMWritableWidget):
    """
    A QSlider with support for Channels and more from PyDM.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

    new_properties = _step_size_properties

    actionTriggered = Signal(int)
    rangeChanged = Signal(float, float)
    sliderMoved = Signal(float)
    sliderPressed = Signal()
    sliderReleased = Signal()
    valueChanged = Signal(float)

    def __init__(self, parent=None, init_channel=None):
        QFrame.__init__(self, parent)
        self.remap_flag = False
        PyDMWritableWidget.__init__(self, init_channel=init_channel)
        self.alarmSensitiveContent = True
        self.alarmSensitiveBorder = False
        # Internal values for properties
        self._ignore_mouse_wheel = True
        self._show_limit_labels = True
        self._show_value_label = True
        self._user_defined_limits = False
        self._needs_limit_info = True
        self._minimum = None
        self._maximum = None
        self._user_minimum = -10.0
        self._user_maximum = 10.0
        self._step_size = 0
        self._num_steps = 101
        self._orientation = Qt.Horizontal
        self._step_size_channel = None

        # Set up all the internal widgets that make up a PyDMSlider.
        # We'll add all these things to layouts when we call setup_widgets_for_orientation
        label_size_policy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.low_lim_label = QLabel(self)
        self.low_lim_label.setObjectName("lowLimLabel")
        self.low_lim_label.setSizePolicy(label_size_policy)
        self.low_lim_label.setAlignment(Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.value_label = QLabel(self)
        self.value_label.setObjectName("valueLabel")
        self.value_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.high_lim_label = QLabel(self)
        self.high_lim_label.setObjectName("highLimLabel")
        self.high_lim_label.setSizePolicy(label_size_policy)
        self.high_lim_label.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
        self._slider = PyDMPrimitiveSlider(parent=self)

        # Pass PyDMPrimitiveWidget eventfilter to self._slider so it will have the tooltip display
        # the address name from middle clicking on the widget
        self._slider.installEventFilter(self)

        self._slider.setOrientation(Qt.Horizontal)

        self._orig_wheel_event = self._slider.wheelEvent
        self._slider.wheelEvent = self.wheelEvent

        self._slider.sliderMoved.connect(self.internal_slider_moved)
        self._slider.sliderPressed.connect(self.internal_slider_pressed)
        self._slider.sliderReleased.connect(self.internal_slider_released)
        self._slider.valueChanged.connect(self.internal_slider_value_changed)

        # Other internal variables and final setup steps
        self._slider_position_to_value_map = None
        self._mute_internal_slider_changes = False
        self.setup_widgets_for_orientation(self._orientation)
        self.reset_slider_limits()

        self.slider_parameters_menu_widget = None
        self.slider_parameters_menu_input_widgets = None
        self.slider_parameters_menu_labels = None
        self.slider_parameters_menu_buttons = None
        self.menu_layout = None
        self._parameters_menu_flag = False
        self.step_max = self.maximum
        self._step_size_channel = None
        self.step_size_channel_pv = None

    # On pyside6, we need to expilcity call pydm's base class's eventFilter() call or events
    # will not propagate to the parent classes properly.
    def eventFilter(self, obj, event):
        return PyDMWritableWidget.eventFilter(self, obj, event)

    def wheelEvent(self, e):
        """
        Method to specifically ignore mouse wheel events.
        """
        if self._ignore_mouse_wheel:
            e.ignore()
        else:
            super().wheelEvent(e)
        return

    def mousePressEvent(self, mouse_event):
        """
        Method to open slider parameters menu with a right click.

        Parameters
        ----------
        mouse_event : mousePressEvent
        """
        if mouse_event.button() == Qt.RightButton:
            position_of_click = mouse_event.pos()
            self.slider_parameters_menu(position_of_click)

    def slider_parameters_menu(self, position_of_click):
        """
        Method that builds a menu to modify a set of Slider Parameters:
            1)	value
            2)	new step size (float or channel) and scale factor for step size
            3)	precision or if precision is defined from a channel
            4)	format of numbers on slider (min, max, value) - float or exp
        """
        self.slider_parameters_menu_widget = QWidget()
        self.slider_parameters_menu_widget.move(self._slider.parentWidget().mapToGlobal(position_of_click))
        self.slider_parameters_menu_widget.show()

        self.slider_parameters_menu_widget.setWindowTitle("PyDM Slider Parameters")
        self.slider_parameters_menu_widget.resize(300, 200)

        main_layout = QVBoxLayout(self.slider_parameters_menu_widget)

        self.slider_parameters_menu_input_widgets = []
        self.slider_parameters_menu_labels = []
        self.slider_parameters_menu_buttons = []
        self.menu_layout = []

        text_info = [
            "Value",
            "Increment",
            "Increment scale",
            "Precision",
            "Precision from PV",
            "Number Format",
            "OK",
            "Apply",
            "Cancel",
        ]

        combo_box_table_scale = ["1e0", "1e1", "1e2", "1e3", "1e4", "1e5"]
        combo_box_table_format = ["Float", "Exp"]

        for key in range(0, 6):
            self.slider_parameters_menu_input_widgets.append(key)
            self.slider_parameters_menu_labels.append(key)
            self.menu_layout.append(key)

            self.menu_layout[key] = QHBoxLayout()
            self.menu_layout[key].setAlignment(Qt.AlignLeft)

            self.slider_parameters_menu_labels[key] = PyDMLabel(self.slider_parameters_menu_widget)
            self.slider_parameters_menu_labels[key].setText(text_info[key])
            self.menu_layout[key].addWidget(self.slider_parameters_menu_labels[key])

            if key == 4:
                self.slider_parameters_menu_input_widgets[key] = QCheckBox()
                self.slider_parameters_menu_input_widgets[key].setTristate(on=False)
                self.slider_parameters_menu_input_widgets[key].setChecked(self.precisionFromPV)
            elif key == 2 or key == 5:
                self.slider_parameters_menu_input_widgets[key] = QComboBox()
            else:
                self.slider_parameters_menu_input_widgets[key] = QLineEdit()
                self.slider_parameters_menu_input_widgets[key].setText("")

            self.menu_layout[key].addWidget(self.slider_parameters_menu_input_widgets[key])
            main_layout.addLayout(self.menu_layout[key])

        self.menu_layout.append(3)
        self.menu_layout[3] = QHBoxLayout()

        self.slider_parameters_menu_input_widgets[0].setText(str(self.value))
        self.slider_parameters_menu_input_widgets[1].setText(str(self._step_size))
        self.slider_parameters_menu_input_widgets[3].setText(str(self.precision))

        self.slider_parameters_menu_input_widgets[2].addItems(combo_box_table_scale)
        self.slider_parameters_menu_input_widgets[5].addItems(combo_box_table_format)

        for key in range(0, 3):
            self.slider_parameters_menu_buttons.append(key)
            self.slider_parameters_menu_buttons[key] = QPushButton(self.slider_parameters_menu_widget)
            self.slider_parameters_menu_buttons[key].setText(text_info[key + 6])
            self.menu_layout[3].addWidget(self.slider_parameters_menu_buttons[key])

        main_layout.addLayout(self.menu_layout[3])

        self.slider_parameters_menu_buttons[0].clicked.connect(self.apply_and_close_menu)
        self.slider_parameters_menu_buttons[1].clicked.connect(self.apply_step_size_menu_changes)
        self.slider_parameters_menu_buttons[2].clicked.connect(self.slider_parameters_menu_widget.close)

    def apply_and_close_menu(self):
        """
        Method for the 'ok' button in the slider parameters menu.
        """
        self.apply_step_size_menu_changes()
        self.slider_parameters_menu_widget.close()

    def apply_step_size_menu_changes(self):
        """
        Method which attempts to set the user imputed data from the slider parameters menu.
        """
        # check
        try:
            slider_value = float(self.slider_parameters_menu_input_widgets[0].text())

            if slider_value < self.minimum or slider_value > self.maximum:
                raise ValueError
            if slider_value != self.value:
                self.remap_flag = True
                self.value_changed(slider_value)
                self.send_value_signal[float].emit(self.value)
        except ValueError:
            logger.error("the given value is not a valid type or outside of the slider range")

        try:
            self.remap_flag = True
            # checks if input can be converted to a float if not connect to a new channel
            new_step_size = float(self.slider_parameters_menu_input_widgets[1].text())
            new_step_size_scaled = new_step_size * float(self.slider_parameters_menu_input_widgets[2].currentText())
            if new_step_size_scaled > 0:
                # if new step_size scaled greater than zero we want to
                # disconnect the step size channel and reset step size

                if self.step_size_channel_pv is not None:
                    self.step_size_channel_pv.disconnect()
                    self.step_size_channel_pv = None
                    self.step_size_channel = None
                self.step_size = new_step_size_scaled
            else:
                logger.error("step input is incorrect or 0")
        except ValueError:
            # want all logic for receiving a string here
            if is_channel_valid(self.slider_parameters_menu_input_widgets[1].text()):
                pv_address = self.slider_parameters_menu_input_widgets[1].text()
                self.init_step_size_channel(pv_address=pv_address, slot=self.step_size_changed)
                self.step_size_channel = pv_address
            else:
                logger.error("step input is incorrect")

        precision_source = self.slider_parameters_menu_input_widgets[4].isChecked()
        self.precisionFromPV = precision_source
        try:
            user_inputted_precision = float(self.slider_parameters_menu_input_widgets[3].text())
            self.precision = user_inputted_precision

        except ValueError:
            logger.error("precision input is incorrect")

        format_type = self.slider_parameters_menu_input_widgets[5].currentText()

        if format_type == "Float":
            self.update_labels()
        else:
            self.update_labels(True)

    def init_for_designer(self):
        """
        Method called after the constructor to tweak configurations for
        when using the widget with the Qt Designer
        """
        self.value = 0.0

    @Property(Qt.Orientation)
    def orientation(self):
        """
        The slider orientation (Horizontal or Vertical)

        Returns
        -------
        int
            Qt.Horizontal or Qt.Vertical
        """
        return self._orientation

    @orientation.setter
    def orientation(self, new_orientation):
        """
        The slider orientation (Horizontal or Vertical)

        Parameters
        ----------
        new_orientation : Qt.Orientation
            Qt.Horizontal or Qt.Vertical
        """
        self._orientation = new_orientation
        self.setup_widgets_for_orientation(new_orientation)

    def setup_widgets_for_orientation(self, new_orientation):
        """
        Reconstruct the widget given the orientation.

        Parameters
        ----------
        new_orientation : Qt.Orientation
            Qt.Horizontal or Qt.Vertical
        """
        if new_orientation not in (Qt.Horizontal, Qt.Vertical):
            logger.error("Invalid orientation '{0}'. The existing layout will not change.".format(new_orientation))
            return

        layout = None
        if new_orientation == Qt.Horizontal:
            layout = QVBoxLayout()
            layout.setContentsMargins(4, 0, 4, 4)
            label_layout = QHBoxLayout()
            label_layout.addWidget(self.low_lim_label)
            label_layout.addStretch(0)
            label_layout.addWidget(self.value_label)
            label_layout.addStretch(0)
            label_layout.addWidget(self.high_lim_label)
            layout.addLayout(label_layout)
            self._slider.setOrientation(new_orientation)
            layout.addWidget(self._slider)
        elif new_orientation == Qt.Vertical:
            layout = QHBoxLayout()
            layout.setContentsMargins(0, 4, 4, 4)
            label_layout = QVBoxLayout()
            label_layout.addWidget(self.high_lim_label)
            label_layout.addStretch(0)
            label_layout.addWidget(self.value_label)
            label_layout.addStretch(0)
            label_layout.addWidget(self.low_lim_label)
            layout.addLayout(label_layout)
            self._slider.setOrientation(new_orientation)
            layout.addWidget(self._slider)

        if self.layout() is not None:
            # Trick to remove the existing layout by re-parenting it in an empty widget.
            QWidget().setLayout(self.layout())
        self.setLayout(layout)

    def update_labels(self, exp=False):
        """
        Update the limits and value labels with the correct values.
        """

        def set_label(value, label_widget, exp_format):
            if value is None:
                label_widget.setText("")
            else:
                if not exp_format:
                    label_widget.setText(self.format_string.format(value))
                else:
                    text = "%." + str(self.precision) + "E"
                    text = text % Decimal(str(value))
                    if self._show_units and self._unit != "":
                        text += " {}".format(self._unit)
                    label_widget.setText(text)

        set_label(self.minimum, self.low_lim_label, exp)
        set_label(self.maximum, self.high_lim_label, exp)
        set_label(self.value, self.value_label, exp)

    def reset_slider_limits(self):
        """
        Reset the limits and adjust the labels properly for the slider.
        """
        logger.debug("Running reset_slider_limits.")
        if self.minimum is None or self.maximum is None:
            self._needs_limit_info = True
            logger.debug("Need both limits before reset_slider_limits can work.")
            self.set_enable_state()
            return
        logger.debug("Has both limits, proceeding.")
        self._needs_limit_info = False
        if self._parameters_menu_flag:
            self._slider_position_to_value_map = self.create_slider_positions_to_value_map()
            self._parameters_menu_flag = False
        else:
            # if no defaults. create a linear space from min to max from default num_steps = 101,
            # this means we can't step to max, but also can't call create map without a value
            self._slider_position_to_value_map = np.linspace(self.minimum, self.maximum, num=self._num_steps)

            if is_channel_valid(self.step_size_channel):
                self.init_step_size_channel(pv_address=self.step_size_channel, slot=self.step_size_changed)

        self.update_labels()
        self.rangeChanged.emit(self.minimum, self.maximum)
        self._slider.setMinimum(0)
        self._slider.valueChanged.disconnect(self.internal_slider_value_changed)
        self._slider.setMaximum(self._num_steps)
        self._slider.valueChanged.connect(self.internal_slider_value_changed)

        self.set_slider_to_closest_value(self.value)

        self._slider.setSingleStep(1)
        self._slider.setPageStep(1)
        self.set_enable_state()

    def init_step_size_channel(self, pv_address: str, slot: callable):
        """
        Connects instance attribute self.step_size_channel_pv to a PyDMChannel

        Parameters
        ---------
        pv_address: str
            Channel name of PV that connection will be established too.
        slot: callable
            callback function to invoke when channel value changes.
        """
        if self.step_size_channel_pv is None:
            self.step_size_channel_pv = PyDMChannel(address=pv_address, value_slot=slot)
            self.step_size_channel_pv.connect()

        elif self.step_size_channel_pv is not None and self.step_size_channel_pv.address != pv_address:
            self.step_size_channel_pv.disconnect()
            self.step_size_channel_pv = None
            self.step_size_channel_pv = PyDMChannel(address=pv_address, value_slot=slot)
            self.step_size_channel_pv.connect()

    def create_slider_positions_to_value_map(self):
        """
        Wrapper around step_size_to_slider_positions_value_map to ensure
        the func is only called after a step_size has been set

        Returns
        -------
        positions_to_value_map: list
            list with all possible allowed slider readback values
        """
        if self._step_size > 0:
            positions_to_values_map = self.step_size_to_slider_positions_value_map()

        elif self._step_size == 0:
            self.calc_step_size()
            positions_to_values_map = self.step_size_to_slider_positions_value_map()

        self.remap_flag = False
        return positions_to_values_map

    def step_size_to_slider_positions_value_map(self):
        """
        Given a value increment by step size and record allowed values until self.maximum,
        Repeat with decrementer until self.minimum, take results and create a linear
        array of allowed values where the length of the array is the number of slider positions.
        and the slider position i has value array[i].
        """
        if self.value is not None and (self.value > self.maximum or self.value < self.minimum):
            logger.debug("Slider out of bounds.")
            self._slider.setEnabled(False)
            raise ValueError("Slider is out of bounds either greater than max or less than min")

        forward_map = []
        backward_map = []
        forward_map_value = self.value
        backward_map_value = self.value

        while forward_map_value < self.maximum:
            forward_map.append(forward_map_value)
            forward_map_value += self._step_size
        # check if end points are less than or greater than correct vals,
        # if less add a new point, is greater set endpoint to max/min

        if len(forward_map) == 0:
            # if len zero we are at or passed maximum. so all we need
            # is the max ele for the map
            forward_map.append(self.maximum)
        elif round(float(forward_map[-1]), self.precision + 1) < round(float(self.maximum), self.precision + 1):
            forward_map.append(self.maximum)
        elif forward_map[-1] > self.maximum:
            forward_map[-1] = self.maximum

        while backward_map_value > self.minimum:
            backward_map_value -= self._step_size
            backward_map.append(backward_map_value)
        if len(backward_map) == 0:
            pass
        elif round(float(backward_map[-1]), self.precision + 1) > round(float(self.minimum), self.precision + 1):
            backward_map.append(self.minimum)
        elif backward_map[-1] < self.minimum:
            backward_map[-1] = self.minimum

        backward_map = list(reversed(backward_map))
        slider_position_map = np.array(backward_map + forward_map)
        self._num_steps = len(slider_position_map) - 1

        return slider_position_map

    def calc_step_size(self):
        """
        Given max, min, and num steps calculate step size
        """
        self.step_size = (self.maximum - self.minimum) / self.num_steps
        if self.step_size == 0:
            self._slider.setEnabled(False)
            raise ValueError("step size is zero after calc step step size")

    def find_closest_slider_position_to_value(self, val):
        """
        Find and returns the index for the closest position on the slider
        for a given value.

        Parameters
        ----------

        Returns
        -------
        int
        """
        diff = abs(self._slider_position_to_value_map - float(val))
        logger.debug("The closest value to %f is: %f", val, self._slider_position_to_value_map[np.argmin(diff)])
        return np.argmin(diff)

    def set_slider_to_closest_value(self, val):
        """
        Set the value for the slider according to a given value.

        Parameters
        ----------
        val : float
        """

        if val is None or self._needs_limit_info:
            logger.debug("Not setting slider to closest value because we need limits.")
            return
        # When we set the slider to the closest value, it may end up at a slightly
        # different position than val (if val is not in self._slider_position_to_value_map)
        # We don't want that slight difference to get broadcast out and put the channel
        # somewhere new.    For example, if the slider can only be at 0.4 or 0.5, but a
        # new value comes in of 0.45, its more important to keep the 0.45 than to change
        # it to where the slider gets set.  Therefore, we mute the internal slider changes
        # so that its valueChanged signal doesn't cause us to emit a signal to PyDM to change
        # the value of the channel.
        logger.debug("Setting slider to closest value.")
        self._mute_internal_slider_changes = True
        self._slider.setValue(self.find_closest_slider_position_to_value(val))
        self._mute_internal_slider_changes = False

    def connection_changed(self, connected):
        """
        Callback invoked when the connection state of the Channel is changed.
        This callback acts on the connection state to enable/disable the widget
        and also trigger the change on alarm severity to ALARM_DISCONNECTED.

        Parameters
        ----------
        connected : int
            When this value is 0 the channel is disconnected, 1 otherwise.
        """
        super().connection_changed(connected)
        self.set_enable_state()

    def write_access_changed(self, new_write_access):
        """
        Callback invoked when the Channel has new write access value.
        This callback calls check_enable_state so it can act on the widget
        enabling or disabling it accordingly

        Parameters
        ----------
        new_write_access : bool
            True if write operations to the channel are allowed.
        """
        super().write_access_changed(new_write_access)
        self.set_enable_state()

    def value_changed(self, new_val):
        """
        Callback invoked when the Channel value is changed.

        Parameters
        ----------
        new_val : int or float
            The new value from the channel.
        """

        self.check_if_value_in_map(new_val)

        # Calls find_closest_slider_position_to_value twice.

        PyDMWritableWidget.value_changed(self, new_val)
        if hasattr(self, "value_label"):
            logger.debug("Setting text for value label.")
            self.value_label.setText(self.format_string.format(self.value))
        # isSliderDown code is probably deprecable, if you want use it
        # PyDMWritableWidget.value_changed(self, new_val) should be moved inside
        if not self._slider.isSliderDown():
            self.set_slider_to_closest_value(self.value)
        self.update_format_string()

    def check_if_value_in_map(self, val):
        if self._slider_position_to_value_map is not None:
            arg_diff = self.find_closest_slider_position_to_value(val)
            smallest_diff = self._slider_position_to_value_map[arg_diff] - float(val)
            if smallest_diff != 0.0:
                self.remap_flag = True

    def ctrl_limit_changed(self, which, new_limit):
        """
        Callback invoked when the Channel receives new control limit
        values.

        Parameters
        ----------
        which : str
            Which control limit was changed. "UPPER" or "LOWER"
        new_limit : float
            New value for the control limit
        """
        logger.debug("%s limit changed to %f", which, new_limit)
        PyDMWritableWidget.ctrl_limit_changed(self, which, new_limit)
        if not self.userDefinedLimits:
            self.reset_slider_limits()

    def update_format_string(self):
        """
        Reconstruct the format string to be used when representing the
        output value.

        Returns
        -------
        format_string : str
            The format string to be used including or not the precision
            and unit
        """
        fs = super().update_format_string()
        self.update_labels()
        return fs

    def set_enable_state(self):
        """
        Determines Whether or not the widget must be enabled or not depending
        on the write access, connection state and presence of limits information
        """
        # Even though by documentation disabling parent QFrame (self), should disable internal
        # slider, in practice it still remains interactive (PyQt 5.12.1). Disabling explicitly, solves
        # the problem.
        should_enable = self._write_access and self._connected and not self._needs_limit_info
        self.setEnabled(should_enable)
        self._slider.setEnabled(should_enable)

    @Slot(int)
    def internal_slider_action_triggered(self, action):
        self.actionTriggered.emit(action)

    @Slot(int)
    def internal_slider_moved(self, val):
        """
        Method invoked when the slider is moved.

        Parameters
        ----------
        val : float
        """
        self.sliderMoved.emit(self.value)

    @Slot()
    def internal_slider_pressed(self):
        """
        Method invoked when the slider is pressed
        """
        self.sliderPressed.emit()

    @Slot()
    def internal_slider_released(self):
        """
        Method invoked when the slider is released
        """
        self.sliderReleased.emit()

    @Slot(int)
    def internal_slider_value_changed(self, val):
        """
        Method invoked when a new value is selected on the slider.
        This will cause the new value to be emitted to the signal
        unless `mute_internal_slider_changes` is True.

        Parameters
        ----------
        val : int
        """
        # Avoid potential crash if limits are undefined

        if self._slider_position_to_value_map is None:
            return
        if not self._mute_internal_slider_changes:
            try:
                self.value = self._slider_position_to_value_map[val]

                self.send_value_signal[float].emit(self.value)
            except IndexError:
                pass

    @Property(bool)
    def tracking(self):
        """
        If tracking is enabled (the default), the slider emits new values
        while the slider is being dragged.  If tracking is disabled, it will
        only emit new values when the user releases the slider.  Tracking can
        cause PyDM to rapidly send new values to the channel.  If you are using
        the slider to control physical hardware, consider whether the device
        you want to control can handle large amounts of changes in a short
        timespan.
        """
        return self._slider.hasTracking()

    @tracking.setter
    def tracking(self, checked):
        self._slider.setTracking(checked)

    def hasTracking(self):
        """
        An alternative function to get the tracking property, to match what
        Qt provides for QSlider.
        """
        return self.tracking

    def setTracking(self, checked):
        """
        An alternative function to set the tracking property, to match what
        Qt provides for QSlider.
        """
        self.tracking = checked

    @Property(bool)
    def ignoreMouseWheel(self):
        """
        If true, the mouse wheel will not change the value of the slider.
        This is useful if you want to put sliders inside a scroll view, and
        don't want to accidentally change the slider as you are scrolling.
        """
        return self._ignore_mouse_wheel

    @ignoreMouseWheel.setter
    def ignoreMouseWheel(self, checked):
        self._ignore_mouse_wheel = checked
        if checked:
            self._slider.wheelEvent = self.wheelEvent
        else:
            self._slider.wheelEvent = self._orig_wheel_event

    @Property(bool)
    def showLimitLabels(self):
        """
        Whether or not the high and low limits should be displayed on the slider.

        Returns
        -------
        bool
        """
        return self._show_limit_labels

    @showLimitLabels.setter
    def showLimitLabels(self, checked):
        """
        Whether or not the high and low limits should be displayed on the slider.

        Parameters
        ----------
        checked : bool
        """
        self._show_limit_labels = checked
        if checked:
            self.low_lim_label.show()
            self.high_lim_label.show()
        else:
            self.low_lim_label.hide()
            self.high_lim_label.hide()

    @Property(bool)
    def showValueLabel(self):
        """
        Whether or not the current value should be displayed on the slider.

        Returns
        -------
        bool
        """
        return self._show_value_label

    @showValueLabel.setter
    def showValueLabel(self, checked):
        """
        Whether or not the current value should be displayed on the slider.

        Parameters
        ----------
        checked : bool
        """
        self._show_value_label = checked
        if checked:
            self.value_label.show()
        else:
            self.value_label.hide()

    @Property(QSlider.TickPosition)
    def tickPosition(self):
        """
        Where to draw tick marks for the slider.

        Returns
        -------
        QSlider.TickPosition
        """
        return self._slider.tickPosition()

    @tickPosition.setter
    def tickPosition(self, position):
        """
        Where to draw tick marks for the slider.

        Parameter
        ---------
        position : QSlider.TickPosition
        """
        self._slider.setTickPosition(position)

    @Property(bool)
    def userDefinedLimits(self):
        """
        Whether or not to use limits defined by the user and not from the
        channel

        Returns
        -------
        bool
        """
        return self._user_defined_limits

    @userDefinedLimits.setter
    def userDefinedLimits(self, user_defined_limits):
        """
        Whether or not to use limits defined by the user and not from the
        channel

        Parameters
        ----------
        user_defined_limits : bool
        """
        self._user_defined_limits = user_defined_limits
        self.reset_slider_limits()

    @Property(float)
    def userMinimum(self):
        """
        Lower user defined limit value

        Returns
        -------
        float
        """
        return self._user_minimum

    @userMinimum.setter
    def userMinimum(self, new_min):
        """
        Lower user defined limit value

        Parameters
        ----------
        new_min : float
        """
        self._user_minimum = float(new_min) if new_min is not None else None
        if self.userDefinedLimits:
            self.reset_slider_limits()

    @Property(float)
    def userMaximum(self):
        """
        Upper user defined limit value

        Returns
        -------
        float
        """
        return self._user_maximum

    @userMaximum.setter
    def userMaximum(self, new_max):
        """
        Upper user defined limit value

        Parameters
        ----------
        new_max : float
        """
        self._user_maximum = float(new_max) if new_max is not None else None
        if self.userDefinedLimits:
            self.reset_slider_limits()

    @property
    def minimum(self):
        """
        The current value being used for the lower limit

        Returns
        -------
        float
        """
        if self.userDefinedLimits:
            return self._user_minimum
        return self._lower_ctrl_limit

    @property
    def maximum(self):
        """
        The current value being used for the upper limit

        Returns
        -------
        float
        """
        if self.userDefinedLimits:
            return self._user_maximum
        return self._upper_ctrl_limit

    @Property(int)
    def num_steps(self):
        """
        The number of steps on the slider

        Returns
        -------
        int
        """
        return self._num_steps

    @num_steps.setter
    def num_steps(self, new_steps):
        """
        The number of steps on the slider

        Parameters
        ----------
        new_steps : int
        """

        self._num_steps = int(new_steps)
        self.reset_slider_limits()

    @Property(float)
    def step_size(self):
        """
        The number of steps on the slider

        Returns
        -------
        int
        """

        return self._step_size

    @step_size.setter
    def step_size(self, new_step_size):
        """
        The number of steps on the slider

        Parameters
        ----------
        new_step_size : float
        """

        if self.maximum is None or self.minimum is None or new_step_size <= 0:
            return False

        self._step_size = float(new_step_size)
        self._parameters_menu_flag = True
        self.num_steps = (self.maximum - self.minimum) / self._step_size
        if self.num_steps == 0:
            raise ValueError("Num steps is set to zero")

        return True

    @Slot(str)
    @Slot(float)
    def step_size_changed(self, new_val):
        """
        PyQT Slot for changes on the Value of the Channel
        This slot sends the value to the step_size setter.

        Parameters
        ----------
        new_val : int, float
        """
        try:
            self.step_size = float(new_val)
        except ValueError:
            logger.debug("cannot cast PV value as float")

    @Property(str)
    def step_size_channel(self):
        """
        String to connect to pydm channel after initialization
        """
        return self._step_size_channel

    @step_size_channel.setter
    def step_size_channel(self, step_size_channel):
        self._step_size_channel = step_size_channel

    @property
    def value(self):
        """
        Channel readback value used to determine slider position
        and generate a slider positions to value map
        """
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value
        if self.remap_flag:
            self._slider_position_to_value_map = self.create_slider_positions_to_value_map()
