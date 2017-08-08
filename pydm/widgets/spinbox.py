from ..PyQt.QtGui import QDoubleSpinBox
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QEvent, Qt
from .channel import PyDMChannel

class PyDMSpinbox(QDoubleSpinBox):
    __pyqtSignals__ = ("send_value_signal(float)",
                       "connected_signal()",
                       "disconnected_signal()",
                       "no_alarm_signal()",
                       "minor_alarm_signal()",
                       "major_alarm_signal()",
                       "invalid_alarm_signal()")

    #Emitted when the user changes the value.
    send_value_signal = pyqtSignal(float)

    def __init__(self, parent=None, channel=None):
        super(PyDMSpinbox, self).__init__(parent)
        self._channel = channel
        self._connected = False
        self._write_access = False
        self.setEnabled(False)

        self.valueChanged.connect(self.sendValue)
        self._units = None
        self.valueBeingSet = False

        self._show_step_exponent = True
        self.step_exponent = 0

        self._prec = 5
        self.setDecimals(self._prec)

    ### START: Left, right Arrow: changing stepsize

    def event(self, event):
        if (event.type()==QEvent.KeyPress) and (event.key()== Qt.Key_Left):
            self.step_exponent = self.step_exponent + 1
            self.update_step_size()
            return True

        if (event.type()==QEvent.KeyPress) and (event.key()== Qt.Key_Right):
            self.step_exponent = self.step_exponent - 1

            if self.step_exponent < -self.decimals():
                self.step_exponent = -self.decimals()

            self.update_step_size()
            return True

        return QDoubleSpinBox.event(self, event)

    def update_step_size(self):
        self.setSingleStep(10**self.step_exponent)
        self.update_suffix()

    ### END: Left, right Arrow: changing stepsize

    def update_suffix(self):
        if self._units is None:
            units = ""
        else:
            units = " {}".format(self._units)
        if self._show_step_exponent:
            self.setSuffix("{units} Step: 1E{exp}".format(units=units, exp=self.step_exponent))
        else:
            self.setSuffix(units)

    @pyqtSlot(float)
    def receiveValue(self, new_val):
        self.valueBeingSet = True
        self.setValue(new_val)
        self.valueBeingSet = False

    @pyqtSlot(float)
    def sendValue(self, value):
        if not self.valueBeingSet:
            self.send_value_signal.emit(value)

    @pyqtSlot(bool)
    def connectionStateChanged(self, connected):
        self._connected = connected
        self.set_enable_state()

    @pyqtSlot(bool)
    def writeAccessChanged(self, write_access):
        self._write_access = write_access
        self.set_enable_state()

    def set_enable_state(self):
        self.setEnabled(self._write_access and self._connected)

    @pyqtSlot(str)
    def receiveUnits(self,unit):
        """
        Accept a unit to display with a channel's value

        The unit may or may not be displayed based on the :attr:`showUnits`
        attribute. Receiving a new value for the unit causes the display to
        reset.
        """
        self._units = str(unit)
        self._scale = 1
        self.update_suffix()

    @pyqtSlot(int)
    @pyqtSlot(float)
    def receive_upper_limit(self,limit):
        self.setMaximum(limit)

    @pyqtSlot(int)
    @pyqtSlot(float)
    def receive_lower_limit(self,limit):
        self.setMinimum(limit)
    
    @pyqtSlot(int)
    def receivePrecision(self, new_prec):
        self._prec = new_prec
        self.setDecimals(self._prec)
    
    def getChannel(self):
        return str(self._channel)

    def setChannel(self, value):
        if self._channel != value:
            self._channel = str(value)

    def resetChannel(self):
        if self._channel is not None:
            self._channel = None

    channel = pyqtProperty(str, getChannel, setChannel, resetChannel)

    def getShow_step_exponent(self):
        return self._show_step_exponent
    
    def setShow_step_exponent(self, val):
        self._show_step_exponent = val
        self.update()
    
    def resetShow_step_exponent(self):
        if self._show_step_exponent:
            self._show_step_exponent = False

    show_step_exponent = pyqtProperty(bool, getShow_step_exponent, setShow_step_exponent, resetShow_step_exponent)

    def channels(self):
        return [PyDMChannel(address=self.channel,
                            connection_slot=self.connectionStateChanged,
                            value_slot=self.receiveValue,
                            unit_slot = self.receiveUnits,
                            write_access_slot=self.writeAccessChanged,
                            upper_ctrl_limit_slot = self.receive_upper_limit,
                            lower_ctrl_limit_slot = self.receive_lower_limit,
                            prec_slot = self.receivePrecision,
                            value_signal=self.send_value_signal,
               )]
