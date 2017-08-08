from ..PyQt.QtGui import QLabel, QApplication, QColor, QPalette, QWidget
from ..PyQt.QtCore import Qt, pyqtSignal, pyqtSlot, pyqtProperty, QState, QStateMachine, QPropertyAnimation, QByteArray
from .channel import PyDMChannel
from ..application import PyDMApplication

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
    
    def __init__(self, parent=None, init_channel=None):
        super(PyDMLabel, self).__init__(parent)
        self.setTextFormat(Qt.PlainText)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.value = None
        self._channels = None
        self._channel = init_channel
        self._user_defined_prec = False
        self._prec = 0
        self._show_units = False
        self._unit_string = ""
        self._alarm_sensitive_text = False
        self._alarm_sensitive_border = True
        self._alarm_flags = (self.ALARM_TEXT * self._alarm_sensitive_text) | (self.ALARM_BORDER * self._alarm_sensitive_border)
        self._connected = False
        self.enum_strings = None
        self.format_string = None
        self.setText("PyDMLabel")
        #If this label is inside a PyDMApplication (not Designer) start it in the disconnected state.
        app = QApplication.instance()
        if isinstance(app, PyDMApplication):
            self.alarmSeverityChanged(self.ALARM_DISCONNECTED)
    
    def redraw_label(self):
        #If the value is a string, just display it as-is, no formatting needed.
        if isinstance(self.value, str):
            self.setText(self.value)
            return
        #If the value is an enum, display the appropriate enum string for the value.
        if self.enum_strings is not None and isinstance(self.value, int):
            self.setText(self.enum_strings[self.value])
            return
        #If the value is a number (float or int), display it using a format string if necessary.
        if isinstance(self.value, float) or isinstance(self.value, int):
            if self.format_string is not None:
                self.setText(self.format_string.format(self.value))
                return
        #If you made it this far, just turn whatever the heck the value is into a string and display it.
        self.setText(str(self.value))
    
    def refresh_format_string(self):
        if self.precision == 0 and self._unit_string == "":
            self.format_string = None
            self.redraw_label()
            return
        strs = []
        if self.precision != 0:
            strs.append("{:." + str(self.precision) + "f}")
        if self._unit_string != "":
            strs.append(self._unit_string)
        self.format_string = " ".join(strs)
        self.redraw_label()
            
    @pyqtSlot(float)
    @pyqtSlot(int)
    @pyqtSlot(str)
    def receiveValue(self, new_value):
        self.value = new_value
        self.redraw_label()
        
    # -2 to +2, -2 is LOLO, -1 is LOW, 0 is OK, etc.    
    @pyqtSlot(int)
    def alarmStatusChanged(self, new_alarm_state):
        pass
    
    #0 = NO_ALARM, 1 = MINOR, 2 = MAJOR, 3 = INVALID    
    @pyqtSlot(int)
    def alarmSeverityChanged(self, new_alarm_severity):
        self.setStyleSheet(self.alarm_style_sheet_map[self._alarm_flags][new_alarm_severity])
        
    #false = disconnected, true = connected
    @pyqtSlot(bool)
    def connectionStateChanged(self, connected):
        self._connected = connected
        if connected:
            self.connected_signal.emit()
        else:
            self.alarmSeverityChanged(self.ALARM_DISCONNECTED)
            self.disconnected_signal.emit()
    
    @pyqtSlot(tuple)
    def enumStringsChanged(self, enum_strings):
        if enum_strings != self.enum_strings:
            self.enum_strings = enum_strings
            self.redraw_label()
    
    @pyqtSlot(int)
    def precisionChanged(self, new_prec):
        if not self._user_defined_prec:
            self.precision = new_prec
            self.refresh_format_string()
    
    @pyqtSlot(str)
    def unitsChanged(self, new_units):
        self._unit_string = str(new_units)
        self.refresh_format_string()
    
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
    
    @pyqtProperty(bool)
    def userDefinedPrecision(self):
        return self._user_defined_prec
    
    @userDefinedPrecision.setter
    def userDefinedPrecision(self, user_defined_prec):
        self._user_defined_prec = user_defined_prec
    
    @pyqtProperty(bool)
    def showUnits(self):
        return self._show_units
    
    @showUnits.setter
    def showUnits(self, show_units):
        self._show_units = show_units
        self.refresh_format_string()
    
    def getPrecision(self):
        return self._prec
    
    def setPrecision(self, new_prec):
        if self._prec != int(new_prec) and new_prec >= 0:
            self._prec = int(new_prec)
            self.refresh_format_string()
            
    def resetPrecision(self):
        if self._prec != 0:
            self._prec = 0
            self.refresh_format_string()
            
    precision = pyqtProperty("int", getPrecision, setPrecision, resetPrecision)

    def channels(self):
        if self._channels != None:
            return self._channels
        self._channels = [PyDMChannel(address=self.channel, connection_slot=self.connectionStateChanged, value_slot=self.receiveValue, severity_slot=self.alarmSeverityChanged, enum_strings_slot=self.enumStringsChanged, prec_slot=self.precisionChanged, unit_slot=self.unitsChanged)]
        return self._channels
