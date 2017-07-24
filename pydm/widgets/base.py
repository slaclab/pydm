from ..PyQt.QtGui import QApplication, QColor
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty
from .channel import PyDMChannel
from ..application import PyDMApplication

def compose_stylesheet(style, base_class="QWidget"):
    style_str = base_class + " {"
    for k, v in style.items():
        style_str += "{}: {}; ".format(k, v)
    style_str += "}"

    return style_str


class PyDMWidget():
    # Tell Designer what signals are available.
    __pyqtSignals__ = ("connected_signal()",
                       "disconnected_signal()",
                       "no_alarm_signal()",
                       "minor_alarm_signal()",
                       "major_alarm_signal()",
                       "invalid_alarm_signal()")

    # Internal signals, used by the state machine
    connected_signal = pyqtSignal()
    disconnected_signal = pyqtSignal()
    no_alarm_signal = pyqtSignal()
    minor_alarm_signal = pyqtSignal()
    major_alarm_signal = pyqtSignal()
    invalid_alarm_signal = pyqtSignal()

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

    def __init__(self, parent=None, init_channel=None):
        self._color = self.local_connection_status_color_map[False]
        self._channel = init_channel
        self._channels = None
        self._alarm_sensitive_content = False
        self._alarm_sensitive_border = True
        self._alarm_flags = (self.ALARM_CONTENT * self._alarm_sensitive_content) | (self.ALARM_BORDER * self._alarm_sensitive_border)
        self._alarm_state = 0
        self._style = dict()
        self._connected = False
        self._prec = 0
        self.enum_strings = None
        self.format_string = None
        # If this label is inside a PyDMApplication (not Designer) start it in the disconnected state.
        app = QApplication.instance()
        if isinstance(app, PyDMApplication):
            self.alarmSeverityChanged(self.ALARM_DISCONNECTED)

    # 0 = NO_ALARM, 1 = MINOR, 2 = MAJOR, 3 = INVALID  
    @pyqtSlot(int)
    def alarmSeverityChanged(self, new_alarm_severity):
        if self._channels is not None:
            self._alarm_state = new_alarm_severity
            self._style = dict(self.alarm_style_sheet_map[self._alarm_flags][new_alarm_severity])
            style = compose_stylesheet(style=self._style)
            self.setStyleSheet(style)
            self.update()

    # false = disconnected, true = connected
    @pyqtSlot(bool)
    def connectionStateChanged(self, connected):
        self._connected = connected
        if connected:
            self.connected_signal.emit()
        else:
            self.alarmSeverityChanged(self.ALARM_DISCONNECTED)
            self.disconnected_signal.emit()

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

    @pyqtSlot(tuple)
    def enumStringsChanged(self, enum_strings):
        if enum_strings != self.enum_strings:
            self.enum_strings = enum_strings
            self.receiveValue(self.value)

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

    @pyqtSlot()
    def force_redraw(self):
        self.update()

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
    
    def channels(self):
        if self._channels != None:
            return self._channels

        self._channels = [
            PyDMChannel(address=self.channel,
                        connection_slot=self.connectionStateChanged,
                        value_slot=self.receiveValue,
                        waveform_slot=None,
                        severity_slot=self.alarmSeverityChanged,
                        write_access_slot=None,
                        enum_strings_slot=self.enumStringsChanged,
                        unit_slot=None,
                        prec_slot=None,
                        upper_ctrl_limit_slot=None,
                        lower_ctrl_limit_slot=None,
                        value_signal=None,
                        waveform_signal=None)
        ]
        return self._channels