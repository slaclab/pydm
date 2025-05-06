from qtpy.QtWidgets import QDoubleSpinBox, QApplication, QLineEdit
from qtpy.QtCore import Property, Qt
from .base import PyDMWritableWidget, TextFormatter, PostParentClassInitSetup


class PyDMSpinbox(QDoubleSpinBox, TextFormatter, PyDMWritableWidget):
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
        self._alarm_sensitive_border = False
        self._show_step_exponent = True
        self._write_on_press = False
        self._user_defined_limits = False
        self._user_minimum = 0
        self._user_maximum = 0
        self.step_exponent = 0
        self.setDecimals(0)
        self.app = QApplication.instance()
        self.setAccelerated(True)

        # install an event filter on the QDoubleSpinBox's children
        # in order to catch the click events
        child = self.findChild(QLineEdit)
        child.installEventFilter(self)

        # Execute setup calls that must be done here in the widget class's __init__,
        # and after it's parent __init__ calls have completed.
        # (so we can avoid pyside6 throwing an error, see func def for more info)
        PostParentClassInitSetup(self)

    # On pyside6, we need to expilcity call pydm's base class's eventFilter() call or events
    # will not propagate to the parent classes properly.
    def eventFilter(self, obj, event):
        return PyDMWritableWidget.eventFilter(self, obj, event)

    def stepBy(self, step):
        """
        Method triggered whenever user triggers a step. If the writeOnPress property
        is enabled, the updated value will be sent.

        Parameters
        ----------
        step: int
        """
        super().stepBy(step)
        if self._write_on_press:
            self.send_value()

    def keyPressEvent(self, ev):
        """
        Method invoked when a key press event happens on the QDoubleSpinBox.

        For PyDMSpinBox we are interested on the Keypress events for:
            - CTRL + Left/Right : Increase or Decrease the step exponent;
            - Up / Down : Add or Remove `singleStep` units to the value;
            - PageUp / PageDown : Add or Remove 10 times `singleStep` units
              to the value;
            - Return or Enter : Send the value to the channel using the
              `send_value_signal`.

        Parameters
        ----------
        ev : QEvent
        """
        ctrl_hold = self.app.queryKeyboardModifiers() == Qt.ControlModifier
        if ctrl_hold and (ev.key() in (Qt.Key_Left, Qt.Key_Right)):
            self.step_exponent += 1 if ev.key() == Qt.Key_Left else -1
            self.step_exponent = max(-self.decimals(), self.step_exponent)
            self.update_step_size()

        elif ev.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.send_value()

        else:
            super().keyPressEvent(ev)

    def widget_ctx_menu(self):
        """
        Fetch the Widget specific context menu which will be populated with additional tools by `assemble_tools_menu`.

        Returns
        -------
        QMenu or None
            If the return of this method is None a new QMenu will be created by `assemble_tools_menu`.
        """

        def toggle_step():
            self.showStepExponent = not self.showStepExponent

        def toggle_write():
            self.writeOnPress = not self.writeOnPress

        menu = self.lineEdit().createStandardContextMenu()
        menu.addSeparator()
        ac = menu.addAction("Toggle Show Step Size")
        ac.triggered.connect(toggle_step)

        ac_write = menu.addAction("Toggle Write On Press")
        ac_write.triggered.connect(toggle_write)

        return menu

    def update_step_size(self):
        """
        Update the Single Step size on the QDoubleSpinBox.
        """
        self.setSingleStep(10**self.step_exponent)
        self.update_format_string()

    def update_format_string(self):
        """
        Reconstruct the format string to be used when representing the
        output value.

        Returns
        -------
        None
        """
        if self._show_units:
            units = " {}".format(self._unit)
        else:
            units = ""

        if self._show_step_exponent:
            self.setSuffix("{0} Step: 1E{1}".format(units, self.step_exponent))
            self.lineEdit().setToolTip("")
        else:
            self.setSuffix(units)
            self.lineEdit().setToolTip("Step: 1E{0:+d}".format(self.step_exponent))

    def value_changed(self, new_val):
        """
        Callback invoked when the Channel value is changed.

        Parameters
        ----------
        new_val : int or float
            The new value from the channel.
        """
        if new_val is None:
            # SpinBox is unable to work with None and
            # but sometimes it can arrive as an initial value
            return
        super().value_changed(new_val)
        self.valueBeingSet = True
        self.setValue(new_val)
        self.valueBeingSet = False

    def send_value(self):
        """
        Method invoked to send the current value on the QDoubleSpinBox to
        the channel using the `send_value_signal`.
        """
        value = QDoubleSpinBox.value(self)
        if not self.valueBeingSet:
            self.send_value_signal[float].emit(value)

    @Property(bool)
    def userDefinedLimits(self) -> bool:
        """
        True if the range of the spinbox should be set based on user-defined limits, False if
        it should be set based on the limits received from the channel

        Returns
        -------
        bool
        """
        return self._user_defined_limits

    @userDefinedLimits.setter
    def userDefinedLimits(self, user_defined_limits: bool) -> None:
        """
        Whether or not to set the range of the spinbox based on user-defined limits. Will also reset
        the range of the spinbox in case this is called while the application is running to ensure it matches
        what the user requested.

        Parameters
        ----------
        user_defined_limits : bool
        """
        self._user_defined_limits = user_defined_limits
        self.reset_limits()

    @Property(float)
    def userMinimum(self) -> float:
        """
        Lower user-defined limit value

        Returns
        -------
        float
        """
        return self._user_minimum

    @userMinimum.setter
    def userMinimum(self, new_min: float) -> None:
        """
        Set the Lower user-defined limit value, updates the range of the spinbox if needed

        Parameters
        ----------
        new_min : float
        """
        self._user_minimum = new_min
        self.reset_limits()

    @Property(float)
    def userMaximum(self) -> float:
        """
        Upper user-defined limit value

        Returns
        -------
        float
        """
        return self._user_maximum

    @userMaximum.setter
    def userMaximum(self, new_max: float) -> None:
        """
        Set the upper user-defined limit value, updates the range of the spinbox if needed

        Parameters
        ----------
        new_max : float
        """
        self._user_maximum = new_max
        self.reset_limits()

    def reset_limits(self) -> None:
        """
        Will reset the lower and upper limits to either the ones set by the user, or the ones from the
        channel depending on the current state of userDefinedLimits(). If a None value would be set,
        do not attempt the update.
        """
        if self.userDefinedLimits:
            if self.userMinimum is None or self.userMaximum is None:
                return
            self.setMinimum(self.userMinimum)
            self.setMaximum(self.userMaximum)
        else:
            if self._lower_ctrl_limit is None or self._upper_ctrl_limit is None:
                return
            self.setMinimum(self._lower_ctrl_limit)
            self.setMaximum(self._upper_ctrl_limit)

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
        super().ctrl_limit_changed(which, new_limit)
        if not self.userDefinedLimits:
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
        super().precision_changed(new_precision)
        self.setDecimals(self.precision)

    @Property(int)
    def precision(self):
        if self.precisionFromPV:
            return self._prec
        else:
            return self._user_prec

    @precision.setter
    def precision(self, new_prec):
        if self.precisionFromPV:
            return
        if new_prec and self._user_prec != int(new_prec) and new_prec >= 0:
            self._user_prec = int(new_prec)
            self.value_changed(self.value)
            self.setDecimals(new_prec)

    @Property(bool)
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

    @Property(bool)
    def writeOnPress(self):
        """
        Whether to write value on key press

        Returns
        -------
        bool
        """
        return self._write_on_press

    @writeOnPress.setter
    def writeOnPress(self, val):
        """
        Whether value to write on key press.

        Parameters
        ----------
        val : bool
        """
        self._write_on_press = val
