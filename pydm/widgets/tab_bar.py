from pydm.PyQt.QtGui import QTabBar, QTabWidget, QIcon, QBrush, QColor, QVBoxLayout, QWidget, QLabel
from .base import PyDMWidget
from .channel import PyDMChannel
from pydm.PyQt.QtCore import pyqtProperty, Q_ENUMS, Qt, QVariant
from functools import partial
from ..utilities.iconfont import IconFont

class PyDMTabBar(QTabBar, PyDMWidget):                
    def __init__(self, parent=None):
        super(PyDMTabBar, self).__init__(parent=parent)
        self.tab_channels = {}
        self._channels = None
        self.alarm_icons = (IconFont().icon('circle', color=self.qcolor_for_alarm(self.ALARM_NONE, alarm_type=self.ALARM_INDICATOR)), 
                        IconFont().icon('circle', color=self.qcolor_for_alarm(self.ALARM_MINOR, alarm_type=self.ALARM_INDICATOR)),
                        IconFont().icon('exclamation-circle', color=self.qcolor_for_alarm(self.ALARM_MAJOR, alarm_type=self.ALARM_INDICATOR)),
                        IconFont().icon('question-circle', color=self.qcolor_for_alarm(self.ALARM_INVALID, alarm_type=self.ALARM_INDICATOR)),
                        IconFont().icon('times-circle', color=self.qcolor_for_alarm(self.ALARM_DISCONNECTED, alarm_type=self.ALARM_INDICATOR)))
    
    @pyqtProperty(str)
    def currentTabAlarmChannel(self):
        """A channel to use for this tab's alarm indicator."""
        if self.currentIndex() < 0:
            return
        return str(self.tab_channels.get(self.currentIndex(),""))
    
    @currentTabAlarmChannel.setter
    def currentTabAlarmChannel(self, new_alarm_channel):
        if self.currentIndex() < 0:
            return
        self.set_channel_for_tab(self.currentIndex(), new_alarm_channel)
    
    def set_channel_for_tab(self, index, channel):
        self.tab_channels[index] = str(channel)
        if index < self.count():
            self.set_initial_icon_for_tab(index)

    def channels(self):
        #Note that because we cache the list of channels, tabs added or removed after this method
        #is called will not ever get channel objects created, and will never connect to data sources.
        if self._channels is not None:
            return self._channels
        
        self._channels = []
        for index in range(0,self.count()):
            channel = str(self.tab_channels[index])
            if channel != "":
                self._channels.append(PyDMChannel(address=str(channel), 
                                                connection_slot=partial(self.connection_changed_for_tab, index), 
                                                severity_slot=partial(self.alarm_changed_for_tab, index)))
        return self._channels

    def connection_changed_for_tab(self, index, conn):
        if not conn:
            self.setTabIcon(index, self.alarm_icons[self.ALARM_DISCONNECTED])
    
    def alarm_changed_for_tab(self, index, alarm_state):
        self.setTabIcon(index, self.alarm_icons[alarm_state])

    def getAlarmChannels(self):
        """alarmChannels is a property used to store the configuration of this tab bar
        when it has been created in Qt Designer.  This property isn't directly editable
        by users, they will go through the currentTabAlarmChannel property to edit this
        information."""
        return [str(self.tab_channels[i]) for i in range(0,self.count())]
    
    def setAlarmChannels(self, new_alarm_channels):
        for tab_number, channel_address in enumerate(new_alarm_channels):
            self.set_channel_for_tab(tab_number, channel_address)
    
    def set_initial_icon_for_tab(self, index):
        channel = self.tab_channels.get(index, "")
        if channel in ("", "None", None):
            self.setTabIcon(index, QIcon())
        else:
            self.setTabIcon(index, self.alarm_icons[4]) 
    
    def tabInserted(self, index):
        if index not in self.tab_channels:
            self.tab_channels[index] = ""
        self.set_initial_icon_for_tab(index)
        
class PyDMTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super(PyDMTabWidget, self).__init__(parent=parent)
        self.setTabBar(PyDMTabBar(parent=self))
    
    @pyqtProperty(str)
    def currentTabAlarmChannel(self):
        """A channel to use for this tab's alarm indicator."""
        return self.tabBar().currentTabAlarmChannel
    
    @currentTabAlarmChannel.setter
    def currentTabAlarmChannel(self, new_alarm_channel):
        self.tabBar().currentTabAlarmChannel = new_alarm_channel
    
    def channels(self):
        return self.tabBar().channels()
    
    def getAlarmChannels(self):
        """alarmChannels is a property used to store the configuration of this tab bar
        when it has been created in Qt Designer.  This property isn't directly editable
        by users, they will go through the currentTabAlarmChannel property to edit this
        information."""
        #return self._ac
        return self.tabBar().getAlarmChannels()
    
    def setAlarmChannels(self, new_alarm_channels):
        #self._ac = new_alarm_channels
        self.tabBar().setAlarmChannels(new_alarm_channels)
        
    alarmChannels = pyqtProperty("QStringList", getAlarmChannels, setAlarmChannels, designable=False)
    #We make a bunch of dummy properties to block out properties available on QTabWidget,
    #but that we don't want to support on PyDMTabWidget.
    currentTabIcon = pyqtProperty("QIcon", None, None, designable=False)
    documentMode = pyqtProperty(bool, None, None, designable=False)
    tabsClosable = pyqtProperty(bool, None, None, designable=False)
    movable = pyqtProperty(bool, None, None, designable=False)
    