import functools
import weakref

from qtpy.QtWidgets import QFrame
from qtpy.QtCore import Property
from .base import PyDMWidget, widget_destroyed
from ..utilities import is_qt_designer


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

        if not is_qt_designer():
            # We should  install the Event Filter only if we are running
            # and not at the Designer
            self.installEventFilter(self)
            self.check_enable_state()

        self.destroyed.connect(functools.partial(widget_destroyed, self.channels, weakref.ref(self)))

    @Property(bool)
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
