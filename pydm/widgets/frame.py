from ..PyQt.QtGui import QFrame
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
        self.alarmSensitiveBorder = False

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
        self._alarm_state = new_alarm_severity
        original_style = str(self.styleSheet()).replace(compose_stylesheet(style=self._style, obj=self), "")
        self._style = dict(self.alarm_style_sheet_map[self._alarm_flags][new_alarm_severity])
        if "color" in self._style and self._alarm_state != 0:
            self._style["background-color"] = self._style["color"]
            del self._style["color"]
        style = compose_stylesheet(style=self._style, obj=self)
        self.setStyleSheet(original_style + style)
        self.update()
