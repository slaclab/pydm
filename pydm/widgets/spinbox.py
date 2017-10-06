from ..PyQt.QtGui import QDoubleSpinBox, QApplication
from ..PyQt.QtCore import pyqtProperty, QEvent, Qt
from .base import PyDMWritableWidget


class PyDMSpinbox(QDoubleSpinBox, PyDMWritableWidget):
    """
    A QDoubleSpinBox with support for Channels and more from PyDM.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """
    def __init__(self, parent=None, init_channel=None):
        QDoubleSpinBox.__init__(self, parent)
        PyDMWritableWidget.__init__(self, init_channel=init_channel)
        self.valueBeingSet = False
        self.setEnabled(False)
        self._show_step_exponent = True
        self.step_exponent = 0
        self.setDecimals(0)
        self.app = QApplication.instance()

        self.valueChanged.connect(self.send_value)  # signal from spinbox
        self.setKeyboardTracking(False)
        self.setAccelerated(True)

    def event(self, event):
        """
        Method invoked when an event of any nature happens on the
        QDoubleSpinBox.

        For PyDMSpinBox we are interested on the Keypress events for:
        - CTRL + Left/Right : Increase or Decrease the step exponent
        - Up / Down : Add or Remove `singleStep` units to the value
        - Return : Send the value to the channel using the `send_value_signal`

        Parameters
        ----------
        event : QEvent
        """
        if event.type() == QEvent.KeyPress and \
           self.app.queryKeyboardModifiers() == Qt.ControlModifier:

            if event.key() == Qt.Key_Left:
                self.step_exponent = self.step_exponent + 1
                self.update_step_size()
                return True
            elif event.key() == Qt.Key_Right:
                self.step_exponent = max(self.step_exponent - 1,
                                         -self.decimals())
                self.update_step_size()
                return True

        return super(PyDMSpinbox, self).event(event)

    def contextMenuEvent(self, ev):
        """Increment LineEdit menu to toggle the display of the step size."""
        def toogle():
            self.showStepExponent = not self.showStepExponent

        menu = self.lineEdit().createStandardContextMenu()
        menu.addSeparator()
        ac = menu.addAction('Toggle Show Step Size')
        ac.triggered.connect(toogle)
        menu.exec_(ev.globalPos())

    def update_step_size(self):
        """
        Update the Single Step size on the QDoubleSpinBox.
        """
        self.setSingleStep(10 ** self.step_exponent)
        self.update_format_string()

    def update_format_string(self):
        """
        Reconstruct the format string to be used when representing the
        output value.

        Returns
        -------
        format_string : str
            The format string to be used including or not the precision
            and unit
        """
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
        """
        Callback invoked when the Channel value is changed.

        Parameters
        ----------
        new_val : int or float
            The new value from the channel.
        """
        super(PyDMSpinbox, self).value_changed(new_val)
        self.valueBeingSet = True
        self.setValue(new_val)
        self.valueBeingSet = False

    def send_value(self, value):
        """
        Method invoked to send the current value on the QDoubleSpinBox to
        the channel using the `send_value_signal`.
        """
        if not self.valueBeingSet:
            self.send_value_signal[float].emit(value)

    def ctrl_limit_changed(self, which, new_limit):
        """
        Callback invoked when the Channel receives new control limit
        values.

        Parameters
        ----------
        which : str
            Which control limit was changed. "UPPER" or "LOWER"
        new_limit : float
            New value for the control limit
        """
        super(PyDMSpinbox, self).ctrl_limit_changed(which, new_limit)
        if which == "UPPER":
            self.setMaximum(new_limit)
        else:
            self.setMinimum(new_limit)

    def precision_changed(self, new_precision):
        """
        Callback invoked when the Channel has new precision value.
        This callback also triggers an update_format_string call so the
        new precision value is considered.

        Parameters
        ----------
        new_precison : int or float
            The new precision value
        """
        super(PyDMSpinbox, self).precision_changed(new_precision)
        self.setDecimals(new_precision)

    @pyqtProperty(bool)
    def showStepExponent(self):
        """
        Whether to show or not the step exponent

        Returns
        -------
        bool
        """
        return self._show_step_exponent

    @showStepExponent.setter
    def showStepExponent(self, val):
        """
        Whether to show or not the step exponent

        Parameters
        ----------
        val : bool
        """
        self._show_step_exponent = val
        self.update_format_string()
