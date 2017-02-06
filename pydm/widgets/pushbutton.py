import sys
import logging
from os import path


from .channel import PyDMChannel
from ..PyQt.QtGui import QPushButton
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty

logger = logging.getLogger(__name__)

class PyDMPushButton(QPushButton):
    """
    Basic PushButton to send a fixed value.

    The PyDMPushButton is meant to hold a specific value, and send that value
    to a channel when it is clicked, much like the MessageButton does in EDM.
    The PyDMPushButton works in two different modes of operation, first, a
    fixed value can be given to the :attr:`.pressValue` attribute, whenever the
    button is clicked a signal containing this value will be sent to the
    connected channel. This is the default behavior of the button. However, if
    the :attr:`.relativeChange` is set to True, the fixed value will be added
    to the current value of the channel. This means that the button will
    increment a channel by a fixed amount with every click, a consistent
    relative move
    
    Parameters
    ----------
    pressValue : int, float, str
        Value to be sent when the button is clicked
    
    channel : str
        ID of channel to manipulate

    parent : QObject, optional
        Parent of PyDMPushButton

    label : str, optional
        String to place on button

    icon : QIcon, optional
        An Icon to display on the PyDMPushButton


    relative : bool, optional
        Choice to have the button peform a relative put, instead of always
        setting to an absolute value
    """
    __pyqtSignals__ = ("send_value_signal(str)",)
    send_value_signal = pyqtSignal([int],[float],[str])

    def __init__(self,parent=None,label=None,icon=None,
                 pressValue=None,relative=False, 
                 channel= None):
        if icon:
            super(PyDMPushButton,self).__init__(icon,label,parent)
        elif label:
            super(PyDMPushButton,self).__init__(label,parent)
        else:
            super(PyDMPushButton,self).__init__(parent)

        self._value       = None
        self._pressValue  = pressValue 
        self._relative    = relative

        self._channel     = channel
        self._channeltype = type(self._value)
        self._connected = False
        self._write_access = False
        self.update_enabled_state()
        self.clicked.connect(self.sendValue)


    @pyqtProperty(str,doc=
    """
    The channel address to attach the PyDMPushButton

    The actual signal/slot attachment is done at the application level of the
    PyDM module.
    """
    )
    def channel(self):
        return str(self._channel)

    @channel.setter
    def channel(self,value):
        if self._channel != value:
            self._channel = str(value)


    @pyqtProperty(str,doc=
    """
    This property holds the value to send back through the channel.

    The type of this value does not matter because it is automatically
    converted to match the prexisting value type of the channel. However, the
    sign of the value matters for both the fixed and relative modes.
    """
    )
    def pressValue(self):
        return str(self._pressValue)
    
    @pressValue.setter
    def pressValue(self,value):
        if value != self._pressValue:
            self._pressValue = value 
   
    
    @pyqtProperty(bool,doc=
    """
    The mode of operation of the PyDMPushButton

    If set to True, the :attr:`pressValue` will be added to the current value
    of the channel. If False, the :attr:`pressValue` will be sent without any
    operation.

    This flag will be ignored if the connected channel sends a str type value
    to :meth:`.receiveValue`. This is designed to eliminate the undesirable
    behavior of concantenating strings as opposed to doing mathematical
    addition. 
    """
    )
    def relativeChange(self):
        return self._relative

    @relativeChange.setter
    def relativeChange(self,choice):
        if self._relative != choice:
            self._relative = choice
    
    
    @pyqtSlot(int)
    @pyqtSlot(float)
    @pyqtSlot(str)
    def receiveValue(self, new_value):
        """
        Receive and store both the value and type of the channel

        While the channel value is not displayed inherently in the Widget, the
        value is stored in order to accomadate the relative mode of operation.
        Also, the type of the incoming value is stored as well. This allows the
        Widget to send back the same Python type as received from the plugin. 
        """
        self._value       = new_value
        self._channeltype = type(new_value)
    
    @pyqtSlot(bool)
    def connectionStateChanged(self, connected):
      self._connected = connected
      self.update_enabled_state()
    
    @pyqtSlot(bool)
    def writeAccessChanged(self, write_access):
      self._write_access = write_access
      self.update_enabled_state()
    
    def update_enabled_state(self):
      self.setEnabled(self._write_access and self._connected)

    @pyqtSlot()
    def sendValue(self):
        """
        Send a new value to the channel

        This function interprets the settings of the PyDMPushButton and sends
        the appropriate value out through the :attr:`.send_value_signal`.   
        """
        if not self._pressValue or self._value is None:
            return None

        if not self._relative or self._channeltype == str:
            self.send_value_signal[self._channeltype].emit(self._channeltype(self._pressValue))
        else:
            send_value = self._value + self._channeltype(self._pressValue)
            self.send_value_signal[self._channeltype].emit(send_value)


    @pyqtSlot(int)
    @pyqtSlot(float)
    @pyqtSlot(str)
    def updatePressValue(self,value):
        """
        Update the pressValue of a function by passing a signal to the
        PyDMPushButton

        This is useful to dynmamically change the pressValue of the button
        during runtime. This enables the applied value to be linked to the
        state of a different widget, say a QLineEdit or QSlider
        """
        try:
            self._pressValue = self._channeltype(value)
        except ValueError:
            logger.warn('{:} is not a valid pressValue '\
                        'for {:}'.format(value,self.channel))

    def channels(self):
        """
        Return a list of the channels connected to the PyDMPushbutton.
        """
        return [PyDMChannel(address      = self.channel,
                            value_slot   = self.receiveValue,
                            value_signal = self.send_value_signal,
                            connection_slot = self.connectionStateChanged,
                            write_access_slot = self.writeAccessChanged),
               ]

