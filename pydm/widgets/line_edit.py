from functools import partial
from PyQt4.QtGui import QLineEdit, QApplication, QColor, QPalette, QMenu
from PyQt4.QtCore import Qt,pyqtSignal,pyqtSlot,pyqtProperty
import pydm.utilities
from channel import PyDMChannel

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
        
        #Create Context Menu upon Right Click
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.launchMenu)
        self.menu     = QMenu(self)
        self.unitMenu = self.menu.addMenu('Convert Units')
        self.createUnitOptions()

    def focusOutEvent(self, event):
        """
        Unselect PyDMLineEdit in PyDMApplication
        
        Overwrites the function called when a user leaves a PyDMLineEdit
        without pressing return.  Resets the value of the text field to the
        current channel value.
        """
        if self._display != None:
            self.setText(self._display)
        super(PyDMLineEdit, self).focusOutEvent(event)
 

    @pyqtSlot(float)
    @pyqtSlot(int)
    @pyqtSlot(str)
    def receiveValue(self,value):
        """
        Receive and update the PyDMLineEdit for a new channel value

        The actual value of the input is saved as well as the type received.
        This also resets the PyDMLineEdit display text using
        :method:`.setDisplay`

        :param value: The new value of the channel
        """
        self._value       = value
        self._channeltype = type(value)
        self.setDisplay() 
  
    
    def setDisplay(self):
        """
        Set the text display of the PyDMLineEdit.

        The original value given by the PV is converted to a text entry based
        on the current settings for a scale value, precision, a user-defined
        format, and the current units. If the user is currently entering a
        value, the text will not be changed but will be saved if the user
        leaves the widget without entering a new value
        """
        value = self._value

        if not isinstance(value,QString):
            if self._scale and value:
                value *= self._channeltype(self._scale)
            
            if self._prec and self._useprec:
                value = self._prec.format(value)
            else:
                value = str(value)
        
        if self._userformat:
            value = self._userformat.format(value)
        
        if self._units and self.showUnits:
            value = self._unitformat.format(value)
        
        self._display = str(value)
        
        if not self.hasFocus():
            self.setText(self._display)

    @pyqtSlot()
    def sendValue(self):
        """
        Emit a :attr:`send_value_signal` to update channel value.

        The text is cleaned of all units, user-formatting and scale values
        before being sent back to the channel.
        """
        send_value = str(self.text())
        
        #Clean text of all formatting
        if self._unitformat:
            send_value = send_value.strip(self._unitformat)
        
        if self._userformat:
            send_value = send_value.strip(self._userformat)
        
        #Remove scale factor
        if self._scale and self._channeltype != QString:
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
        Accept a precision to display a channel's value.
        """
        if value >= 0:
            self._prec = '{{:.{:}f}}'.format(str(value))
            self.setDisplay()

    @pyqtProperty(bool,doc=
    """
    A choice whether or not to use the precision given in the EPICS .PREC field
    """)
    def usePrecision(self):
        return self._useprec

    @usePrecision.setter
    def usePrecision(self,choice):
        if self._useprec != choice:
            self._useprec = choice


    @pyqtSlot(str)
    def receiveUnits(self,unit):
        """
        Accept a precision to display a channel's value
        """
        self._units = str(unit)
        self._scale = 1
        self._unitformat = '{{:}} {:}'.format(unit)
        self.setDisplay()
        self.createUnitOptions()
        
    
    def createUnitOptions(self):
        """
        Create the menu for displaying possible unit values
        """
        self.unitMenu.clear()
        units = pydm.utilities.find_unit_options(self._units)
        if units and self._useunits:
            for choice in units:
                self.unitMenu.addAction(choice,partial(self.apply_conversion,choice))
        else:
            self.unitMenu.addAction('No Unit Conversions found')
 
    @pyqtProperty(bool,doc=
    """
    A choice whether or not to use the units given in the EPICS .EGU field
    """
    )
    def showUnits(self):
        return self._useunits

    @showUnits.setter
    def showUnits(self,choice):
        if self._useunits != choice:
            self._useunits = choice

    
    def apply_conversion(self,unit):
        """
        Convert the current unit to a different one
        """
        if not self._units:
            logger.warning('Attempting to convert PyDMLineEdit unit, but no '\
                           'initial units supplied')
            return None

        scale = pydm.utilities.convert(str(self._units),unit) 
        if scale:
            self._scale = scale*float(self._scale)
            self._units = unit
            self._unitformat = '{{:}} {:}'.format(unit)
            self.clearFocus()
            self.setDisplay()
    
    def launchMenu(self,point):
        return self.menu.exec_(self.mapToGlobal(point))

    @pyqtProperty(QString,doc=
    """
    A user defined format for the text display value
    """
    )
    def userFormat(self):
        return QString.fromAscii(self._userformat)

    @userFormat.setter
    def userFormat(self,value):
        if self._userformat != str(value):
            self._userformat = str(value)

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
        return [PyDMChannel(address=self.channel,
                            value_slot=self.receiveValue,
                            value_signal=self.send_value_signal,
                            prec_slot = self.receivePrecision,
                            unit_slot = self.receiveUnits,
                            write_access_slot=self.writeAccessChanged,
                           )]
