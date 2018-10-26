from qtpy.QtWidgets import (QTabBar, QTabWidget, QWidget)
from qtpy.QtGui import QIcon, QColor
from .base import PyDMWidget
from .channel import PyDMChannel
from qtpy.QtCore import Property
from functools import partial
from ..utilities.iconfont import IconFont


class PyDMTabBar(QTabBar, PyDMWidget):
    """PyDMTabBar is used internally by PyDMTabWidget, and shouldn't be directly used on its own."""

    def __init__(self, parent=None):
        super(PyDMTabBar, self).__init__(parent=parent)
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

    @Property(str)
    def currentTabAlarmChannel(self):
        """A channel to use for this tab's alarm indicator."""
        if self.currentIndex() < 0:
            return
        return str(self.tab_channels.get(self.currentIndex(), "")["address"])

    @currentTabAlarmChannel.setter
    def currentTabAlarmChannel(self, new_alarm_channel):
        if self.currentIndex() < 0:
            return
        self.set_channel_for_tab(self.currentIndex(), new_alarm_channel)

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
            # Create PyDMChannel and connecdt
            chan = PyDMChannel(address=str(channel),
                               connection_slot=partial(self.connection_changed_for_tab, index),
                               severity_slot=partial(self.alarm_changed_for_tab, index))
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
            if self.tab_connection_status.get(index,
                                              False) and index in self.tab_alarm_severity:
                icon_index = self.tab_alarm_severity[index]
            self.setTabIcon(index, self.alarm_icons[icon_index])

    def tabInserted(self, index):
        super(PyDMTabBar, self).tabInserted(index)
        if index not in self.tab_channels:
            self.tab_channels[index]["address"] = ""
        self.set_initial_icon_for_tab(index)

    @Property(QColor)
    def noAlarmIconColor(self):
        return self._no_alarm_icon_color

    @noAlarmIconColor.setter
    def noAlarmIconColor(self, new_color):
        if self._no_alarm_icon_color != new_color:
            self._no_alarm_icon_color = new_color
            self.generate_alarm_icons()

    @Property(QColor)
    def minorAlarmIconColor(self):
        return self._minor_alarm_icon_color

    @minorAlarmIconColor.setter
    def minorAlarmIconColor(self, new_color):
        if self._minor_alarm_icon_color != new_color:
            self._minor_alarm_icon_color = new_color
            self.generate_alarm_icons()

    @Property(QColor)
    def majorAlarmIconColor(self):
        return self._major_alarm_icon_color

    @majorAlarmIconColor.setter
    def majorAlarmIconColor(self, new_color):
        if self._major_alarm_icon_color != new_color:
            self._major_alarm_icon_color = new_color
            self.generate_alarm_icons()

    @Property(QColor)
    def invalidAlarmIconColor(self):
        return self._invalid_alarm_icon_color

    @invalidAlarmIconColor.setter
    def invalidAlarmIconColor(self, new_color):
        if self._invalid_alarm_icon_color != new_color:
            self._invalid_alarm_icon_color = new_color
            self.generate_alarm_icons()

    @Property(QColor)
    def disconnectedAlarmIconColor(self):
        return self._disconnected_alarm_icon_color

    @disconnectedAlarmIconColor.setter
    def disconnectedAlarmIconColor(self, new_color):
        if self._disconnected_alarm_icon_color != new_color:
            self._disconnected_alarm_icon_color = new_color
            self.generate_alarm_icons()

    def generate_alarm_icons(self):
        self.alarm_icons = (
            IconFont().icon('circle', color=self.noAlarmIconColor),
            IconFont().icon('circle', color=self.minorAlarmIconColor),
            IconFont().icon('exclamation-circle',
                            color=self.majorAlarmIconColor),
            IconFont().icon('question-circle',
                            color=self.invalidAlarmIconColor),
            IconFont().icon('times-circle',
                            color=self.disconnectedAlarmIconColor)
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
        super(PyDMTabWidget, self).__init__(parent=parent)
        self.tb = PyDMTabBar(parent=self)
        self.setTabBar(self.tb)

    @Property(str)
    def currentTabAlarmChannel(self):
        """
        A channel to use for the current tab's alarm indicator.

        Returns
        -------
        str
        """
        return self.tabBar().currentTabAlarmChannel

    @currentTabAlarmChannel.setter
    def currentTabAlarmChannel(self, new_alarm_channel):
        self.tabBar().currentTabAlarmChannel = new_alarm_channel

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

    @Property(QColor)
    def noAlarmIconColor(self):
        """
        A color to use for alarm-sensitive tabs that have PyDMWidget.ALARM_NONE severity level.
        This property can be defined in a stylesheet by using 'qproperty-noAlarmIconColor'.

        Returns
        -------
        QColor
        """
        return self.tabBar().noAlarmIconColor

    @noAlarmIconColor.setter
    def noAlarmIconColor(self, new_color):
        if self.tabBar().noAlarmIconColor != new_color:
            self.tabBar().noAlarmIconColor = new_color
            self.tabBar().generate_alarm_icons()

    @Property(QColor)
    def minorAlarmIconColor(self):
        """
        A color to use for alarm-sensitive tabs that have PyDMWidget.ALARM_MINOR severity level.
        This property can be defined in a stylesheet by using 'qproperty-minorAlarmIconColor'.

        Returns
        -------
        QColor
        """
        return self.tabBar().minorAlarmIconColor

    @minorAlarmIconColor.setter
    def minorAlarmIconColor(self, new_color):
        self.tabBar().minorAlarmIconColor = new_color

    @Property(QColor)
    def majorAlarmIconColor(self):
        """
        A color to use for alarm-sensitive tabs that have PyDMWidget.ALARM_MAJOR severity level.
        This property can be defined in a stylesheet by using 'qproperty-majorAlarmIconColor'.

        Returns
        -------
        QColor
        """
        return self.tabBar().majorAlarmIconColor

    @majorAlarmIconColor.setter
    def majorAlarmIconColor(self, new_color):
        self.tabBar().majorAlarmIconColor = new_color

    @Property(QColor)
    def invalidAlarmIconColor(self):
        """
        A color to use for alarm-sensitive tabs that have PyDMWidget.ALARM_INVALID severity level.
        This property can be defined in a stylesheet by using 'qproperty-majorAlarmIconColor'.

        Returns
        -------
        QColor
        """
        return self.tabBar().invalidAlarmIconColor

    @invalidAlarmIconColor.setter
    def invalidAlarmIconColor(self, new_color):
        self.tabBar().invalidAlarmIconColor = new_color

    @Property(QColor)
    def disconnectedAlarmIconColor(self):
        """
        A color to use for alarm-sensitive tabs that have PyDMWidget.ALARM_DISCONNECTED severity level.
        This property can be defined in a stylesheet by using 'qproperty-disconnectedAlarmIconColor'.

        Returns
        -------
        QColor
        """
        return self.tabBar().disconnectedAlarmIconColor

    @disconnectedAlarmIconColor.setter
    def disconnectedAlarmIconColor(self, new_color):
        self.tabBar().disconnectedAlarmIconColor = new_color

    alarmChannels = Property("QStringList", getAlarmChannels,
                             setAlarmChannels, designable=False)

    # We make a bunch of dummy properties to block out properties available on QTabWidget,
    # but that we don't want to support on PyDMTabWidget.
    currentTabIcon = Property("QIcon", None, None, designable=False)
    documentMode = Property(bool, None, None, designable=False)
    tabsClosable = Property(bool, None, None, designable=False)
    movable = Property(bool, None, None, designable=False)
