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
    self._value = 0.0
    self._show_limit_labels = True
    self._show_value_label = True
    self._minimum = -10.0
    self._maximum = 10.0
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
  
  def reset_slider_limits(self):
    self._slider.setMinimum(0)
    self._slider.setMaximum(self._num_steps-1)
    self._slider.setSingleStep(1)
    self._slider.setPageStep(10)
    self._slider_position_to_value_map = np.linspace(self._minimum, self._maximum, num=self._num_steps)
    self.low_lim_label.setText(str(self._minimum))
    self.high_lim_label.setText(str(self._maximum))
    self.value_label.setText(str(self._value))
    self.set_slider_to_closest_value(self.value)
    self.rangeChanged.emit(self._minimum, self._maximum)
  
  def find_closest_slider_position_to_value(self, val):
    diff = abs(self._slider_position_to_value_map - float(val))
    return np.argmin(diff)
  
  def set_slider_to_closest_value(self, val):
    self._slider.setValue(self.find_closest_slider_position_to_value(self._value))
  
  @pyqtProperty(float)
  def value(self):
    return self._value
  
  @value.setter
  def value(self, new_val):
    self._value = float(new_val)
    self._value = max(min(self._maximum, self._value), self._minimum)
    self.value_label.setText(str(self._value))
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
  
  def set_enable_state(self):
    self.setEnabled(self._write_access and self._connected)
    
  @pyqtSlot(int)
  def internal_slider_action_triggered(self, action):
    self.actionTriggered.emit(action)
  
  @pyqtSlot(int)
  def internal_slider_moved(self, val):
    self.value = self._slider_position_to_value_map[val]
    self.sliderMoved.emit(self.value)
  
  @pyqtSlot()
  def internal_slider_pressed(self):
    self.sliderPressed.emit()
  
  @pyqtSlot()
  def internal_slider_released(self):
    self.sliderReleased.emit()
  
  @pyqtSlot(int)
  def internal_slider_value_changed(self, val):
    self.value = self._slider_position_to_value_map[val]
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
    
  @pyqtProperty(float)
  def minimum(self):
    return self._minimum
  
  @minimum.setter
  def minimum(self, new_min):
    self._minimum = float(new_min)
    self.reset_slider_limits()
  
  @pyqtProperty(float)
  def maximum(self):
    return self._maximum
  
  @maximum.setter
  def maximum(self, new_max):
    self._maximum = float(new_max)
    self.reset_slider_limits()
  
  @pyqtProperty(int)
  def num_steps(self):
    return self._num_steps
  
  @num_steps.setter
  def num_steps(self, new_steps):
    self._num_steps = int(new_steps)
    self.reset_slider_limits()
  
  def getChannel(self):
    if self._channel is None:
      return ""
    return str(self._channel)
  
  def setChannel(self, value):
    if self._channel != value:
      self._channel = str(value)

  def resetChannel(self):
    if self._channel != None:
      self._channel = None
  channel = pyqtProperty(str, getChannel, setChannel, resetChannel)

  def channels(self):
    if self._channels is None:
      self._channels = [PyDMChannel(address=self.channel, connection_slot=self.connectionStateChanged, value_slot=self.receiveValue, severity_slot=self.alarmSeverityChanged, write_access_slot=self.writeAccessChanged, value_signal=self.valueChanged)]
    return self._channels



