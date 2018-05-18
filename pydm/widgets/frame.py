from ..PyQt.QtGui import QFrame
from ..PyQt.QtCore import pyqtProperty
from .base import PyDMWidget, compose_stylesheet


class PyDMFrame(QFrame, PyDMWidget):
    """
    QFrame with support for alarms
    This class inherits from QFrame and PyDMWidget.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """
    def __init__(self, parent=None, init_channel=None):
        QFrame.__init__(self, parent)
        PyDMWidget.__init__(self, init_channel=init_channel)

        self._disable_on_disconnect = False
        self.alarmSensitiveBorder = False

    @pyqtProperty(bool)
    def disableOnDisconnect(self):
        """
        Whether or not the PyDMFrame should be disabled in case the
        channel is disconnected.

        Returns
        -------
        disable : bool
            The configured value
        """
        return self._disable_on_disconnect

    @disableOnDisconnect.setter
    def disableOnDisconnect(self, new_val):
        """
        Whether or not the PyDMFrame should be disabled in case the
        channel is disconnected.

        Parameters
        ----------
        new_val : bool
            The new configuration to use
        """
        if self._disable_on_disconnect != bool(new_val):
            self._disable_on_disconnect = new_val
            self.check_enable_state()

    def alarm_severity_changed(self, new_alarm_severity):
        """
        Callback invoked when the Channel alarm severity is changed.
        This callback is not processed if the widget has no channel
        associated with it.
        This callback handles the composition of the stylesheet to be
        applied and the call
        to update to redraw the widget with the needed changes for the
        new state.

        Parameters
        ----------
        new_alarm_severity : int
            The new severity where 0 = NO_ALARM, 1 = MINOR, 2 = MAJOR
            and 3 = INVALID
        """
        if self._channel is None:
            return
        # Cleanup the old alarm stylesheet used
        alarm_style = compose_stylesheet(style=self._style, obj=self)
        original_style = str(self.styleSheet()).replace(alarm_style, "")

        self._alarm_state = new_alarm_severity

        # Must update the alarm flags here as the alarm sensitive content and alarm sensitive border flags
        # can be toggled after the widget's construction
        self._alarm_flags = (self.ALARM_CONTENT * self._alarm_sensitive_content) | \
                            (self.ALARM_BORDER * self._alarm_sensitive_border)

        self._style = dict(self.alarm_style_sheet_map[self._alarm_flags][new_alarm_severity])
        if "color" in self._style:
            if self._alarm_state != PyDMWidget.ALARM_NONE:
                # The style doesn't take the color attribute, but replace it with the background-color one
                self._style["background-color"] = self._style["color"]
            del self._style["color"]
        style = compose_stylesheet(style=self._style, obj=self)
        self.setStyleSheet(original_style + style)
        self.update()

    def check_enable_state(self):
        """
        Checks whether or not the widget should be disable.
        This method also disables the widget and add a Tool Tip
        with the reason why it is disabled.
        """
        if hasattr(self, "_disable_on_disconnect") and self._disable_on_disconnect:
            PyDMWidget.check_enable_state(self)
        else:
            self.setEnabled(True)
