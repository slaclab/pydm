import numpy as np
from ..PyQt.QtGui import QApplication, QColor, QCursor
from ..PyQt.QtCore import Qt, QEvent, pyqtSignal, pyqtSlot, pyqtProperty
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


class PyDMPrimitiveWidget():
    """
    Primitive class that determines that a given widget is a PyDMWidget.
    All Widget classes from PyDMWidget will be True for isinstance(obj, PyDMPrimitiveWidget)
    """
    pass

class PyDMWidget(PyDMPrimitiveWidget):
    """
    PyDM base class for Read-Only widgets.
    This class implements all the functions of connection, alarm handling and more.
    
    Parameters
    ----------
    init_channel : str
        The channel to be used by the widget.
        
    """
    
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
        self._show_units = False
        self._alarm_sensitive_content = False
        self._alarm_sensitive_border = True
        self._alarm_flags = (self.ALARM_CONTENT * self._alarm_sensitive_content) | (self.ALARM_BORDER * self._alarm_sensitive_border)
        self._alarm_state = 0
        self._style = dict()
        self._connected = False
    
        self._precision_from_pv = True
        self._prec = 0
        self._unit = ""
        
        self._upper_ctrl_limit = None
        self._lower_ctrl_limit = None

        self.enum_strings = None
        self.format_string = "{}"
        
        self.value = None   
        
        # If this label is inside a PyDMApplication (not Designer) start it in the disconnected state.
        app = QApplication.instance()
        if isinstance(app, PyDMApplication):
            self.alarmSeverityChanged(self.ALARM_DISCONNECTED)
            
    """
    CALLBACKS
    """
    def connection_changed(self, connected):
        """
        Callback invoked when the connection state of the Channel is changed.
        This callback acts on the connection state to enable/disable the widget
        and also trigger the change on alarm severity to ALARM_DISCONNECTED.
        
        Params
        ------
        connected : int
            When this value is 0 the channel is disconnected, 1 otherwise.
        """    
        self._connected = connected
        self.check_enable_state()
        if not connected:
            self.alarmSeverityChanged(self.ALARM_DISCONNECTED)        

    def value_changed(self, new_val):
        """
        Callback invoked when the Channel value is changed.
        
        Params
        ------
        new_val : str, int, float, bool or np.ndarray
            The new value from the channel. The type depends on the channel.
        """
        self.value = new_val

    def alarm_severity_changed(self, new_alarm_severity):
        """
        Callback invoked when the Channel alarm severity is changed.
        This callback is not processed if the widget has no channel associated with it.
        This callback handles the composition of the stylesheet to be applied and the call
        to update to redraw the widget with the needed changes for the new state.
        
        Params:
        new_alarm_severity : int
            The new severity where 0 = NO_ALARM, 1 = MINOR, 2 = MAJOR and 3 = INVALID
        """
        # 0 = NO_ALARM, 1 = MINOR, 2 = MAJOR, 3 = INVALID
        if self._channels is not None:
            self._alarm_state = new_alarm_severity
            self._style = dict(self.alarm_style_sheet_map[self._alarm_flags][new_alarm_severity])
            style = compose_stylesheet(style=self._style)
            self.setStyleSheet(style)
            self.update()
    
    def enum_strings_changed(self, new_enum_strings):
        if new_enum_strings != self.enum_strings:
            self.enum_strings = new_enum_strings
            self.value_changed(self.value)
    
    def unit_changed(self, new_unit):
        if self._unit != new_unit:
            self._unit = new_unit
            self.update_format_string()

    def precision_changed(self, new_precision):
        if self._precision_from_pv:
            self._prec = new_precision
            self.update_format_string()

    def ctrl_limit_changed(self, which, new_limit):
        if which == "UPPER":
            self._upper_ctrl_limit = new_limit
        else:
            self._lower_ctrl_limit = new_limit

    """
    QT SLOTS
    """
    @pyqtSlot(bool)
    def connectionStateChanged(self, connected):
        # false = disconnected, true = connected
        self.connection_changed(connected)
    
    @pyqtSlot(int)
    @pyqtSlot(float)
    @pyqtSlot(str)
    @pyqtSlot(bool)
    @pyqtSlot(np.ndarray)
    def valueChanged(self, new_val):
        self.value_changed(new_val)

    @pyqtSlot(int)
    def alarmSeverityChanged(self, new_alarm_severity):
        self.alarm_severity_changed(new_alarm_severity)

    @pyqtSlot(tuple)
    def enumStringsChanged(self, enum_strings):
        self.enum_strings_changed(enum_strings)

    @pyqtSlot(str)
    def unitChanged(self, unit):
        self.unit_changed(unit)

    @pyqtSlot(int)
    @pyqtSlot(float)
    def precisionChanged(self, prec):
        self.precision_changed(prec)

    @pyqtSlot(float)
    def upperCtrlLimitChanged(self, limit):
        self.ctrl_limit_changed("UPPER", limit)

    @pyqtSlot(float)
    def lowerCtrlLimitChanged(self, limit):
        self.ctrl_limit_changed("LOWER", limit)

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

    @pyqtProperty(bool, doc=
    """Wether or not to use the precision information from the PV"""
    )
    def precisionFromPV(self):
        return self._precision_from_pv

    @precisionFromPV.setter
    def precisionFromPV(self, value):
        if self._precision_from_pv != bool(value):
            self._precision_from_pv = value

    @pyqtProperty(int, doc=
    """The precision to be used when formatting the output
    of the PV"""
    )
    def precision(self):
        return self._prec

    @precision.setter
    def precision(self, new_prec):
        # Only allow one to change the property if not getting the precision from the PV    
        if self._precision_from_pv:
            return
        if self._prec != int(new_prec) and new_prec >= 0:
            self._prec = int(new_prec)
            self.update_format_string()

    @pyqtProperty(bool)
    def showUnits(self):
        return self._show_units
    
    @showUnits.setter
    def showUnits(self, show_units):
        if self._show_units != show_units:
            self._show_units = show_units
            self.update_format_string()

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
    def update_format_string(self):
        self.format_string = "{}"
        if isinstance(self.value, (int, float)):
            self.format_string = "{:." + str(self._prec) + "f}"
        if self._show_units and self._unit != "":
            self.format_string += " {}".format(self._unit)
        return self.format_string
    
    def check_enable_state(self):
        status = self._connected
        tooltip = ""
        if not status:
            tooltip = "PV is disconnected."

        self.setToolTip(tooltip)
        self.setEnabled(status)
    
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
                        value_signal=None,
                        waveform_signal=None,
                        write_access_slot=None)
        ]
        return self._channels

class PyDMWritableWidget(PyDMWidget):
    """
    PyDM base class for Writable widgets.
    This class implements the send_value_signal and also the event filter for write access changes on PVs.

    
    Parameters
    ----------
    init_channel : str
        The channel to be used by the widget.
        
    """
    
    __pyqtSignals__ = ("send_value_signal([int], [float], [str], [bool], [np.ndarray])")
        
    # Emitted when the user changes the value.
    send_value_signal = pyqtSignal([int], [float], [str], [bool], [np.ndarray])
    
    def __init__(self, init_channel=None):
        super().__init__(init_channel=init_channel)
        self._write_access = False            
        self.installEventFilter(self)

    """
    EVENT FILTER
    """
    def eventFilter(self, object, event):
        """
        Filters events on this object.
        
        Params
        ------
        object : QObject
            The object that is being handled. 
        event : QEvent
            The event that is happening.
        
        Returns
        -------
        bool : True to stop the event from being handled further; otherwise return false.
        
        """
        status = self._write_access and self._connected
        
        if event.type() == QEvent.Leave:
            QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
            return True
            
        if event.type() == QEvent.Enter and not status:
            QApplication.setOverrideCursor(QCursor(Qt.ForbiddenCursor))
            return True
        
        return False

    """
    CALLBACKS
    """
    def write_access_changed(self, new_write_access):
        self._write_access = new_write_access
        self.check_enable_state()
    

    """
    QT SLOTS
    """
    @pyqtSlot(bool)
    def writeAccessChanged(self, write_access):
        self.write_access_changed(write_access)

    
    def check_enable_state(self):
        status = self._write_access and self._connected
        tooltip = ""
        if not self._connected:
            tooltip += "PV is disconnected."
        else:
            if not self._write_access:
                tooltip += "Access denied by Channel Access Security."
        self.setToolTip(tooltip)
        self.setEnabled(status)
        
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
