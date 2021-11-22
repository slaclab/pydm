import os
import hashlib

from pydm.widgets.channel import PyDMChannel
from qtpy.QtWidgets import QPushButton, QMessageBox, QInputDialog, QLineEdit
from qtpy.QtCore import Slot, Property
from .base import PyDMWritableWidget, PyDMWidget
from qtpy.QtCore import Qt, QEvent, Signal, Slot, Property
from qtpy.QtGui import QColor

import logging
logger = logging.getLogger(__name__)


class PyDMReadbackButton(QPushButton, PyDMWritableWidget):
    """
     Button to handle a control PV and Readback PV. The button can be selected to display different colors when
    the value is not equal to the other.

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

    releaseValue : int, float, str
        Value to be sent when the button is released

    relative : bool, optional
        Choice to have the button perform a relative put, instead of always
        setting to an absolute value

    init_channel : str, optional
        ID of channel to manipulate

    channel_readback: str, optional
        ID of channel to readback

    """


    DEFAULT_CONFIRM_MESSAGE = "Are you sure you want to proceed?"

    def __init__(self, parent=None, label=None, icon=None,
                 pressValue=None, releaseValue=None, relative=False,
                 init_channel_set=None, init_channel_readback=None):
        if icon:
            QPushButton.__init__(self, icon, label, parent)
        elif label:
            QPushButton.__init__(self, label, parent)
        else:
            QPushButton.__init__(self, parent)
        PyDMWritableWidget.__init__(self, init_channel=init_channel_set)

        self._pressValue = pressValue
        self._releaseValue = releaseValue
        self._relative = relative
        self._alarm_sensitive_border = False
        self._show_confirm_dialog = False
        self._confirm_message = PyDMReadbackButton.DEFAULT_CONFIRM_MESSAGE
        self._password_protected = False
        self._password = ""
        self._protected_password = ""
        self._released = False
        self._pressText=""
        self._releaseText=""
        self._pressColor = QColor(239,239,239)
        self._releaseColor = QColor(239,239,239)
        self._inconsistentColor = QColor(239, 239, 239)

        self._channel_readback = init_channel_readback
        self._readback_value = None
        self._value=None
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


    @Property(str)
    def releaseValue(self):
        """
        This property holds the value to send back through the channel.

        The type of this value does not matter because it is automatically
        converted to match the prexisting value type of the channel. However,
        the sign of the value matters for both the fixed and relative modes.

        Returns
        -------
        str
        """
        return str(self._releaseValue)

    @releaseValue.setter
    def releaseValue(self, value):
        """
        This property holds the value to send back through the channel.

        The type of this value does not matter because it is automatically
        converted to match the prexisting value type of the channel. However,
        the sign of the value matters for both the fixed and relative modes.

        Parameters
        ----------
        value : str
        """
        if str(value) != self._releaseValue:
            self._releaseValue = str(value)


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

    @Property(str)
    def pressText(self):
        """
        The text displayed when pressing the button.

        Returns
        -------
        str
        """
        return self._pressText

    @pressText.setter
    def pressText(self, value):
        if self._pressText!= value:
            self._pressText = value
        self.clicked.connect(self.updateText)

        #self.setText(self._pressText)

    @Property(str)
    def releaseText(self):
        """
        The text displayed when release the button.

        Returns
        -------
        str
        """
        return self._releaseText

    @releaseText.setter
    def releaseText(self, value):
        if self._releaseText!= value:
            self._releaseText = value
        self.clicked.connect(self.updateText)


    @Property(QColor)
    def pressColor(self):
        """
                The color displayed when pressing the button.

                Returns
                -------
                str
        """
        return self._pressColor

    @pressColor.setter
    def pressColor(self, value):
        if self._pressColor != value:
           self._pressColor=value
        self.clicked.connect(self.updateColor)

    @Property(QColor)
    def releaseColor(self):
        """
                The color displayed when releasing the button.

                Returns
                -------
                str
        """
        return self._releaseColor

    @releaseColor.setter
    def releaseColor(self, value):
        if self._releaseColor != value:
            self._releaseColor = value
        self.clicked.connect(self.updateColor)

    @Property(QColor)
    def inconsistentColor(self):
        return self._inconsistentColor

    @inconsistentColor.setter
    def inconsistentColor(self, value):
        """
                The color displayed when pv value and readback pv value are different

                Returns
                -------
                str
        """
        if self._inconsistentColor != value:
            self._inconsistentColor = value

    def confirm_dialog(self, is_release=False):
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
                self._confirm_message = PyDMReadbackButton.DEFAULT_CONFIRM_MESSAGE
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)

            relative = "Yes" if self._relative else "No"
            val = self._pressValue
            op = "Press"
            if is_release:
                val = self._releaseValue
                op = "Release"

            message = os.linesep.join(
                [
                    self._confirm_message,
                    "Value: {}".format(val),
                    "Relative Change: {}".format(relative)
                ]
            )

            msg.setText(message)

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
        if self.isCheckable():
            if self.isChecked():
                val=self.__execute_send(self._pressValue)
            else:
                val = self.__execute_send(self._releaseValue)
        else:
            self._released = False
            val = self.__execute_send(self._pressValue)

        if self._show_confirm_dialog or self._password_protected:
            self.__execute_send(self._releaseValue, is_release=True)

        self._value=val
        return val

    def __execute_send(self, new_value, skip_confirm=False, skip_password=False,
                       is_release=False):
        """
        Execute the send operation for push and release.

        Parameters
        ----------
        new_value : int, float or str
        skip_confirm : bool, Default False
            Whether or not to skip the confirmation dialog.
        skip_password : bool, Default False
            Whether or not to skip the password dialog.
        is_release : bool, Default False
            Whether or not this method is being invoked to handle a release
            event.

        Returns
        -------

        """
        send_value = None
        if new_value is None or self.value is None:
            return None

        if is_release and not self._write_when_release:
            return None

        if not skip_confirm:
            if not self.confirm_dialog(is_release=is_release):
                return None

        if not skip_password:
            if not self.validate_password():
                return None

        if not self._relative or self.channeltype == str:
            send_value = new_value
            self.send_value_signal[self.channeltype].emit(
                self.channeltype(send_value)
            )
        else:
            send_value = self.value + self.channeltype(new_value)
            self.send_value_signal[self.channeltype].emit(send_value)
        return send_value


    @Slot()
    def sendReleaseValue(self):
        """
        Send new release value to the channel.

        This function interprets the settings of the PyDMPushButton and sends
        the appropriate value out through the :attr:`.send_value_signal`.

        Returns
        -------
        None if any of the following condition is False:
            1. There's no new value (releaseValue) for the widget
            2. There's no initial or current value for the widget
            3. The confirmation dialog returns No as the user's answer to the dialog
            4. The password validation dialog returns a validation error
            5. writeWhenRelease is False
        Otherwise, return the value sent to the channel:
            1. The value sent to the channel is the same as the pressValue if the existing
               channel type is a str, or the relative flag is False
            2. The value sent to the channel is the sum of the existing value and the pressValue
               if the relative flag is True, and the channel type is not a str
        """
        self._released = True
        if self._show_confirm_dialog or self._password_protected:
            # This will be handled via our friend sendValue
            return
        self.__execute_send(self._releaseValue, is_release=True)

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


    @Property(str)
    def channelReadback(self):

        if self._channel_readback:
            return str(self._channel_readback)
        return None

    @channelReadback.setter
    def channelReadback(self, value):

        if self._channel_readback != value:
            # Remove old connections
            for channel_readback in [c for c in self._channels if
                            c.address == self._channel_readback]:
                channel_readback.disconnect()
                self._channels.remove(channel_readback)
            # Load new channel
            self._channel_readback = str(value)
            if not self._channel_readback:
                logger.debug('Channel was set to an empty string.')
                return
            channel_readback = PyDMChannel(address=self._channel_readback)
                                           #value_slot=self.readbackchannelValueChanged)
            if hasattr(self, 'channelReadback'):
                channel_readback.value_slot = self.readbackchannelValueChanged

            # Connect write channels if we have them
            channel_readback.connect()
            self._channels.append(channel_readback)


    @Slot(int)
    @Slot(float)
    @Slot(str)
    def updateReleaseValue(self, value):
        """
        Update the releaseValue of a function by passing a signal to the
        PyDMPushButton.

        This is useful to dynamically change the releaseValue of the button
        during runtime. This enables the applied value to be linked to the
        state of a different widget, say a QLineEdit or QSlider

        Parameters
        ----------
        value : int, float or str
        """
        try:
            self.releaseValue = self.channeltype(value)
        except(ValueError, TypeError):
            logger.error("'{0}' is not a valid releaseValue for '{1}'.".format(value, self.channel))

    @Slot()
    def updateText(self):
         """
        Update the button text by passing a signal to the
        PyDMPushButton.

        Parameters
        ----------
        value : int, float or str
        """
         if self.isCheckable():
             if self.isChecked():
                 self.setText(self._pressText)
             else:
                 self.setText(self._releaseText)

    @Slot()
    def updateColor(self):
        """
                PyQT Slot to update the button color
        """
        if self.isCheckable():
            if self.isChecked():
                self.setStyleSheet("QPushButton{background-color:%s}" % self._pressColor.name())
            else:
                self.setStyleSheet("QPushButton{background-color:%s}" % self._releaseColor.name())

    @Slot(int)
    @Slot(float)
    @Slot(str)
    @Slot(bool)
    def readbackchannelValueChanged(self, new_val):
        """
                PyQT Slot for changes on the Value of the Readback Channel
                This slot compares the Values of two channels and update the button color if they are different.

                Parameters
                ----------
                new_val : int, float, str, bool or np.ndarray
        """
        #bgColor=self.palette().color(self.palette().Background)
        self._readback_value = new_val
        if self._value is not None:
            if self._readback_value is not None:
                 if float(self._value) != float(self._readback_value):
                      self.setStyleSheet("QPushButton{background-color:%s}" % self._inconsistentColor.name())



        


