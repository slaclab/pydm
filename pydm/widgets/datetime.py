import logging
from qtpy import QtWidgets, QtCore

from .base import PyDMWritableWidget, PyDMWidget, PostParentClassInitSetup
from pydm.utilities import ACTIVE_QT_WRAPPER, QtWrapperTypes, coerce_enum_value

if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYSIDE6:
    from PySide6.QtCore import Property
else:
    from qtpy.QtCore import Property

logger = logging.getLogger(__name__)


# Canonical TimeBase: a plain int-attr class for PyQt5; a real IntEnum for the Qt6 bindings
# (PyQt6 + PySide6).  TimeBase (PascalCase) is intentionally distinct from the ``timeBase``
# property name -- a same-name collision silently breaks uic runtime loading.
class TimeBase(object):
    Milliseconds = 0
    Seconds = 1


if ACTIVE_QT_WRAPPER in (QtWrapperTypes.PYQT6, QtWrapperTypes.PYSIDE6):
    from pydm.utilities import int_enum_from

    TimeBase = int_enum_from("TimeBase", TimeBase)


# PySide6 Designer-dropdown carrier(s) for this widget's enum(s) -- see the cross-wrapper enum note in pydm.utilities.
# TimeBase is shared by two widgets, so each gets its OWN carrier base (named like that widget).
if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYSIDE6:
    from PySide6.QtCore import QEnum
    from enum import IntEnum

    class PyDMDateTimeEdit(QtWidgets.QDateTimeEdit, PyDMWritableWidget):
        @QEnum
        class TimeBase(IntEnum):
            Milliseconds = 0
            Seconds = 1

    class PyDMDateTimeLabel(QtWidgets.QLabel, PyDMWidget):
        @QEnum
        class TimeBase(IntEnum):
            Milliseconds = 0
            Seconds = 1

    _PyDMDateTimeEditBases = (PyDMDateTimeEdit,)
    _PyDMDateTimeLabelBases = (PyDMDateTimeLabel,)
else:
    _PyDMDateTimeEditBases = (QtWidgets.QDateTimeEdit, PyDMWritableWidget)
    _PyDMDateTimeLabelBases = (QtWidgets.QLabel, PyDMWidget)


class PyDMDateTimeEdit(*_PyDMDateTimeEditBases):
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
    elif ACTIVE_QT_WRAPPER == QtWrapperTypes.PYQT6:
        from pydm.utilities import pyqt6_designer_enum

        TimeBase = pyqt6_designer_enum("PyDMDateTimeEdit", TimeBase)
    else:  # PySide6: adopt this widget's carrier-registered enum
        TimeBase = _PyDMDateTimeEditBases[0].TimeBase

    # Publish the registered enum as a class attribute on every wrapper (PyQt5's Q_ENUM
    # registers it in the metaobject but does not assign it here), so both ``self.TimeBase``
    # and uic's ``PyDMDateTimeEdit.TimeBase.<key>`` resolve.
    TimeBase = TimeBase
    Milliseconds = TimeBase.Milliseconds
    Seconds = TimeBase.Seconds

    returnPressed = QtCore.Signal()

    def __init__(self, parent=None, init_channel=None):
        self._block_past_date = True
        self._relative = True
        self._time_base = self.TimeBase.Milliseconds

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

    def readTimeBase(self) -> TimeBase:
        """Whether to use milliseconds or seconds as time base for the widget"""
        return self._time_base

    def setTimeBase(self, base) -> None:
        base = coerce_enum_value(base, self.TimeBase)
        if self._time_base != base:
            self._time_base = base

    timeBase = Property(TimeBase, readTimeBase, setTimeBase)

    def readRelative(self) -> bool:
        """
        Whether the value in milliseconds is relative to current date or if it
        is milliseconds since epoch.
        """
        return self._relative

    def setRelative(self, checked) -> None:
        if self._relative != checked:
            self._relative = checked

    relative = Property(bool, readRelative, setRelative)

    def readBlockPastDate(self) -> bool:
        """Error out if user tries to set value to a date older than current."""
        return self._block_past_date

    def setBlockPastDate(self, block) -> None:
        if block != self._block_past_date:
            self._block_past_date = block

    blockPastDate = Property(bool, readBlockPastDate, setBlockPastDate)

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

        if self.timeBase == self.TimeBase.Seconds:
            new_value /= 1000.0

        # Force to the same base type as the data source, else qt can cast the pointer wrong
        new_value = self.channeltype(new_value)
        self.send_value_signal[self.channeltype].emit(new_value)

    def value_changed(self, new_val):
        super().value_changed(new_val)
        new_val = int(new_val)

        if self.timeBase == self.TimeBase.Seconds:
            new_val *= 1000

        val = QtCore.QDateTime.currentDateTime()
        if self._relative:
            val = val.addMSecs(new_val)
        else:
            val.setMSecsSinceEpoch(new_val)
        self.setDateTime(val)


class PyDMDateTimeLabel(*_PyDMDateTimeLabelBases):
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
    elif ACTIVE_QT_WRAPPER == QtWrapperTypes.PYQT6:
        from pydm.utilities import pyqt6_designer_enum

        TimeBase = pyqt6_designer_enum("PyDMDateTimeLabel", TimeBase)
    else:  # PySide6: adopt this widget's carrier-registered enum
        TimeBase = _PyDMDateTimeLabelBases[0].TimeBase

    # Publish the registered enum as a class attribute on every wrapper (PyQt5's Q_ENUM
    # registers it in the metaobject but does not assign it here), so both ``self.TimeBase``
    # and uic's ``PyDMDateTimeLabel.TimeBase.<key>`` resolve.
    TimeBase = TimeBase
    Milliseconds = TimeBase.Milliseconds
    Seconds = TimeBase.Seconds

    def __init__(self, parent=None, init_channel=None):
        QtWidgets.QLabel.__init__(self, parent)
        PyDMWidget.__init__(self, init_channel=init_channel)

        self._block_past_date = True
        self._relative = True
        self._time_base = self.TimeBase.Milliseconds
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

    def readTextFormat(self) -> str:
        """The format to use when displaying the date/time values."""
        return self._text_format

    def setTextFormat(self, text_format) -> None:
        if self._text_format != text_format:
            self._text_format = text_format
            if self.value is not None:
                self.value_changed(self.value)

    textFormat = Property(str, readTextFormat, setTextFormat)

    def readTimeBase(self) -> TimeBase:
        """Whether to use milliseconds or seconds as time base for the widget"""
        return self._time_base

    def setTimeBase(self, base) -> None:
        base = coerce_enum_value(base, self.TimeBase)
        if self._time_base != base:
            self._time_base = base

    timeBase = Property(TimeBase, readTimeBase, setTimeBase)

    def readRelative(self) -> None:
        """
        Whether the value in milliseconds is relative to current date or if it
        is milliseconds since epoch.
        """
        return self._relative

    def setRelative(self, checked) -> None:
        if self._relative != checked:
            self._relative = checked

    relative = Property(bool, readRelative, setRelative)

    def value_changed(self, new_val):
        super().value_changed(new_val)
        new_val = int(new_val)

        if self.timeBase == self.TimeBase.Seconds:
            new_val *= 1000

        val = QtCore.QDateTime.currentDateTime()
        if self._relative:
            val = val.addMSecs(new_val)
        else:
            val.setMSecsSinceEpoch(new_val)
        self.setText(val.toString(self.textFormat))
