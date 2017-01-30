from ..PyQt.QtGui import QLabel, QApplication, QColor, QPalette, QWidget
from ..PyQt.QtCore import Qt, pyqtSignal, pyqtSlot, pyqtProperty, QState, QStateMachine, QPropertyAnimation
from .channel import PyDMChannel
class PyDMLabel(QLabel):
  #Tell Designer what signals are available.
  __pyqtSignals__ = ("send_value_signal(str)",
                     "connected_signal()",
                     "disconnected_signal()", 
                     "no_alarm_signal()", 
                     "minor_alarm_signal()", 
                     "major_alarm_signal()", 
                     "invalid_alarm_signal()")
  
  #Internal signals, used by the state machine
  connected_signal = pyqtSignal()
  disconnected_signal = pyqtSignal()
  no_alarm_signal = pyqtSignal()
  minor_alarm_signal = pyqtSignal()
  major_alarm_signal = pyqtSignal()
  invalid_alarm_signal = pyqtSignal()
  
  #Usually, this widget will get this from its parent pydm application.  However, in Designer, the parent isnt a pydm application, and doesn't know what a color map is.  The following two color maps are provided for that scenario.
  local_alarm_severity_color_map = {
    0: QColor(0, 0, 0), #NO_ALARM
    1: QColor(200, 200, 20), #MINOR_ALARM
    2: QColor(240, 0, 0), #MAJOR_ALARM
    3: QColor(240, 0, 240) #INVALID_ALARM
  }
  local_connection_status_color_map = {
    False: QColor(0, 0, 0),
    True: QColor(0, 0, 0,)
  }
  
  NO_ALARM = 0x0
  ALARM_TEXT = 0x1
  ALARM_BORDER = 0x2
  
  ALARM_NONE = 0
  ALARM_MINOR = 1
  ALARM_MAJOR = 2
  ALARM_INVALID = 3
  ALARM_DISCONNECTED = 4
  
  #We put all this in a big dictionary to try to avoid constantly allocating and deallocating new stylesheet strings.
  alarm_style_sheet_map = {
    NO_ALARM: {
      ALARM_NONE: "PyDMLabel {}",
      ALARM_MINOR: "PyDMLabel {}",
      ALARM_MAJOR: "PyDMLabel {}",
      ALARM_INVALID: "PyDMLabel {}",
      ALARM_DISCONNECTED: "PyDMLabel {}"
    },
    ALARM_TEXT: {
      ALARM_NONE: "PyDMLabel {color: black;}",
      ALARM_MINOR: "PyDMLabel {color: yellow;}",
      ALARM_MAJOR: "PyDMLabel {color: red;}",
      ALARM_INVALID: "PyDMLabel {color: purple;}",
      ALARM_DISCONNECTED: "PyDMLabel {color: white;}"
    },
    ALARM_BORDER: {
      ALARM_NONE: "PyDMLabel {border-width: 2px; border-style: hidden;}",
      ALARM_MINOR: "PyDMLabel {border: 2px solid yellow;}",
      ALARM_MAJOR: "PyDMLabel {border: 2px solid red;}",
      ALARM_INVALID: "PyDMLabel {border: 2px solid purple;}",
      ALARM_DISCONNECTED: "PyDMLabel {border: 2px solid white;}"
    },
    ALARM_TEXT | ALARM_BORDER: {
      ALARM_NONE: "PyDMLabel {color: black; border-width: 2px; border-style: hidden;}",
      ALARM_MINOR: "PyDMLabel {color: yellow; border: 2px solid yellow;}",
      ALARM_MAJOR: "PyDMLabel {color: red; border: 2px solid red;}",
      ALARM_INVALID: "PyDMLabel {color: purple; border: 2px solid purple;}",
      ALARM_DISCONNECTED: "PyDMLabel {color: white; border: 2px solid white;}"
    }
  }
  
  def __init__(self, init_channel=None, parent=None):
    super(PyDMLabel, self).__init__(parent)
    self.setTextFormat(Qt.PlainText)
    self.setTextInteractionFlags(Qt.NoTextInteraction)
    self.value = None
    self._channels = None
    self._channel = init_channel
    self._prec = 0
    self._alarm_sensitive_text = False
    self._alarm_sensitive_border = True
    self._alarm_flags = (self.ALARM_TEXT * self._alarm_sensitive_text) | (self.ALARM_BORDER * self._alarm_sensitive_border)
    self._connected = False
    self.enum_strings = None
    self.format_string = None
    self.setText("PyDMLabel")
    self.alarmSeverityChanged(self.ALARM_DISCONNECTED)
        
  @pyqtSlot(float)
  @pyqtSlot(int)
  @pyqtSlot(str)
  def receiveValue(self, new_value):
    self.value = new_value
    if isinstance(new_value, str):
      self.setText(new_value)
      return
    if isinstance(new_value, float):
      if self.format_string:
        self.setText(self.format_string.format(new_value))
        return
    if self.enum_strings is not None and isinstance(new_value, int):
      self.setText(self.enum_strings[new_value])
      return
    self.setText(str(new_value))
    
  # -2 to +2, -2 is LOLO, -1 is LOW, 0 is OK, etc.  
  @pyqtSlot(int)
  def alarmStatusChanged(self, new_alarm_state):
    pass
  
  @pyqtSlot(int)
  def alarmSeverityChanged(self, new_alarm_severity):
    if not self._connected:
      new_alarm_severity = self.ALARM_DISCONNECTED
    self.setStyleSheet(self.alarm_style_sheet_map[self._alarm_flags][new_alarm_severity])
    
  #false = disconnected, true = connected
  @pyqtSlot(bool)
  def connectionStateChanged(self, connected):
    self._connected = connected
    if connected:
      self.connected_signal.emit()
    else:
      self.disconnected_signal.emit()
  
  @pyqtSlot(tuple)
  def enumStringsChanged(self, enum_strings):
    if enum_strings != self.enum_strings:
      self.enum_strings = enum_strings
      self.receiveValue(self.value)
  
  @pyqtProperty(bool, doc=
  """
  Whether or not the label's text color changes when alarm severity changes.
  """
  )
  def alarmSensitiveText(self):
    return self._alarm_sensitive_text
    
  @alarmSensitiveText.setter
  def alarmSensitiveText(self, checked):
    self._alarm_sensitive_text = checked
    self._alarm_flags = (self.ALARM_TEXT * self._alarm_sensitive_text) | (self.ALARM_BORDER * self._alarm_sensitive_border)
  
  @pyqtProperty(bool, doc=
  """
  Whether or not the label's border color changes when alarm severity changes.
  """
  )
  def alarmSensitiveBorder(self):
    return self._alarm_sensitive_border
    
  @alarmSensitiveBorder.setter
  def alarmSensitiveBorder(self, checked):
    self._alarm_sensitive_border = checked
    self._alarm_flags = (self.ALARM_TEXT * self._alarm_sensitive_text) | (self.ALARM_BORDER * self._alarm_sensitive_border)
  
  def getChannel(self):
    return str(self._channel)
  
  def setChannel(self, value):
    if self._channel != value:
      self._channel = str(value)

  def resetChannel(self):
    if self._channel != None:
      self._channel = None
    
  channel = pyqtProperty(str, getChannel, setChannel, resetChannel)
  
  def getPrecision(self):
    return self._prec
  
  def setPrecision(self, new_prec):
    if self._prec != int(new_prec) and new_prec >= 0:
      self._prec = int(new_prec)
      self.format_string = "{:." + str(self._prec) + "f}"
      
  def resetPrecision(self):
    if self._prec != 0:
      self._prec = 0
      self.format_string = None
      
  precision = pyqtProperty("int", getPrecision, setPrecision, resetPrecision)

  def channels(self):
    if self._channels != None:
      return self._channels
    self._channels = [PyDMChannel(address=self.channel, connection_slot=self.connectionStateChanged, value_slot=self.receiveValue, severity_slot=self.alarmSeverityChanged, enum_strings_slot=self.enumStringsChanged)]
    return self._channels