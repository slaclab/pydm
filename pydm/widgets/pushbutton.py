import hashlib

from qtpy.QtWidgets import QPushButton, QMessageBox, QInputDialog, QLineEdit
from qtpy.QtCore import Slot, Property
from .base import PyDMWritableWidget

import logging
logger = logging.getLogger(__name__)


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

    label : str, optional
        String to place on button

    icon : QIcon, optional
        An Icon to display on the PyDMPushButton

    pressValue : int, float, str
        Value to be sent when the button is clicked

    relative : bool, optional
        Choice to have the button perform a relative put, instead of always
        setting to an absolute value

    init_channel : str, optional
        ID of channel to manipulate

    """

    DEFAULT_CONFIRM_MESSAGE = "Are you sure you want to proceed?"

    def __init__(self, parent=None, label=None, icon=None,
                 pressValue=None, relative=False,
                 init_channel=None):
        if icon:
            QPushButton.__init__(self, icon, label, parent)
        elif label:
            QPushButton.__init__(self, label, parent)
        else:
            QPushButton.__init__(self, parent)
        PyDMWritableWidget.__init__(self, init_channel=init_channel)
        self._pressValue = pressValue
        self._relative = relative
        self._alarm_sensitive_border = False
        self._show_confirm_dialog = False
        self._confirm_message = PyDMPushButton.DEFAULT_CONFIRM_MESSAGE
        self._password_protected = False
        self._password = ""
        self._protected_password = ""
        self.clicked.connect(self.sendValue)

    @Property(bool)
    def passwordProtected(self):
        """
        Whether or not this button is password protected.

        Returns
        -------
        bool
        """
        return self._password_protected

    @passwordProtected.setter
    def passwordProtected(self, value):
        """
        Whether or not this button is password protected.

        Parameters
        ----------
        value : bool
        """
        if self._password_protected != value:
            self._password_protected = value

    @Property(str)
    def password(self):
        """
        Password to be encrypted using SHA256.

        .. warning::
            To avoid issues exposing the password this method
            always returns an empty string.

        Returns
        -------
        str
        """
        return ""

    @password.setter
    def password(self, value):
        """
        Password to be encrypted using SHA256.

        Parameters
        ----------
        value : str
            The password to be encrypted
        """
        if value is not None and value != "":
            sha = hashlib.sha256()
            sha.update(value.encode())
            # Use the setter as it also checks whether the existing password is the same with the
            # new one, and only updates if the new password is different
            self.protectedPassword = sha.hexdigest()

    @Property(str)
    def protectedPassword(self):
        """
        The encrypted password.

        Returns
        -------
        str
        """
        return self._protected_password

    @protectedPassword.setter
    def protectedPassword(self, value):
        if self._protected_password != value:
            self._protected_password = value

    @Property(bool)
    def showConfirmDialog(self):
        """
        Wether or not to display a confirmation dialog.

        Returns
        -------
        bool
        """
        return self._show_confirm_dialog

    @showConfirmDialog.setter
    def showConfirmDialog(self, value):
        """
        Wether or not to display a confirmation dialog.

        Parameters
        ----------
        value : bool
        """
        if self._show_confirm_dialog != value:
            self._show_confirm_dialog = value

    @Property(str)
    def confirmMessage(self):
        """
        Message to be displayed at the Confirmation dialog.

        Returns
        -------
        str
        """
        return self._confirm_message

    @confirmMessage.setter
    def confirmMessage(self, value):
        """
        Message to be displayed at the Confirmation dialog.

        Parameters
        ----------
        value : str
        """
        if self._confirm_message != value:
            self._confirm_message = value

    @Property(str)
    def pressValue(self):
        """
        This property holds the value to send back through the channel.

        The type of this value does not matter because it is automatically
        converted to match the prexisting value type of the channel. However,
        the sign of the value matters for both the fixed and relative modes.

        Returns
        -------
        str
        """
        return str(self._pressValue)

    @pressValue.setter
    def pressValue(self, value):
        """
        This property holds the value to send back through the channel.

        The type of this value does not matter because it is automatically
        converted to match the prexisting value type of the channel. However,
        the sign of the value matters for both the fixed and relative modes.

        Parameters
        ----------
        value : str
        """
        if str(value) != self._pressValue:
            self._pressValue = str(value)

    @Property(bool)
    def relativeChange(self):
        """
        The mode of operation of the PyDMPushButton.

        If set to True, the :attr:`pressValue` will be added to the current
        value of the channel. If False, the :attr:`pressValue` will be sent
        without any operation.

        This flag will be ignored if the connected channel sends a str type
        value to :meth:`.receiveValue`. This is designed to eliminate the
        undesirable behavior of concatenating strings as opposed to doing
        mathematical addition.

        Returns
        -------
        bool
        """
        return self._relative

    @relativeChange.setter
    def relativeChange(self, choice):
        """
        The mode of operation of the PyDMPushButton.

        If set to True, the :attr:`pressValue` will be added to the current
        value of the channel. If False, the :attr:`pressValue` will be sent
        without any operation.

        This flag will be ignored if the connected channel sends a str type
        value to :meth:`.receiveValue`. This is designed to eliminate the
        undesirable behavior of concatenating strings as opposed to doing
        mathematical addition.

        Parameters
        ----------
        choice : bool
        """
        if self._relative != choice:
            self._relative = choice

    def confirm_dialog(self):
        """
        Show the confirmation dialog with the proper message in case
        ```showConfirmMessage``` is True.

        Returns
        -------
        bool
            True if the message was confirmed or if ```showCofirmMessage```
            is False.
        """

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
        """
        If the widget is ```passwordProtected```, this method will propmt
        the user for the correct password.

        Returns
        -------
        bool
            True in case the password was correct of if the widget is not
            password protected.
        """
        if not self._password_protected:
            return True

        pwd, ok = QInputDialog().getText(None, "Authentication", "Please enter your password:",
                                         QLineEdit.Password, "")
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

    @Slot()
    def sendValue(self):
        """
        Send a new value to the channel.

        This function interprets the settings of the PyDMPushButton and sends
        the appropriate value out through the :attr:`.send_value_signal`.

        Returns
        -------
        None if any of the following condition is False:
            1. There's no new value (pressValue) for the widget
            2. There's no initial or current value for the widget
            3. The confirmation dialog returns No as the user's answer to the dialog
            4. The password validation dialog returns a validation error
        Otherwise, return the value sent to the channel:
            1. The value sent to the channel is the same as the pressValue if the existing
               channel type is a str, or the relative flag is False
            2. The value sent to the channel is the sum of the existing value and the pressValue
               if the relative flag is True, and the channel type is not a str
        """
        send_value = None
        if self._pressValue is None or self.value is None:
            return None

        if not self.confirm_dialog():
            return None

        if not self.validate_password():
            return None

        if not self._relative or self.channeltype == str:
            send_value = self._pressValue
            self.send_value_signal[self.channeltype].emit(self.channeltype(send_value))
        else:
            send_value = self.value + self.channeltype(self._pressValue)
            self.send_value_signal[self.channeltype].emit(send_value)
        return send_value

    @Slot(int)
    @Slot(float)
    @Slot(str)
    def updatePressValue(self, value):
        """
        Update the pressValue of a function by passing a signal to the
        PyDMPushButton.

        This is useful to dynamically change the pressValue of the button
        during runtime. This enables the applied value to be linked to the
        state of a different widget, say a QLineEdit or QSlider

        Parameters
        ----------
        value : int, float or str
        """
        try:
            self.pressValue = self.channeltype(value)
        except(ValueError, TypeError):
            logger.error("'{0}' is not a valid pressValue for '{1}'.".format(value, self.channel))
