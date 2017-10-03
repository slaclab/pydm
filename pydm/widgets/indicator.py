from ..PyQt.QtGui import QWidget, QApplication, QColor, QPainter, QBrush, QPen
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QState, QStateMachine, QPropertyAnimation, Qt, QByteArray
from .channel import PyDMChannel
import warnings

class PyDMIndicator(QWidget):
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

    # Usually, this widget will get this from its parent pydm application.  However, in Designer, the parent isnt a pydm application, and doesn't know what a color map is.  The following two color maps are provided for that scenario.
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

    def __init__(self, parent=None, init_channel=None):
        warnings.warn("PyDMIndicator is deprecated. Please replace it with"
                      " PyDMDrawingRectangle. PyDMIndicator will be removed"
                      " on the next release.")
        self._color = self.local_connection_status_color_map[False]
        self._border_thickness = 0
        self._border_color = QColor(0, 0, 0)
        self._has_border = False
        self.painter = QPainter()
        self.brush = QBrush(self._color)
        self.pen = QPen(Qt.NoPen)
        super(PyDMIndicator, self).__init__(parent)
        self.setup_state_machine()
        self._channel = init_channel


    # Can the state machine be implemented at a lower level, like a QWidget subclass?
    def setup_state_machine(self):
        self.state_machine = QStateMachine(self)

        # We'll need to talk to the parent application to figure out what colors to use for a specific state.    If the parent application doesn't have a color map (this is true when we are in Designer) then use the local colors defined above.
        app = QApplication.instance()
        try:
            connection_status_color_map = app.connection_status_color_map
            alarm_severity_color_map = app.alarm_severity_color_map
        except AttributeError:
            connection_status_color_map = self.local_connection_status_color_map
            alarm_severity_color_map = self.local_alarm_severity_color_map

        # There are two connection states: Disconnected, and Connected.
        disconnected_state = QState(self.state_machine)
        disconnected_state.assignProperty(self, "color", connection_status_color_map[False])
        # connected_state is parallel because it will have sub-states for alarm severity.
        connected_state = QState(self.state_machine)
        # connected_state itself doesn't have any particular color, that is all defined by the alarm severity.

        self.state_machine.setInitialState(disconnected_state)

        disconnected_state.addTransition(self.connected_signal, connected_state)
        connected_state.addTransition(self.disconnected_signal, disconnected_state)

        # Now lets add the alarm severity states.
        no_alarm_state = QState(connected_state)
        no_alarm_state.assignProperty(self, "color", alarm_severity_color_map[0])
        minor_alarm_state = QState(connected_state)
        minor_alarm_state.assignProperty(self, "color", alarm_severity_color_map[1])
        major_alarm_state = QState(connected_state)
        major_alarm_state.assignProperty(self, "color", alarm_severity_color_map[2])
        invalid_alarm_state = QState(connected_state)
        invalid_alarm_state.assignProperty(self, "color", alarm_severity_color_map[3])
        connected_state.setInitialState(no_alarm_state)

        # Add the transitions between different severities.
        # This is a bunch, since any severity can transition to any other.
        no_alarm_state.addTransition(self.minor_alarm_signal, minor_alarm_state)
        no_alarm_state.addTransition(self.major_alarm_signal, major_alarm_state)
        no_alarm_state.addTransition(self.invalid_alarm_signal, invalid_alarm_state)
        minor_alarm_state.addTransition(self.no_alarm_signal, no_alarm_state)
        minor_alarm_state.addTransition(self.major_alarm_signal, major_alarm_state)
        minor_alarm_state.addTransition(self.invalid_alarm_signal, invalid_alarm_state)
        major_alarm_state.addTransition(self.no_alarm_signal, no_alarm_state)
        major_alarm_state.addTransition(self.minor_alarm_signal, minor_alarm_state)
        major_alarm_state.addTransition(self.invalid_alarm_signal, invalid_alarm_state)
        invalid_alarm_state.addTransition(self.no_alarm_signal, no_alarm_state)
        invalid_alarm_state.addTransition(self.minor_alarm_signal, minor_alarm_state)
        invalid_alarm_state.addTransition(self.major_alarm_signal, major_alarm_state)

        # Add a cool fade animation to a state transition.
        self.color_fade = QPropertyAnimation(self, QByteArray(b'color'), self)
        self.color_fade.setDuration(175)
        self.color_fade.valueChanged.connect(self.force_redraw)
        self.state_machine.addDefaultAnimation(self.color_fade)
        self.state_machine.start()

    # 0 = NO_ALARM, 1 = MINOR, 2 = MAJOR, 3 = INVALID
    @pyqtSlot(int)
    def alarmSeverityChanged(self, new_alarm_severity):
        if new_alarm_severity == 0:
            self.no_alarm_signal.emit()
        elif new_alarm_severity == 1:
            self.minor_alarm_signal.emit()
        elif new_alarm_severity == 2:
            self.major_alarm_signal.emit()
        elif new_alarm_severity == 3:
            self.invalid_alarm_signal.emit()

    # false = disconnected, true = connected
    @pyqtSlot(bool)
    def connectionStateChanged(self, connected):
        if connected:
            self.connected_signal.emit()
        else:
            self.disconnected_signal.emit()

    @pyqtSlot()
    def force_redraw(self):
        self.update()

    def paintEvent(self, event):
        self.painter.begin(self)
        self.painter.setBrush(self.brush)
        self.painter.setPen(self.pen)
        self.painter.drawRect(0, 0, self.width(), self.height())
        self.painter.end()

    # Define setter and getter for the "color" property, used by the state machine to change color based on alarm severity and connection.
    def getColor(self):
        return self._color

    def setColor(self, new_color):
        if new_color != self._color:
            old_alpha = self.brush.color().alphaF()
            new_color.setAlphaF(old_alpha)
            self._color = new_color
            self.brush.setColor(self._color)

    color = pyqtProperty(QColor, getColor, setColor)

    def getBorderColor(self):
        return self._border_color

    def setBorderColor(self, new_color):
        if new_color != self._border_color:
            self._border_color = new_color
            self.pen.setColor(new_color)

    def resetBorderColor(self):
        self._border_color = QColor(0, 0, 0)

    border_color = pyqtProperty(QColor, getBorderColor, setBorderColor, resetBorderColor)

    def getBorderThickness(self):
        return self._border_thickness

    def setBorderThickness(self, new_thickness):
        if new_thickness != self._border_thickness:
            self._border_thickness = new_thickness
            self.pen.setWidth(self._border_thickness)
            self.update()

    def resetBorderThickness(self):
        self._border_thickness = 0.0
        self.pen.setWidth(self._border_thickness)
        self.update()

    border_thickness = pyqtProperty(float, getBorderThickness, setBorderThickness, resetBorderThickness)

    def getHasBorder(self):
        return self._has_border

    def setHasBorder(self, val):
        self._has_border = val
        if self._has_border:
            self.pen = QPen(QBrush(self.getBorderColor()), self.getBorderThickness())
        else:
            self.pen = QPen(Qt.NoPen)
        self.update()

    def resetHasBorder(self):
        if self._has_border:
            self._has_border = False
            self.pen = QPen(Qt.NoPen)
            self.update()

    has_border = pyqtProperty(bool, getHasBorder, setHasBorder)

    def getChannel(self):
        return str(self._channel)

    def setChannel(self, value):
        if self._channel != value:
            self._channel = str(value)

    def resetChannel(self):
        if self._channel is not None:
            self._channel = None

    channel = pyqtProperty(str, getChannel, setChannel, resetChannel)

    def channels(self):
        return [PyDMChannel(address=self.channel, connection_slot=self.connectionStateChanged, severity_slot=self.alarmSeverityChanged)]
