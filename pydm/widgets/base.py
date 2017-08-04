import numpy as np
from ..PyQt.QtGui import QApplication, QColor, QCursor
from ..PyQt.QtCore import Qt, pyqtSignal, pyqtSlot, pyqtProperty
from .channel import PyDMChannel
from ..application import PyDMApplication

def compose_stylesheet(style, base_class="QWidget"):
    """
    Creates a stylesheet string for a base class from a dictionary.
    
    Parameters
    ----------
    style : dict
        A dictionary with key being the property and value being the property value to compose the stylesheet
    base_class : str, optional
        The QT base class to apply this stylesheet. Default: "QWidget"
    
    Returns
    -------
    style_str : str
        The composed stylesheet with the proper base class.        
    """
    style_str = base_class + " {"
    for k, v in style.items():
        style_str += "{}: {}; ".format(k, v)
    style_str += "}"

    return style_str


class PyDMWidget():
    __pyqtSignals__ = ("send_value_signal(str)")
    
    # Emitted when the user changes the value.
    send_value_signal = pyqtSignal(str)
    
    # Usually, this widget will get this from its parent pydm application.  
    # However, in Designer, the parent isnt a pydm application, and doesn't know what a color map is.
    # The following two color maps are provided for that scenario.
    local_alarm_severity_color_map = {
        0: QColor(0, 0, 0),  # NO_ALARM
        1: QColor(200, 200, 20),  # MINOR_ALARM
        2: QColor(240, 0, 0),  # MAJOR_ALARM
        3: QColor(240, 0, 240)  # INVALID_ALARM
    }
    local_connection_status_color_map = {
        False: QColor(0, 0, 0),
        True: QColor(0, 0, 0,)
    }
    
    NO_ALARM = 0x0
    ALARM_CONTENT = 0x1
    ALARM_BORDER = 0x2
    
    ALARM_NONE = 0
    ALARM_MINOR = 1
    ALARM_MAJOR = 2
    ALARM_INVALID = 3
    ALARM_DISCONNECTED = 4
    
    # We put all this in a big dictionary to try to avoid constantly allocating and deallocating new stylesheet strings.
    alarm_style_sheet_map = {
        NO_ALARM: {
            ALARM_NONE: {},
            ALARM_MINOR: {},
            ALARM_MAJOR: {},
            ALARM_INVALID: {},
            ALARM_DISCONNECTED: {}
        },
        ALARM_CONTENT: {
            ALARM_NONE: {"color": "black"},
            ALARM_MINOR: {"color": "yellow"},
            ALARM_MAJOR: {"color": "red"},
            ALARM_INVALID: {"color": "purple"},
            ALARM_DISCONNECTED: {"color": "white"}
        },
        ALARM_BORDER: {
            ALARM_NONE: {"border-width": "2px", "border-style": "hidden"},
            ALARM_MINOR: {"border": "2px solid yellow"},
            ALARM_MAJOR: {"border": "2px solid red"},
            ALARM_INVALID: {"border": "2px solid purple"},
            ALARM_DISCONNECTED: {"border": "2px solid white"}
        },
        ALARM_CONTENT | ALARM_BORDER: {
            ALARM_NONE: {"color": "black", "border-width": "2px", "border-style": "hidden"},
            ALARM_MINOR: {"color": "yellow", "border": "2px solid yellow"},
            ALARM_MAJOR: {"color": "red", "border": "2px solid red"},
            ALARM_INVALID: {"color": "purple", "border": "2px solid purple"},
            ALARM_DISCONNECTED: {"color": "white", "border": "2px solid white"}
        }
    }

    def __init__(self, init_channel=None):
        self._color = self.local_connection_status_color_map[False]
        self._channel = init_channel
        self._channels = None
        self._alarm_sensitive_content = False
        self._alarm_sensitive_border = True
        self._alarm_flags = (self.ALARM_CONTENT * self._alarm_sensitive_content) | (self.ALARM_BORDER * self._alarm_sensitive_border)
        self._alarm_state = 0
        self._style = dict()
        self._connected = False
        self._write_access = False
        self._prec = 0
        self._unit = ""
        
        self._upper_ctrl_limit = None
        self._lower_ctrl_limit = None
        
        self.enum_strings = None
        self.format_string = None
        
        self.value = None
        
        self._value_signal = None
        self._connection_changed = None
        self._value_changed = None
        self._alarm_severity_changed = None
        self._write_access_changed = None
        self._enum_strings_changed = None
        self._unit_changed = None
        self._precision_changed = None
        self._ctrl_limit_changed = None        
        
        # If this label is inside a PyDMApplication (not Designer) start it in the disconnected state.
        app = QApplication.instance()
        if isinstance(app, PyDMApplication):
            self.alarmSeverityChanged(self.ALARM_DISCONNECTED)

    """
    CALLBACK PROPERTIES
    """
    @property
    def value_signal(self):
        return self._value_signal
    
    @value_signal.setter
    def value_signal(self, callback):
        if self._value_signal != callback:
            self._value_signal = callback

    @property
    def connection_changed(self):
        return self._connection_changed
    
    @connection_changed.setter
    def connection_changed(self, callback):
        if self._connection_changed != callback:
            self._connection_changed = callback

    @property
    def value_changed(self):
        return self._value_changed
    
    @value_changed.setter
    def value_changed(self, callback):
        if self._value_changed != callback:
            self._value_changed = callback

    @property
    def alarm_severity_changed(self):
        return self._alarm_severity_changed
    
    @alarm_severity_changed.setter
    def alarm_severity_changed(self, callback):
        if self._alarm_severity_changed != callback:
            self._alarm_severity_changed = callback
    
    @property
    def write_access_changed(self):
        return self._write_access_changed
    
    @write_access_changed.setter
    def write_access_changed(self, callback):
        if self._write_access_changed != callback:
            self._write_access_changed = callback
    
    @property
    def enum_strings_changed(self):
        return self._write_access_changed
    
    @enum_strings_changed.setter
    def enum_strings_changed(self, callback):
        if self._enum_strings_changed != callback:
            self._enum_strings_changed = callback
    
    @property
    def unit_changed(self):
        return self._unit_changed
    
    @unit_changed.setter
    def unit_changed(self, callback):
        if self._unit_changed != callback:
            self._unit_changed = callback

    @property
    def precision_changed(self):
        return self._precision_changed
    
    @precision_changed.setter
    def precision_changed(self, callback):
        if self._precision_changed != callback:
            self._precision_changed = callback

    @property
    def ctrl_limit_changed(self):
        return self._ctrl_limit_changed
    
    @ctrl_limit_changed.setter
    def ctrl_limit_changed(self, callback):
        if self._ctrl_limit_changed != callback:
            self._ctrl_limit_changed = callback

    """
    QT SLOTS
    """
    # false = disconnected, true = connected
    @pyqtSlot(bool)
    def connectionStateChanged(self, connected):
        print("Connection state changed...")
        self._connected = connected
        self.checkEnableState()
        if not connected:
            self.alarmSeverityChanged(self.ALARM_DISCONNECTED)
        if self._connection_changed is not None:
            self._connection_changed(connected)
    
    @pyqtSlot(int)
    @pyqtSlot(float)
    @pyqtSlot(str)
    @pyqtSlot(bool)
    @pyqtSlot(np.ndarray)
    def valueChanged(self, new_val):
        self.value = new_val
        if self._value_changed is not None:
            self._value_changed(new_val)

    @pyqtSlot(int)
    def alarmSeverityChanged(self, new_alarm_severity):
        # 0 = NO_ALARM, 1 = MINOR, 2 = MAJOR, 3 = INVALID
        if self._channels is not None:
            self._alarm_state = new_alarm_severity
            self._style = dict(self.alarm_style_sheet_map[self._alarm_flags][new_alarm_severity])
            style = compose_stylesheet(style=self._style)
            self.setStyleSheet(style)
            self.update()
            if self._alarm_severity_changed is not None:
                self._alarm_severity_changed(new_alarm_severity)


    @pyqtSlot(tuple)
    def enumStringsChanged(self, enum_strings):
        if enum_strings != self.enum_strings:
            self.enum_strings = enum_strings
            self.valueChanged(self.value)
            if self._enum_strings_changed is not None:
                self._enum_strings_changed(enum_strings)

    @pyqtSlot(bool)
    def writeAccessChanged(self, write_access):
        self._write_access = write_access
        self.checkEnableState()
        if self._write_access_changed is not None:
            self._write_access_changed(write_access)

    @pyqtSlot(str)
    def unitChanged(self, unit):
        if self._unit_changed is not None:
            self._unit_changed(unit)

    @pyqtSlot(int)
    @pyqtSlot(float)
    def precisionChanged(self, prec):
        self._prec = prec
        if self._precision_changed is not None:
            self._precision_changed(prec)

    @pyqtSlot(float)
    def upperCtrlLimitChanged(self, limit):
        self._upper_ctrl_limit = limit
        if self._ctrl_limit_changed is not None:
            self._ctrl_limit_changed("UPPER", limit)

    @pyqtSlot(float)
    def lowerCtrlLimitChanged(self, limit):
        self._lower_ctrl_limit = limit
        if self._ctrl_limit_changed is not None:
            self._ctrl_limit_changed("UPPER", limit)


    @pyqtSlot()
    def force_redraw(self):
        self.update()
    
    """
    PYQT PROPERTIES
    """
    @pyqtProperty(bool, doc=
    """
    Whether or not the content color changes when alarm severity changes.
    """
    )
    def alarmSensitiveContent(self):
        return self._alarm_sensitive_content

    @alarmSensitiveContent.setter
    def alarmSensitiveContent(self, checked):
        self._alarm_sensitive_content = checked
        self._alarm_flags = (self.ALARM_CONTENT * self._alarm_sensitive_content) | (self.ALARM_BORDER * self._alarm_sensitive_border)

    @pyqtProperty(bool, doc=
    """
    Whether or not the border color changes when alarm severity changes.
    """
    )
    def alarmSensitiveBorder(self):
        return self._alarm_sensitive_border

    @alarmSensitiveBorder.setter
    def alarmSensitiveBorder(self, checked):
        self._alarm_sensitive_border = checked
        self._alarm_flags = (self.ALARM_CONTENT * self._alarm_sensitive_content) | (self.ALARM_BORDER * self._alarm_sensitive_border)

    @pyqtProperty(int, doc=
    """The precision to be used when formatting the output
    of the PV"""
    )
    def precision(self):
        return self._prec

    @precision.setter
    def precision(self, new_prec):
        if self._prec != int(new_prec) and new_prec >= 0:
            self._prec = int(new_prec)
            self.format_string = "{:." + str(self._prec) + "f}"

    @pyqtProperty(str, doc=
    """
    The channel to be used 
    """
    )
    def channel(self):
        return str(self._channel)

    @channel.setter  
    def channel(self, value):
        if self._channel != value:
            self._channel = str(value)
        
        
    """
    PyDMWidget methods
    """
    def checkEnableState(self):
        status = self._write_access and self._connected
        if status:
            self.setCursor(QCursor(Qt.ArrowCursor))
        else:
            self.setCursor(QCursor(Qt.ForbiddenCursor))
        #self.setEnabled(status)
    
    def get_ctrl_limits(self):
        return (self._lower_ctrl_limit, self._upper_ctrl_limit)
    
    def channels(self):
        if self._channels != None:
            return self._channels

        self._channels = [
            PyDMChannel(address=self.channel,
                        connection_slot=self.connectionStateChanged,
                        value_slot=self.valueChanged,
                        waveform_slot=self.valueChanged,
                        severity_slot=self.alarmSeverityChanged,
                        enum_strings_slot=self.enumStringsChanged,
                        unit_slot=self.unitChanged,
                        prec_slot=self.precisionChanged,
                        upper_ctrl_limit_slot=self.upperCtrlLimitChanged,
                        lower_ctrl_limit_slot=self.lowerCtrlLimitChanged,
                        value_signal=self.send_value_signal,
                        waveform_signal=self.send_value_signal,
                        write_access_slot=self.writeAccessChanged)
        ]
        return self._channels
