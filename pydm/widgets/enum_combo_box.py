from ..PyQt.QtGui import QWidget, QComboBox, QHBoxLayout
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty
from .channel import PyDMChannel

class PyDMEnumComboBox(QWidget):
  activated = pyqtSignal([int], [str])
  currentIndexChanged = pyqtSignal([int], [str])
  highlighted = pyqtSignal([int], [str])
  valueChanged = pyqtSignal(int)
  
  ALARM_NONE = 0
  ALARM_MINOR = 1
  ALARM_MAJOR = 2
  ALARM_INVALID = 3
  ALARM_DISCONNECTED = 4
  alarm_style_sheet_map = {
      ALARM_NONE: "QComboBox {color: black;}",
      ALARM_MINOR: "QComboBox {color: yellow;}",
      ALARM_MAJOR: "QComboBox {color: red;}",
      ALARM_INVALID: "QComboBox {color: purple;}",
      ALARM_DISCONNECTED: "QComboBox {color: white;}"
  }
  
  def __init__(self, parent=None):
    super(PyDMEnumComboBox, self).__init__(parent=parent)
    self.horizontal_layout = QHBoxLayout(self)
    self.combo_box = QComboBox(self)
    self.horizontal_layout.addWidget(self.combo_box)
    #Internal values for properties
    self._connected = False
    self._write_access = True
    self._has_enums = False
    self._channels = None
    self._channel = ""
    self._value = None
    self.setEnabled(False)
    self.combo_box.activated[int].connect(self.internal_combo_box_activated_int)
    self.combo_box.activated[str].connect(self.internal_combo_box_activated_str)
    self.combo_box.currentIndexChanged[int].connect(self.internal_combo_box_index_changed_int)
    self.combo_box.currentIndexChanged[str].connect(self.internal_combo_box_index_changed_str)
    self.combo_box.highlighted[int].connect(self.internal_combo_box_highlighted_int)
    self.combo_box.highlighted[str].connect(self.internal_combo_box_highlighted_str)

  #Internal properties we don't expose to PyQt (so designer doesn't see them)
  
  @property
  def connected(self):
    return self._connected
  
  @connected.setter
  def connected(self, connected):
    self._connected = connected
    self.update_enable_state()
  
  @property
  def write_access(self):
    return self._write_access
  
  @write_access.setter
  def write_access(self, write_access):
    self._write_access = write_access
    self.update_enable_state()
  
  @property
  def has_enums(self):
    return self._has_enums
  
  @has_enums.setter
  def has_enums(self, has_enums):
    self._has_enums = has_enums
    self.update_enable_state()
  
  #Internal methods
  
  def set_items(self, enums):
    self.combo_box.clear()
    for enum in enums:
      self.combo_box.addItem(enum)
    self.has_enums = True
  
  def update_enable_state(self):
    self.setEnabled(self.write_access and self.connected and self.has_enums)
  
  #PyDM widget slots
  
  @pyqtSlot(bool)
  def connectionStateChanged(self, connected):
    self.connected = connected
  
  @pyqtSlot(bool)
  def writeAccessChanged(self, write_access):
    self.write_access = write_access
  
  @pyqtSlot(tuple)
  def enumStringsChanged(self, enum_strings):
    self.set_items(enum_strings)
  
  @pyqtSlot(int)
  def alarmSeverityChanged(self, new_alarm_severity):
    if not self.connected:
      new_alarm_severity = self.ALARM_DISCONNECTED
    self.combo_box.setStyleSheet(self.alarm_style_sheet_map[new_alarm_severity])
  
  @pyqtSlot(int)
  @pyqtSlot(float)
  @pyqtSlot(str)
  def receiveValue(self, new_val):
    if self._value != new_val:
      self._value = new_val
      self.combo_box.setCurrentIndex(new_val)
  
  #Internal combo box signal handling.
  #In places where we just forward the signal, we may want to instead just do self.signal = self.combo_box.signal
  #in __init__...
  
  @pyqtSlot(int)
  def internal_combo_box_activated_int(self, index):
    if self._value != index:
      self._value = index
      self.valueChanged.emit(index)
    self.activated[int].emit(index)
  
  @pyqtSlot(str)
  def internal_combo_box_activated_str(self, text):
    self.activated[str].emit(text)
  
  @pyqtSlot(int)
  def internal_combo_box_index_changed_int(self, index):
    self.currentIndexChanged[int].emit(index)
  
  @pyqtSlot(str)
  def internal_combo_box_index_changed_str(self, text):
    self.currentIndexChanged[str].emit(text)
  
  @pyqtSlot(int)
  def internal_combo_box_highlighted_int(self, index):
    self.highlighted[int].emit(index)
  
  @pyqtSlot(str)
  def internal_combo_box_highlighted_str(self, text):
    self.highlighted[str].emit(text)
    
  #PyQt properties (the ones that show up in designer)
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

  #PyDM widget required methods
  def channels(self):
    if self._channels is None:
      self._channels = [PyDMChannel(address=self.channel, 
                        connection_slot=self.connectionStateChanged, 
                        value_slot=self.receiveValue, 
                        severity_slot=self.alarmSeverityChanged, 
                        write_access_slot=self.writeAccessChanged, 
                        enum_strings_slot=self.enumStringsChanged, 
                        value_signal=self.valueChanged)]
    return self._channels
  