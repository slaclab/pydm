from qtpy.QtWidgets import QTabBar, QTabWidget
from qtpy.QtGui import QIcon, QColor
from qtpy.QtCore import QByteArray
from .base import PyDMWidget, PostParentClassInitSetup
from .channel import PyDMChannel
from functools import partial
from pydm.utilities.iconfont import IconFont
from pydm.utilities import ACTIVE_QT_WRAPPER, QtWrapperTypes

if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYSIDE6:
    from PySide6.QtCore import Property
else:
    from PyQt5.QtCore import pyqtProperty as Property


class PyDMTabBar(QTabBar, PyDMWidget):
    """PyDMTabBar is used internally by PyDMTabWidget, and shouldn't be directly used on its own."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_channels = {}
        self.tab_connection_status = {}
        self.tab_alarm_severity = {}
        self._channels = []
        self._no_alarm_icon_color = QColor(0, 220, 0)
        self._minor_alarm_icon_color = QColor(220, 220, 0)
        self._major_alarm_icon_color = QColor(255, 0, 0)
        self._invalid_alarm_icon_color = QColor(220, 0, 220)
        self._disconnected_alarm_icon_color = QColor(255, 255, 255)
        self.alarm_icons = None
        self.generate_alarm_icons()

        # Execute setup calls that must be done here in the widget class's __init__,
        # and after it's parent __init__ calls have completed.
        # (so we can avoid pyside6 throwing an error, see func def for more info)
        PostParentClassInitSetup(self)

    # On pyside6, we need to expilcity call pydm's base class's eventFilter() call or events
    # will not propagate to the parent classes properly.
    def eventFilter(self, obj, event):
        return PyDMWidget.eventFilter(self, obj, event)

    def readCurrentTabAlarmChannel(self) -> str:
        """A channel to use for this tab's alarm indicator."""
        if self.currentIndex() < 0:
            return
        try:
            return str(self.tab_channels[self.currentIndex()]["address"])
        except KeyError:
            return ""

    def setCurrentTabAlarmChannel(self, new_alarm_channel) -> None:
        if self.currentIndex() < 0:
            return
        self.set_channel_for_tab(self.currentIndex(), new_alarm_channel)

    currentTabAlarmChannel = Property(str, readCurrentTabAlarmChannel, setCurrentTabAlarmChannel)

    def set_channel_for_tab(self, index, channel):
        idx = self.tab_channels.get(index)
        if idx:
            # Disconnect the channel if we already had one in
            chan = idx.get("channel", None)
            if chan:
                self._channels.remove(chan)
                self.tab_channels[index]["channel"] = None
                chan.disconnect()
                del chan
        else:
            chan = None
            self.tab_channels[index] = dict()

        self.tab_channels[index]["address"] = str(channel)
        self.set_initial_icon_for_tab(index)
        if channel:
            # Create PyDMChannel and connect
            chan = PyDMChannel(
                address=str(channel),
                connection_slot=partial(self.connection_changed_for_tab, index),
                severity_slot=partial(self.alarm_changed_for_tab, index),
            )
            self.tab_channels[index]["channel"] = chan
            chan.connect()
            self._channels.append(chan)

    def channels(self):
        if self._channels is not None:
            return list(self._channels)
        return None

    def connection_changed_for_tab(self, index, conn):
        if not conn:
            self.setTabIcon(index, self.alarm_icons[self.ALARM_DISCONNECTED])
        self.tab_connection_status[index] = conn

    def alarm_changed_for_tab(self, index, alarm_state):
        self.setTabIcon(index, self.alarm_icons[alarm_state])
        self.tab_alarm_severity[index] = alarm_state

    def getAlarmChannels(self):
        """alarmChannels is a property used to store the configuration of this tab bar
        when it has been created in Qt Designer.  This property isn't directly editable
        by users, they will go through the currentTabAlarmChannel property to edit this
        information."""
        return [str(self.tab_channels[i]["address"]) for i in range(0, self.count())]

    def setAlarmChannels(self, new_alarm_channels):
        for tab_number, channel_address in enumerate(new_alarm_channels):
            self.set_channel_for_tab(tab_number, channel_address)

    def set_initial_icon_for_tab(self, index):
        idx = self.tab_channels.get(index)
        if idx and idx.get("address") in ("", "None", None):
            self.setTabIcon(index, QIcon())
        else:
            icon_index = self.ALARM_DISCONNECTED
            if self.tab_connection_status.get(index, False) and index in self.tab_alarm_severity:
                icon_index = self.tab_alarm_severity[index]
            self.setTabIcon(index, self.alarm_icons[icon_index])

    def tabInserted(self, index):
        super().tabInserted(index)
        if index not in self.tab_channels:
            self.tab_channels[index] = {"address": ""}
        self.set_initial_icon_for_tab(index)

    def readNoAlarmIconColor(self) -> QColor:
        return self._no_alarm_icon_color

    def setNoAlarmIconColor(self, new_color) -> None:
        if self._no_alarm_icon_color != new_color:
            self._no_alarm_icon_color = new_color
            self.generate_alarm_icons()

    noAlarmIconColor = Property(QColor, readNoAlarmIconColor, setNoAlarmIconColor)

    def readMinorAlarmIconColor(self) -> QColor:
        return self._minor_alarm_icon_color

    def setMinorAlarmIconColor(self, new_color) -> None:
        if self._minor_alarm_icon_color != new_color:
            self._minor_alarm_icon_color = new_color
            self.generate_alarm_icons()

    minorAlarmIconColor = Property(QColor, readMinorAlarmIconColor, setMinorAlarmIconColor)

    def readMajorAlarmIconColor(self) -> QColor:
        return self._major_alarm_icon_color

    def setMajorAlarmIconColor(self, new_color) -> None:
        if self._major_alarm_icon_color != new_color:
            self._major_alarm_icon_color = new_color
            self.generate_alarm_icons()

    majorAlarmIconColor = Property(QColor, readMajorAlarmIconColor, setMajorAlarmIconColor)

    def readInvalidAlarmIconColor(self) -> QColor:
        return self._invalid_alarm_icon_color

    def setInvalidAlarmIconColor(self, new_color) -> None:
        if self._invalid_alarm_icon_color != new_color:
            self._invalid_alarm_icon_color = new_color
            self.generate_alarm_icons()

    invalidAlarmIconColor = Property(QColor, readInvalidAlarmIconColor, setInvalidAlarmIconColor)

    def readDisconnectedAlarmIconColor(self) -> QColor:
        return self._disconnected_alarm_icon_color

    def setDisconnectedAlarmIconColor(self, new_color) -> None:
        if self._disconnected_alarm_icon_color != new_color:
            self._disconnected_alarm_icon_color = new_color
            self.generate_alarm_icons()

    disconnectedAlarmIconColor = Property(QColor, readDisconnectedAlarmIconColor, setDisconnectedAlarmIconColor)

    def generate_alarm_icons(self):
        self.alarm_icons = (
            IconFont().icon("circle", color=self.noAlarmIconColor),
            IconFont().icon("circle", color=self.minorAlarmIconColor),
            IconFont().icon("exclamation-circle", color=self.majorAlarmIconColor),
            IconFont().icon("question-circle", color=self.invalidAlarmIconColor),
            IconFont().icon("times-circle", color=self.disconnectedAlarmIconColor),
        )
        for i in range(0, self.count()):
            self.set_initial_icon_for_tab(i)


class PyDMTabWidget(QTabWidget):
    """PyDMTabWidget provides a tabbed container widget.  Each tab has an
    alarm channel property which can be used to show an alarm indicator on
    the tab.  The indicator is driven by the alarm severity of the specified
    channel, not the value.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Tab Widget
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tb = PyDMTabBar(parent=self)
        self.setTabBar(self.tb)

    def readCurrentTabAlarmChannel(self) -> QByteArray:
        """
        A channel to use for the current tab's alarm indicator.

        Returns
        -------
        str
        """
        if self.tabBar().currentTabAlarmChannel:
            return bytearray(self.tabBar().currentTabAlarmChannel.encode("utf-8"))
        else:
            return bytearray()

    def setCurrentTabAlarmChannel(self, new_alarm_channel) -> None:
        if isinstance(new_alarm_channel, QByteArray):
            self.tabBar().currentTabAlarmChannel = bytes(new_alarm_channel).decode()
        else:
            self.tabBar().currentTabAlarmChannel = str(new_alarm_channel)

    currentTabAlarmChannel = Property(QByteArray, readCurrentTabAlarmChannel, setCurrentTabAlarmChannel)

    def channels(self):
        """
        A list of the channels used by the tab widget.

        Returns
        -------
        list
        """
        return self.tabBar().channels()

    def getAlarmChannels(self):
        """alarmChannels is a property used to store the configuration of this tab bar
        when it has been created in Qt Designer.  This property isn't directly editable
        by users, they will go through the currentTabAlarmChannel property to edit this
        information."""
        return self.tabBar().getAlarmChannels()

    def setAlarmChannels(self, new_alarm_channels):
        """
        Sets the list of alarm channels for each tab.  This is needed for instantiating
        a tab widget from a .ui file, and is probably not very useful for users.
        """
        self.tabBar().setAlarmChannels(new_alarm_channels)

    def readNoAlarmIconColor(self) -> QColor:
        """
        A color to use for alarm-sensitive tabs that have PyDMWidget.ALARM_NONE severity level.
        This property can be defined in a stylesheet by using 'qproperty-noAlarmIconColor'.

        Returns
        -------
        QColor
        """
        return self.tabBar().noAlarmIconColor

    def setNoAlarmIconColor(self, new_color) -> None:
        if self.tabBar().noAlarmIconColor != new_color:
            self.tabBar().noAlarmIconColor = new_color
            self.tabBar().generate_alarm_icons()

    noAlarmIconColor = Property(QColor, readNoAlarmIconColor, setNoAlarmIconColor)

    def readMinorAlarmIconColor(self) -> QColor:
        """
        A color to use for alarm-sensitive tabs that have PyDMWidget.ALARM_MINOR severity level.
        This property can be defined in a stylesheet by using 'qproperty-minorAlarmIconColor'.

        Returns
        -------
        QColor
        """
        return self.tabBar().minorAlarmIconColor

    def setMinorAlarmIconColor(self, new_color) -> None:
        self.tabBar().minorAlarmIconColor = new_color

    minorAlarmIconColor = Property(QColor, readMinorAlarmIconColor, setMinorAlarmIconColor)

    def readMajorAlarmIconColor(self) -> QColor:
        """
        A color to use for alarm-sensitive tabs that have PyDMWidget.ALARM_MAJOR severity level.
        This property can be defined in a stylesheet by using 'qproperty-majorAlarmIconColor'.

        Returns
        -------
        QColor
        """
        return self.tabBar().majorAlarmIconColor

    def setMajorAlarmIconColor(self, new_color) -> None:
        self.tabBar().majorAlarmIconColor = new_color

    majorAlarmIconColor = Property(QColor, readMajorAlarmIconColor, setMajorAlarmIconColor)

    def readInvalidAlarmIconColor(self) -> QColor:
        """
        A color to use for alarm-sensitive tabs that have PyDMWidget.ALARM_INVALID severity level.
        This property can be defined in a stylesheet by using 'qproperty-majorAlarmIconColor'.

        Returns
        -------
        QColor
        """
        return self.tabBar().invalidAlarmIconColor

    def setInvalidAlarmIconColor(self, new_color) -> None:
        self.tabBar().invalidAlarmIconColor = new_color

    invalidAlarmIconColor = Property(QColor, readInvalidAlarmIconColor, setInvalidAlarmIconColor)

    def readDisconnectedAlarmIconColor(self) -> QColor:
        """
        A color to use for alarm-sensitive tabs that have PyDMWidget.ALARM_DISCONNECTED severity level.
        This property can be defined in a stylesheet by using 'qproperty-disconnectedAlarmIconColor'.

        Returns
        -------
        QColor
        """
        return self.tabBar().disconnectedAlarmIconColor

    def setDisconnectedAlarmIconColor(self, new_color) -> None:
        self.tabBar().disconnectedAlarmIconColor = new_color

    disconnectedAlarmIconColor = Property(QColor, readDisconnectedAlarmIconColor, setDisconnectedAlarmIconColor)

    alarmChannels = Property("QStringList", getAlarmChannels, setAlarmChannels, designable=False)

    # We make a bunch of dummy properties to block out properties available on QTabWidget,
    # but that we don't want to support on PyDMTabWidget.
    currentTabIcon = Property("QIcon", None, None, designable=False)
    documentMode = Property(bool, None, None, designable=False)
    tabsClosable = Property(bool, None, None, designable=False)
    movable = Property(bool, None, None, designable=False)
