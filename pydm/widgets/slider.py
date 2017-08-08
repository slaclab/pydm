from ..PyQt.QtGui import QFrame, QLabel, QSlider, QVBoxLayout, QHBoxLayout, QSizePolicy, QWidget
from ..PyQt.QtCore import Qt, pyqtSignal, pyqtSlot, pyqtProperty, QState, QStateMachine, QPropertyAnimation
from .channel import PyDMChannel
import numpy as np

class PyDMSlider(QFrame):
    actionTriggered = pyqtSignal(int)
    rangeChanged = pyqtSignal(float, float)
    sliderMoved = pyqtSignal(float)
    sliderPressed = pyqtSignal()
    sliderReleased = pyqtSignal()
    valueChanged = pyqtSignal(float)
    
    ALARM_NONE = 0
    ALARM_MINOR = 1
    ALARM_MAJOR = 2
    ALARM_INVALID = 3
    ALARM_DISCONNECTED = 4
    alarm_style_sheet_map = {
        ALARM_NONE: "QLabel {color: black;}",
        ALARM_MINOR: "QLabel {color: yellow;}",
        ALARM_MAJOR: "QLabel {color: red;}",
        ALARM_INVALID: "QLabel {color: purple;}",
        ALARM_DISCONNECTED: "QLabel {color: white;}"
    }
    
    def __init__(self, parent=None):
        super(PyDMSlider, self).__init__(parent=parent)
        #Internal values for properties
        self._connected = False
        self._write_access = False
        self.set_enable_state()
        self._channels = None
        self._channel = ""
        self._value = None
        self._user_defined_prec = False
        self._prec = 5
        self._format_string = "{:." + str(self._prec) + "f}"
        self._show_limit_labels = True
        self._show_value_label = True
        self._user_defined_limits = False
        self._needs_limit_info = True
        self._minimum = None
        self._maximum = None
        self._user_minimum = -10.0
        self._user_maximum = 10.0
        self._num_steps = 101
        self._orientation = Qt.Horizontal
        # Set up all the internal widgets that make up a PyDMSlider.
        # We'll add all these things to layouts when we call setup_widgets_for_orientation
        label_size_policy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.low_lim_label = QLabel(self)
        self.low_lim_label.setSizePolicy(label_size_policy)
        self.low_lim_label.setAlignment(Qt.AlignLeft|Qt.AlignTrailing|Qt.AlignVCenter)
        self.value_label = QLabel(self)
        self.value_label.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.high_lim_label = QLabel(self)
        self.high_lim_label.setSizePolicy(label_size_policy)
        self.high_lim_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self._slider = QSlider(parent=self)
        self._slider.setOrientation(Qt.Horizontal)
        self._slider.sliderMoved.connect(self.internal_slider_moved)
        self._slider.sliderPressed.connect(self.internal_slider_pressed)
        self._slider.sliderReleased.connect(self.internal_slider_released)
        self._slider.valueChanged.connect(self.internal_slider_value_changed)
        #self.vertical_layout.addWidget(self._slider)
        #Other internal variables and final setup steps
        self._slider_position_to_value_map = None
        self._mute_internal_slider_changes = False
        self.setup_widgets_for_orientation(self._orientation)
        self.reset_slider_limits()
    
    @pyqtProperty(Qt.Orientation)
    def orientation(self):
        return self._orientation
    
    @orientation.setter
    def orientation(self, new_orientation):
        self._orientation = new_orientation
        self.setup_widgets_for_orientation(new_orientation)
        
    def setup_widgets_for_orientation(self, new_orientation):
        layout = None
        if new_orientation == Qt.Horizontal:
            layout = QVBoxLayout()
            layout.setContentsMargins(4,0,4,4)
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
            layout.setContentsMargins(0,4,4,4)
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
            # Trick to remove the existing layout by reparenting it in an empty widget.
            QWidget().setLayout(self.layout())
        self.setLayout(layout)
    
    def update_labels(self):
        if self.minimum is None:
            self.low_lim_label.setText("")
        else:
            self.low_lim_label.setText(self._format_string.format(self.minimum))
        if self.maximum is None:
            self.high_lim_label.setText("")
        else:
            self.high_lim_label.setText(self._format_string.format(self.maximum))
        if self.value is None:
            self.value_label.setText("")
        else:
            self.value_label.setText(self._format_string.format(self.value))
        
    def reset_slider_limits(self):
        if self.minimum is None or self.maximum is None:
            self._needs_limit_info = True
            self.set_enable_state()
            return
        self._needs_limit_info = False
        self._slider.setMinimum(0)
        self._slider.setMaximum(self._num_steps-1)
        self._slider.setSingleStep(1)
        self._slider.setPageStep(10)
        self._slider_position_to_value_map = np.linspace(self.minimum, self.maximum, num=self._num_steps)
        self.update_labels()
        self.set_slider_to_closest_value(self.value)
        self.rangeChanged.emit(self.minimum, self.maximum)
        self.set_enable_state()
    
    def find_closest_slider_position_to_value(self, val):
        diff = abs(self._slider_position_to_value_map - float(val))
        return np.argmin(diff)
    
    def set_slider_to_closest_value(self, val):
        if val is None or self._needs_limit_info:
            return
        # When we set the slider to the closest value, it may end up at a slightly
        # different position than val (if val is not in self._slider_position_to_value_map)
        # We don't want that slight difference to get broacast out and put the channel
        # somewhere new.    For example, if the slider can only be at 0.4 or 0.5, but a
        # new value comes in of 0.45, its more important to keep the 0.45 than to change
        # it to where the slider gets set.  Therefore, we mute the internal slider changes
        # so that its valueChanged signal doesn't cause us to emit a signal to PyDM to change
        # the value of the channel.
        self._mute_internal_slider_changes = True
        self._slider.setValue(self.find_closest_slider_position_to_value(val))
        self._mute_internal_slider_changes = False
        
    @pyqtProperty(float)
    def value(self):
        return self._value
    
    @value.setter
    def value(self, new_val):
        self._value = float(new_val)
        self.value_label.setText(self._format_string.format(self._value))
        if not self._slider.isSliderDown():
            self.set_slider_to_closest_value(self._value)
        
    @pyqtSlot(int)
    @pyqtSlot(float)
    @pyqtSlot(str)
    def receiveValue(self, val):
        self.value = val
        
    @pyqtSlot(bool)
    def connectionStateChanged(self, connected):
        self._connected = connected
        self.set_enable_state()
        if not self._connected:
            self.alarmSeverityChanged(self.ALARM_DISCONNECTED)
    
    @pyqtSlot(bool)
    def writeAccessChanged(self, write_access):
        self._write_access = write_access
        self.set_enable_state()
    
    @pyqtSlot(int)
    def alarmSeverityChanged(self, new_alarm_severity):
        self.value_label.setStyleSheet(self.alarm_style_sheet_map[new_alarm_severity])
    
    @pyqtSlot(int)
    def precisionChanged(self, new_prec):
        if not self._user_defined_prec:
            self.precision = new_prec
    
    @pyqtSlot(float)
    def lowerCtrlLimitChanged(self, new_lower_limit):
        self._minimum = new_lower_limit
        if not self.userDefinedLimits:
            self.reset_slider_limits()
        
    @pyqtSlot(float)
    def upperCtrlLimitChanged(self, new_upper_limit):
        self._maximum = new_upper_limit
        if not self.userDefinedLimits:
            self.reset_slider_limits()
    
    def set_enable_state(self):
        self.setEnabled(self._write_access and self._connected and not self._needs_limit_info)
        
    @pyqtSlot(int)
    def internal_slider_action_triggered(self, action):
        self.actionTriggered.emit(action)
    
    @pyqtSlot(int)
    def internal_slider_moved(self, val):
        #The user has moved the slider, we need to update our value.
        #Only update the underlying value, not the self.value property,
        #because we don't need to reset the slider position.    If we change
        #self.value, we can get into a loop where the position changes, which
        #updates the value, which changes the position again, etc etc.
        self._value = self._slider_position_to_value_map[val]
        self.sliderMoved.emit(self.value)
    
    @pyqtSlot()
    def internal_slider_pressed(self):
        self.sliderPressed.emit()
    
    @pyqtSlot()
    def internal_slider_released(self):
        self.sliderReleased.emit()
    
    @pyqtSlot(int)
    def internal_slider_value_changed(self, val):
        #At this point, our local copy of the value reflects the position of the
        #slider, now all we need to do is emit a signal to PyDM so that the data
        #plugin will send a put to the channel.  Don't update self.value or self._value
        #in here, it is pointless at best, and could cause an infinite loop at worst.
        if not self._mute_internal_slider_changes:
            self.valueChanged.emit(self.value)
    
    @pyqtProperty(bool, doc=
    """
    showLimitLabels: Whether or not the high and low limits should be displayed on the slider.
    """
    )
    def showLimitLabels(self):
        return self._show_limit_labels
        
    @showLimitLabels.setter
    def showLimitLabels(self, checked):
        self._show_limit_labels = checked
        if checked:
            self.low_lim_label.show()
            self.high_lim_label.show()
        else:
            self.low_lim_label.hide()
            self.high_lim_label.hide()
    
    @pyqtProperty(bool, doc=
    """
    showValueLabel: Whether or not the current value should be displayed on the slider.
    """
    )
    def showValueLabel(self):
        return self._show_value_label
        
    @showValueLabel.setter
    def showValueLabel(self, checked):
        self._show_value_label = checked
        if checked:
            self.value_label.show()
        else:
            self.value_label.hide()
    
    @pyqtProperty(QSlider.TickPosition, doc=
    """
    Where to draw tick marks for the slider.
    """
    )
    def tickPosition(self):
        return self._slider.tickPosition()
    
    @tickPosition.setter
    def tickPosition(self, position):
        self._slider.setTickPosition(position)
    
    @pyqtProperty(bool)
    def userDefinedLimits(self):
        return self._user_defined_limits
    
    @userDefinedLimits.setter
    def userDefinedLimits(self, user_defined_limits):
        self._user_defined_limits = user_defined_limits
        self.reset_slider_limits()
        
    @pyqtProperty(float)
    def userMinimum(self):
        return self._user_minimum
    
    @userMinimum.setter
    def userMinimum(self, new_min):
        self._user_minimum = float(new_min)
        if self.userDefinedLimits:
            self.reset_slider_limits()
    
    @pyqtProperty(float)
    def userMaximum(self):
        return self._user_maximum
    
    @userMaximum.setter
    def userMaximum(self, new_max):
        self._user_maximum = float(new_max)
        if self.userDefinedLimits:
            self.reset_slider_limits()
    
    @property
    def minimum(self):
        if self.userDefinedLimits:
            return self._user_minimum
        return self._minimum
    
    @property
    def maximum(self):
        if self.userDefinedLimits:
            return self._user_maximum
        return self._maximum
    
    @pyqtProperty(int)
    def num_steps(self):
        return self._num_steps
    
    @num_steps.setter
    def num_steps(self, new_steps):
        self._num_steps = int(new_steps)
        self.reset_slider_limits()
    
    @pyqtProperty(bool)
    def userDefinedPrecision(self):
        return self._user_defined_prec
    
    @userDefinedPrecision.setter
    def userDefinedPrecision(self, user_defined_prec):
        self._user_defined_prec = user_defined_prec
    
    @pyqtProperty(int)
    def precision(self):
        return self._prec
    
    @precision.setter
    def precision(self, new_prec):
        self._prec = new_prec
        self._format_string = "{:." + str(self._prec) + "f}"
        self.update_labels()
    
    def getChannel(self):
        if self._channel is None:
            return ""
        return str(self._channel)
    
    def setChannel(self, value):
        if self._channel != value:
            self._channel = str(value)

    def resetChannel(self):
        if self._channel is not None:
            self._channel = None
    channel = pyqtProperty(str, getChannel, setChannel, resetChannel)

    def channels(self):
        if self._channels is None:
            self._channels = [PyDMChannel(address=self.channel, connection_slot=self.connectionStateChanged, value_slot=self.receiveValue, severity_slot=self.alarmSeverityChanged, write_access_slot=self.writeAccessChanged, value_signal=self.valueChanged, prec_slot=self.precisionChanged, upper_ctrl_limit_slot=self.upperCtrlLimitChanged, lower_ctrl_limit_slot=self.lowerCtrlLimitChanged)]
        return self._channels



