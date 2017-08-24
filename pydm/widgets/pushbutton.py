import hashlib

from ..PyQt.QtGui import QPushButton, QMessageBox, QInputDialog, QLineEdit
from ..PyQt.QtCore import pyqtSlot, pyqtProperty
from .base import PyDMWritableWidget

class PyDMPushButton(QPushButton, PyDMWritableWidget):
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
    parent : QObject, optional
        Parent of PyDMPushButton

    init_channel : str, optional
        ID of channel to manipulate

    pressValue : int, float, str
        Value to be sent when the button is clicked

    label : str, optional
        String to place on button

    icon : QIcon, optional
        An Icon to display on the PyDMPushButton

    relative : bool, optional
        Choice to have the button perform a relative put, instead of always
        setting to an absolute value
    """
    DEFAULT_CONFIRM_MESSAGE = "Are you sure you want to proceed ?"

    def __init__(self,parent=None,label=None,icon=None,
                 pressValue=None,relative=False, 
                 init_channel= None):
        if icon:
            super().__init__(icon,label,parent, init_channel=init_channel)
        elif label:
            super().__init__(label,parent, init_channel=init_channel)
        else:
            super().__init__(parent, init_channel=init_channel)

        self._pressValue  = pressValue 
        self._relative    = relative

        self._show_confirm_dialog = False
        self._confirm_message = PyDMPushButton.DEFAULT_CONFIRM_MESSAGE
        self._password_protected = False
        self._password = ""
        self._protected_password = ""
        self.clicked.connect(self.sendValue)

    @pyqtProperty(bool, doc=
    """
    Wether or not this button is password protected.
    """
    )
    def passwordProtected(self):
        return self._password_protected

    @passwordProtected.setter
    def passwordProtected(self, value):
        if self._password_protected != value:
            self._password_protected = value

    @pyqtProperty(str, doc=
    """
    Password to be encrypted using SHA256.
    """
    )
    def password(self):
        return ""

    @password.setter
    def password(self, value):
        if value is not None and value != "":
            sha = hashlib.sha256()
            sha.update(value.encode())
            self._protected_password = sha.hexdigest()
    
    @pyqtProperty(str, doc=
    """
    The encrypted password
    """
    )
    def protectedPassword(self):
        return self._protected_password

    @protectedPassword.setter
    def protectedPassword(self, value):
        if self._protected_password != value:
            self._protected_password = value

    @pyqtProperty(bool, doc=
    """
    Wether or not to display a confirmation dialog.
    """
    )
    def showConfirmDialog(self):
        return self._show_confirm_dialog

    @showConfirmDialog.setter
    def showConfirmDialog(self, value):
        if self._show_confirm_dialog != value:
            self._show_confirm_dialog = value

    @pyqtProperty(str, doc=
    """
    Message to be displayed at the Confirmation dialog.
    """
    )
    def confirmMessage(self):
        return self._confirm_message

    @confirmMessage.setter
    def confirmMessage(self, value):
        if self._confirm_message != value:
            self._confirm_message = value

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
    
    def confirm_dialog(self):
        if self._show_confirm_dialog:
            if self._confirm_message == "":
                self._confirm_message = PyDMPushButton.DEFAULT_CONFIRM_MESSAGE
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setText(self._confirm_message)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.No)
            ret = msg.exec_()
            if ret == QMessageBox.No:
                return False
        return True
    
    def validate_password(self):
        if not self._password_protected:
            return True

        pwd, ok = QInputDialog.getText(None, "Authentication", "Please enter your password:", QLineEdit.Password,"")
        pwd = str(pwd)
        if not ok or pwd == "":
            return False

        sha = hashlib.sha256()
        sha.update(pwd.encode())
        pwd_encrypted = sha.hexdigest()
        if pwd_encrypted != self._protected_password:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Invalid password.")
            msg.setWindowTitle("Error")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setDefaultButton(QMessageBox.Ok)
            msg.setEscapeButton(QMessageBox.Ok)
            msg.exec_()
            return False
        return True

    def alarm_severity_changed(self, new_alarm_severity):
        """
        Callback invoked when the Channel alarm severity is changed.
        This callback is not processed if the widget has no channel associated with it.
        This callback handles the composition of the stylesheet to be applied and the call
        to update to redraw the widget with the needed changes for the new state.

        Parameters
        ----------
        new_alarm_severity : int
            The new severity where 0 = NO_ALARM, 1 = MINOR, 2 = MAJOR and 3 = INVALID
        """
        pass

    @pyqtSlot()
    def sendValue(self):
        """
        Send a new value to the channel

        This function interprets the settings of the PyDMPushButton and sends
        the appropriate value out through the :attr:`.send_value_signal`.   
        """
        if not self._pressValue or self.value is None:
            return None
        if not self.confirm_dialog():
            return None

        if not self.validate_password():
            return None

        if not self._relative or self.channeltype == str:
            self.send_value_signal[self.channeltype].emit(self.channeltype(self._pressValue))
        else:
            send_value = self.value + self.channeltype(self._pressValue)
            self.send_value_signal[self.channeltype].emit(send_value)


    @pyqtSlot(int)
    @pyqtSlot(float)
    @pyqtSlot(str)
    def updatePressValue(self,value):
        """
        Update the pressValue of a function by passing a signal to the
        PyDMPushButton

        This is useful to dynamically change the pressValue of the button
        during runtime. This enables the applied value to be linked to the
        state of a different widget, say a QLineEdit or QSlider
        """
        try:
            self.pressValue = self.channeltype(value)
        except ValueError:
            print('{:} is not a valid pressValue '\
                        'for {:}'.format(value,self.channel))
