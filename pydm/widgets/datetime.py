import logging
from qtpy import QtWidgets, QtCore

from .base import PyDMWritableWidget, PyDMWidget, PostParentClassInitSetup
from pydm.utilities import ACTIVE_QT_WRAPPER, QtWrapperTypes

logger = logging.getLogger(__name__)


class TimeBase(object):
    Milliseconds = 0
    Seconds = 1


if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYSIDE6:
    from PySide6.QtCore import QEnum
    from enum import Enum

    @QEnum
    # overrides prev enum def
    class TimeBase(Enum):  # noqa F811
        Milliseconds = 0
        Seconds = 1


class PyDMDateTimeEdit(QtWidgets.QDateTimeEdit, PyDMWritableWidget):
    """
    A QDateTimeEdit with support for setting the text via a PyDM Channel, or
    through the PyDM Rules system.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

    if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYQT5:
        from PyQt5.QtCore import Q_ENUM

        Q_ENUM(TimeBase)

    # Make enum definitions known to this class
    Milliseconds = TimeBase.Milliseconds
    Seconds = TimeBase.Seconds

    returnPressed = QtCore.Signal()

    def __init__(self, parent=None, init_channel=None):
        self._block_past_date = True
        self._relative = True
        self._time_base = TimeBase.Milliseconds

        QtWidgets.QDateTimeEdit.__init__(self, parent)
        PyDMWritableWidget.__init__(self, init_channel=init_channel)
        self.setDisplayFormat("yyyy/MM/dd hh:mm:ss.zzz")
        self.setDateTime(QtCore.QDateTime.currentDateTime())
        self.setCalendarPopup(True)
        self.returnPressed.connect(self.send_value)
        # Execute setup calls that must be done here in the widget class's __init__,
        # and after it's parent __init__ calls have completed.
        # (so we can avoid pyside6 throwing an error, see func def for more info)
        PostParentClassInitSetup(self)

    # On pyside6, we need to expilcity call pydm's base class's eventFilter() call or events
    # will not propagate to the parent classes properly.
    def eventFilter(self, obj, event):
        return PyDMWritableWidget.eventFilter(self, obj, event)

    @QtCore.Property(TimeBase)
    def timeBase(self):
        """Whether to use milliseconds or seconds as time base for the widget"""
        return self._time_base

    @timeBase.setter
    def timeBase(self, base):
        if self._time_base != base:
            self._time_base = base

    @QtCore.Property(bool)
    def relative(self):
        """
        Whether the value in milliseconds is relative to current date or if it
        is milliseconds since epoch.
        """
        return self._relative

    @relative.setter
    def relative(self, checked):
        if self._relative != checked:
            self._relative = checked

    @QtCore.Property(bool)
    def blockPastDate(self):
        """Error out if user tries to set value to a date older than current."""
        return self._block_past_date

    @blockPastDate.setter
    def blockPastDate(self, block):
        if block != self._block_past_date:
            self._block_past_date = block

    def keyPressEvent(self, key_event):
        ret = super().keyPressEvent(key_event)
        if key_event.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
            self.returnPressed.emit()
        return ret

    def send_value(self):
        val = self.dateTime()
        now = QtCore.QDateTime.currentDateTime()
        if self._block_past_date and val < now:
            logger.error("Selected date cannot be lower than current date.")
            return

        if self.relative:
            new_value = now.msecsTo(val)
        else:
            new_value = val.toMSecsSinceEpoch()

        if self.timeBase == TimeBase.Seconds:
            new_value /= 1000.0
        self.send_value_signal[self.channeltype].emit(new_value)

    def value_changed(self, new_val):
        super().value_changed(new_val)
        new_val = int(new_val)

        if self.timeBase == TimeBase.Seconds:
            new_val *= 1000

        val = QtCore.QDateTime.currentDateTime()
        if self._relative:
            val = val.addMSecs(new_val)
        else:
            val.setMSecsSinceEpoch(new_val)
        self.setDateTime(val)


class PyDMDateTimeLabel(QtWidgets.QLabel, PyDMWidget):
    """
    A QLabel with support for setting the text via a PyDM Channel, or
    through the PyDM Rules system.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

    if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYQT5:
        from PyQt5.QtCore import Q_ENUM

        Q_ENUM(TimeBase)

    # Make enum definitions known to this class
    Milliseconds = TimeBase.Milliseconds
    Seconds = TimeBase.Seconds

    def __init__(self, parent=None, init_channel=None):
        QtWidgets.QLabel.__init__(self, parent)
        PyDMWidget.__init__(self, init_channel=init_channel)

        self._block_past_date = True
        self._relative = True
        self._time_base = TimeBase.Milliseconds
        self._text_format = "yyyy/MM/dd hh:mm:ss.zzz"
        self.setText("")

        # Execute setup calls that must be done here in the widget class's __init__,
        # and after it's parent __init__ calls have completed.
        # (so we can avoid pyside6 throwing an error, see func def for more info)
        PostParentClassInitSetup(self)

    # On pyside6, we need to expilcity call pydm's base class's eventFilter() call or events
    # will not propagate to the parent classes properly.
    def eventFilter(self, obj, event):
        return PyDMWidget.eventFilter(self, obj, event)

    @QtCore.Property(str)
    def textFormat(self):
        """The format to use when displaying the date/time values."""
        return self._text_format

    @textFormat.setter
    def textFormat(self, text_format):
        if self._text_format != text_format:
            self._text_format = text_format
            if self.value is not None:
                self.value_changed(self.value)

    @QtCore.Property(TimeBase)
    def timeBase(self):
        """Whether to use milliseconds or seconds as time base for the widget"""
        return self._time_base

    @timeBase.setter
    def timeBase(self, base):
        if self._time_base != base:
            self._time_base = base

    @QtCore.Property(bool)
    def relative(self):
        """
        Whether the value in milliseconds is relative to current date or if it
        is milliseconds since epoch.
        """
        return self._relative

    @relative.setter
    def relative(self, checked):
        if self._relative != checked:
            self._relative = checked

    def value_changed(self, new_val):
        super().value_changed(new_val)
        new_val = int(new_val)

        if self.timeBase == TimeBase.Seconds:
            new_val *= 1000

        val = QtCore.QDateTime.currentDateTime()
        if self._relative:
            val = val.addMSecs(new_val)
        else:
            val.setMSecsSinceEpoch(new_val)
        self.setText(val.toString(self.textFormat))
