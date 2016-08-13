from channel import PyDMChannel

from PyQt4.QtGui import QLineEdit, QApplication, QColor, QPalette
from PyQt4.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QState, QStateMachine, QPropertyAnimation

class PyDMLineEdit(QLineEdit):
    """
    Writeable text field to send and display channel values
    """
    __pyqtSignals__ = ("send_value_signal(str)",
                       "connected_signal()",
                       "disconnected_signal()", 
                       "no_alarm_signal()", 
                       "minor_alarm_signal()", 
                       "major_alarm_signal()", 
                       "invalid_alarm_signal()"
                      )
                     
    send_value_signal = pyqtSignal([int],[float],[str])
  
    def __init__(self,parent=None,channel=None):
        super(PyDMLineEdit, self).__init__(parent)
        self._value       = None
        self._display     = None
        self._channeltype = None
        self._channel     = channel

        self._useprec    = True
        self._prec       = None
        
        self._userformat = None 
        
        self._scale      = 1
        
        self._useunits   = True
        self._units      = None
        self._unitformat = None
        
        self.returnPressed.connect(self.sendValue)
  
    
    def focusOutEvent(self, event):
        """
        Unselect PyDMLineEdit in PyDMApplication

        Called when a user leaves a PyDMLineEdit without pressing return.
        Resets the value of the text field to the current channel value
        """
        if self._value != None:
            self.setText(self._display)
        super(PyDMLineEdit, self).focusOutEvent(event)
 

    @pyqtSlot(float)
    @pyqtSlot(int)
    @pyqtSlot(str)
    def receiveValue(self,value):
        """
        Receive and update the PyDMLineEdit for a new channel value
        """
        self._value       = value
        self._channeltype = type(value)
       
        if not isinstance(value,str):
            if self._scale:
                value *= self._scale
            
            if self._prec and self._useprec:
                value = self._prec.format(value)
            else:
                value = str(value)
        
        if self._userformat:
            value = self._userformat.format(value)
        
        if self._units and self._useunits:
            value = self._unitformat.format(value)
        
        self._display = str(value)
        
        if not self.hasFocus():
            self.setText(self._display)
  
  
    @pyqtSlot()
    def sendValue(self):
        """
        Emit a :attr:`send_value_signal` to update channel value.
        """
        send_value = self.text()
        
        #Clean text of all formatting
        if self._unitformat:
            send_value.strip(self._unitformat)
        
        if self._userformat:
            send_value.strip(self._userformat)
        
        #Remove scale factor
        if self._scale and self._channeltype != str:
            send_value = (self._channeltype(send_value)
                          / self._channeltype(self._scale))
         
        self.send_value_signal[self._channeltype].emit(self._channeltype(send_value))
   

    @pyqtSlot(bool)
    def writeAccessChanged(self, write_access):
        """
        Change the PyDMLineEdit to read only if write access is denied
        """
        self.setReadOnly(not write_access)
 

    @pyqtSlot(int)
    def receivePrecision(self,value):
        """
        Accept a precision to display a channel's value
        """
        self._prec = value


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
   

    def channels(self):
        return [PyDMChannel(address=self.channel,value_slot=self.receiveValue,
#                            write_access_slot=self.writeAccessChanged,
                            value_signal=self.send_value_signal)]
