from ..PyQt.QtGui import QDoubleSpinBox, QApplication
from ..PyQt.QtCore import pyqtProperty, QEvent, Qt
from .base import PyDMWritableWidget


class PyDMSpinbox(QDoubleSpinBox, PyDMWritableWidget):

    def __init__(self, parent=None, init_channel=None):
        super().__init__(parent, init_channel=init_channel)
        self.valueBeingSet = False
        self.setEnabled(False)
        self._show_step_exponent = True
        self.step_exponent = 0
        self.setDecimals(0)
        self.app = QApplication.instance()

    def event(self, event):
        if (event.type() == QEvent.KeyPress):
            ctrl_hold = self.app.queryKeyboardModifiers() == Qt.ControlModifier
            
            if ctrl_hold and (event.key() == Qt.Key_Left):
                self.step_exponent = self.step_exponent + 1
                self.update_step_size()
                return True
    
            if ctrl_hold and (event.key() == Qt.Key_Right):
                self.step_exponent = self.step_exponent - 1
    
                if self.step_exponent < -self.decimals():
                    self.step_exponent = -self.decimals()
    
                self.update_step_size()
                return True

            if (event.key() == Qt.Key_Up):
                self.setValue(self.value + self.singleStep())
                self.send_value()
                return True

            if (event.key() == Qt.Key_Down):
                self.setValue(self.value - self.singleStep())
                self.send_value()
                return True
    
            if (event.key() == Qt.Key_Return):
                self.send_value()
                return True

        return super().event(event)

    def update_step_size(self):
        self.setSingleStep(10**self.step_exponent)
        self.update_format_string()

    def update_format_string(self):
        if self._show_units:
            units = " {}".format(self._unit)
        else:
            units = ""
            
        if self._show_step_exponent:
            self.setSuffix("{units} Step: 1E{exp}".format(
                units=units, exp=self.step_exponent))
        else:
            self.setSuffix(units)

    def value_changed(self, new_val):
        super().value_changed(new_val)
        self.valueBeingSet = True
        self.setValue(new_val)
        self.valueBeingSet = False

    def send_value(self):
        value = float(self.cleanText())
        if not self.valueBeingSet:
            self.send_value_signal[float].emit(value)

    def ctrl_limit_changed(self, which, new_limit):
        super().ctrl_limit_changed(which, new_limit)
        if which == "UPPER":
            self.setMaximum(new_limit)
        else:
            self.setMinimum(new_limit)

    def precision_changed(self, new_precision):
        super().precision_changed(new_precision)
        self.setDecimals(new_precision)

    @pyqtProperty(bool)
    def showStepExponent(self):
        return self._show_step_exponent

    @showStepExponent.setter
    def showStepExponent(self, val):
        self._show_step_exponent = val
        self.update()