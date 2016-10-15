import sys
import logging
from os import path


from channel import PyDMChannel
from PyQt4.QtGui import QPushButton
from PyQt4.QtCore import QString,pyqtSignal, pyqtSlot, pyqtProperty

logger = logging.getLogger(__name__)

class PyDMPushButton(QPushButton):
    """
    Basic PushButton to modify an EPICS PV.

    The PyDMPushButton is meant to hold a specific value, and send that value
    to a PV when it is clicked.  
    The PyDMPushbutton works in two different modes of operation 
    """
    __pyqtSignals__ = ("send_value_signal(Qstring)",)

    send_value_signal = pyqtSignal([int],[float],[str])


    def __init__(self,button_label,parent=None,
                 pressValue = None, relative = False, 
                 init_channel = None):
        super(PyDMPushButton,self).__init__(button_label,parent=parent)
        
        self._value       = None
        self._pressValue  = pressValue 
        self._relative    = relative

        self._channel     = init_channel
        self._channeltype = type(self._value)

        self.clicked.connect(self.sendValue)


    @pyqtProperty(int)
    @pyqtProperty(float)
    @pyqtProperty(str)
    def pressValue(self):
        return self._pressValue
    
    @pressValue.setter
    def pressValue(self,value):
        if value != self._pressValue:
            self._pressValue = value 
   

    @pyqtSlot(int)
    @pyqtSlot(float)
    @pyqtSlot(str)
    def receiveValue(self, new_value):
        self._value       = new_value
        self._channeltype = type(new_value)

    @pyqtSlot()
    def sendValue(self):
        """
        Emit a :attr:`.send_value_signal` with the desired PV value
        """
        if not self._relative or self._channeltype == str:
            self.send_value_signal[self._channeltype].emit(self._channeltype(self._pressValue))
        else:
            send_value = self._value + self._channeltype(self._pressValue)
            self.send_value_signal[self._channeltype].emit(send_value)


    @pyqtProperty(bool)
    def relativeChange(self):
        return self._relative

    @relativeChange.setter
    def relativeChange(self,choice):
        if self._relative != choice:
            self._relative = choice

    @pyqtProperty('QString')
    def channel(self):
        return QString.fromAscii(self._channel)


    @channel.setter
    def setChannel(self):
        if self._channel != value:
            self._channel = str(value)

    def channels(self):
        return [PyDMChannel(address=self.channel,
                            value_slot   = self.receiveValue,
                            value_signal = self.send_value_signal),
               ]

    
    
if __name__ == '__main__':
    #Append Path
    dir = path.join(path.dirname(path.abspath(__file__)),'../..')
    sys.path.insert(0,dir)
    
    import pydm
    app = pydm.PyDMApplication(sys.argv)
    widget = PyDMPushButton('Push Me',
                            init_channel='ca://TST:PYQT:FLOAT',
                            pressValue='1002',
                           )
    widget.relativeChange = True
    widget.show()
    sys.exit(app.exec_())
