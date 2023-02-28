import os
import shlex
import subprocess
from functools import partial
import sys
import logging
import warnings
import hashlib
from ast import literal_eval
from qtpy.QtWidgets import QPushButton, QMenu, QMessageBox, QInputDialog, QLineEdit, QWidget
from qtpy.QtGui import QCursor, QIcon, QMouseEvent
from qtpy.QtCore import Property, QSize, Qt, QTimer
from .base import PyDMWidget, only_if_channel_set
from ..utilities import IconFont
from typing import Optional, Union, List

logger = logging.getLogger(__name__)


class PyDMShellCommand(QPushButton, PyDMWidget):
    """
    A QPushButton capable of execute shell commands.

    Parameters
    ----------
    parent : QWidget, optional
        The parent widget for the shell command
    command : str or list, optional
        A string for a single command to run, or a list of strings for multiple commands
    title : str or list, optional
        Title of the command to run, shown in the display. If a list, number of elements must match that of command
    init_channel : str, optional
        The channel to be used by the widget
    """

    DEFAULT_CONFIRM_MESSAGE = "Are you sure you want to proceed?"

    def __init__(self, parent: Optional[QWidget] = None, 
                 command: Optional[Union[str, List[str]]] = None, 
                 title: Optional[Union[str, List[str]]] = None,
                 init_channel: Optional[str] = None) -> None:
        QPushButton.__init__(self, parent)
        PyDMWidget.__init__(self, init_channel=init_channel)
        self.iconFont = IconFont()
        self._icon = self.iconFont.icon("cog")
        self._warning_icon = self.iconFont.icon('exclamation-circle')
        self.setIconSize(QSize(16, 16))
        self.setIcon(self._icon)
        self.setCursor(QCursor(self._icon.pixmap(16, 16)))
        if not title:
            title = []
        if not command:
            command = []
        if isinstance(title, str):
            title = [title]
        if isinstance(command, str):
            command = [command]
        if len(title) > 0 and (len(title) != len(command)):
            raise ValueError("Number of items in 'command' must match number of items in 'title'.")
        self._commands = command
        self._titles = title
        self._menu_needs_rebuild = True
        self._allow_multiple = False
        self.process = None
        self._show_icon = True
        self._redirect_output = False

        self._password_protected = False
        self._password = ""
        self._protected_password = ""
        self.env_var = None

        self._show_confirm_dialog = False
        self._confirm_message = PyDMShellCommand.DEFAULT_CONFIRM_MESSAGE
    
    def confirmDialog(self) -> bool:
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
                self._confirm_message = PyDMShellCommand.DEFAULT_CONFIRM_MESSAGE
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setText(self._confirm_message)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            ret = msg.exec_()

            if ret == QMessageBox.No:
                return False

        return True

    @Property(bool)
    def showConfirmDialog(self) -> bool:
        """
        Wether or not to display a confirmation dialog.

        Returns
        -------
        bool
        """
        return self._show_confirm_dialog

    @showConfirmDialog.setter
    def showConfirmDialog(self, value: bool) -> None:
        """
        Wether or not to display a confirmation dialog.

        Parameters
        ----------
        value : bool
        """
        if self._show_confirm_dialog != value:
            self._show_confirm_dialog = value

    @Property(str)
    def confirmMessage(self) -> str:
        """
        Message to be displayed at the Confirmation dialog.

        Returns
        -------
        str
        """
        return self._confirm_message

    @confirmMessage.setter
    def confirmMessage(self, value: str) -> None:
        """
        Message to be displayed at the Confirmation dialog.

        Parameters
        ----------
        value : str
        """
        if self._confirm_message != value:
            self._confirm_message = value

    @only_if_channel_set
    def check_enable_state(self) -> None:
        """
        override parent method, so this widget does not get disabled when the pv disconnects.
        This method adds a Tool Tip with the reason why it is disabled.
        """
        status = self._connected
        tooltip = self.restore_original_tooltip()
        if not status:
            if tooltip != '':
                tooltip += '\n'
            tooltip += "Alarm PV is disconnected."
            tooltip += '\n'
            tooltip += self.get_address()

        self.setToolTip(tooltip)
        
    @Property(str)
    def environmentVariables(self) -> str:
        """
        Return the environment variables which would be set along with the shell command.

        Returns
        -------
        self.env_var : str
        """
        return self.env_var

    @environmentVariables.setter
    def environmentVariables(self, new_dict: str) -> None:
        """
        Set environment variables which would be set along with the shell command.

        Parameters
        ----------
        new_dict : str
        """
        if self.env_var != new_dict:
            self.env_var = new_dict

    @Property(bool)
    def showIcon(self) -> bool:
        """
        Whether or not we should show the selected Icon.

        Returns
        -------
        bool
        """
        return self._show_icon

    @showIcon.setter
    def showIcon(self, value: bool) -> None:
        """
        Whether or not we should show the selected Icon.

        Parameters
        ----------
        value : bool
        """
        if self._show_icon != value:
            self._show_icon = value

            if self._show_icon:
                self.setIcon(self._icon)
            else:
                self._icon = self.icon()
                self.setIcon(QIcon())

    @Property(bool)
    def redirectCommandOutput(self) -> bool:
        """
        Whether or not we should redirect the output of command to the shell.

        Returns
        -------
        bool
        """
        return self._redirect_output

    @redirectCommandOutput.setter
    def redirectCommandOutput(self, value: bool) -> None:
        """
        Whether or not we should redirect the output of command to the shell.

        Parameters
        ----------
        value : bool

        Returns
        -------
        None.
        """
        if self._redirect_output != value:
            self._redirect_output = value

    @Property(bool)
    def allowMultipleExecutions(self) -> bool:
        """
        Whether or not we should allow the same command
        to be executed even if it is still running.

        Returns
        -------
        bool
        """
        return self._allow_multiple

    @allowMultipleExecutions.setter
    def allowMultipleExecutions(self, value: bool) -> None:
        """
        Whether or not we should allow the same command
        to be executed even if it is still running.

        Parameters
        ----------
        value : bool
        """
        if self._allow_multiple != value:
            self._allow_multiple = value

    @Property('QStringList')
    def titles(self) -> List[str]:
        return self._titles

    @titles.setter
    def titles(self, val: List[str]) -> None:
        self._titles = val
        self._menu_needs_rebuild = True

    @Property('QStringList')
    def commands(self) -> List[str]:
        return self._commands

    @commands.setter
    def commands(self, val: List[str]) -> None:
        if not val:
            self._commands = []
        else:
            self._commands = val
        self._menu_needs_rebuild = True

    @Property(str, designable=False)
    def command(self) -> str:
        """
        DEPRECATED: use the 'commands' property.
        This property simply returns the first command from the 'commands'
        property.
        The shell command to run.

        Returns
        -------
        str
        """
        if len(self.commands) == 0:
            return ""
        return self.commands[0]

    @command.setter
    def command(self, value: str) -> None:
        """
        DEPRECATED: Use the 'commands' property instead.
        This property only has an effect if the 'commands' property is empty.
        If 'commands' is empty, it will be set to a single item list containing
        the value of 'command'.

        Parameters
        ----------
        value : str
        """
        warnings.warn("'PyDMShellCommand.command' is deprecated, "
                      "use 'PyDMShellCommand.commands' instead.")
        if not self._commands:
            if value:
                self.commands = [value]
            else:
                self.commands = []

    @Property(bool)
    def passwordProtected(self) -> bool:
        """
        Whether or not this button is password protected.
        Returns
        -------
        bool
        -------
        """
        return self._password_protected

    @passwordProtected.setter
    def passwordProtected(self, value: bool) -> None:
        """
        Whether or not this button is password protected.
        Parameters
        ----------
        value : bool
        """
        if self._password_protected != value:
            self._password_protected = value

    @Property(str)
    def password(self) -> str:
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
    def password(self, value: str) -> None:
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
    def protectedPassword(self) -> str:
        """
        The encrypted password.

        Returns
        -------
        str
        """
        return self._protected_password

    @protectedPassword.setter
    def protectedPassword(self, value: str) -> None:
        """
        Setter for the encrypted password.

    	Parameters 
    	-------
    	value: str
    	"""
        if self._protected_password != value:
            self._protected_password = value

    def _rebuild_menu(self) -> None:
        if not any(self._commands):
            self._commands = []
        if not any(self._titles):
            self._titles = []
        if len(self._commands) == 0:
            self.setEnabled(False)
        if len(self._commands) <= 1:
            self.setMenu(None)
            self._menu_needs_rebuild = False
            return
        menu = QMenu(self)
        for i, command in enumerate(self._commands):
            if i >= len(self._titles):
                title = command
            else:
                title = self._titles[i]
            action = menu.addAction(title)
            action.triggered.connect(partial(self.execute_command, command))
        self.setMenu(menu)
        self._menu_needs_rebuild = False

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._menu_needs_rebuild:
            self._rebuild_menu()
        super(PyDMShellCommand, self).mousePressEvent(event)

    def mouseReleaseEvent(self, mouse_event: QMouseEvent) -> None:
        """
        mouseReleaseEvent is called when a mouse button is released.
        This means that if the user presses the mouse inside your widget,
        then drags the mouse somewhere else before releasing the mouse
        button, your widget receives the release event.

        Parameters
        ----------
        mouse_event :
        """
        if mouse_event.button() != Qt.LeftButton:
            return super(PyDMShellCommand, self).mouseReleaseEvent(mouse_event)
        if self.menu() is not None:
            return super(PyDMShellCommand, self).mouseReleaseEvent(mouse_event)
        assert len(self.commands) == 1, "More than one command present, but no menu created."
        self.execute_command(self.commands[0])
        super(PyDMShellCommand, self).mouseReleaseEvent(mouse_event)

    def show_warning_icon(self) -> None:
        """ Show the warning icon.  This is called when a shell command fails
        (i.e. exits with nonzero status) """
        self.setIcon(self._warning_icon)
        QTimer.singleShot(5000, self.hide_warning_icon)

    def hide_warning_icon(self) -> None:
        """ Hide the warning icon.  This is called on a timer after the warning
        icon is shown."""
        if self._show_icon:
            self.setIcon(self._icon)
        else:
            self.setIcon(QIcon())

    def validate_password(self) -> bool:
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

    def execute_command(self, command: str) -> None:
        """
        Execute the shell command given by ```command```.
        The process is available through the ```process``` member.

        Parameters
        ----------
        command : str 
            Shell command
        """
        if not command:
            logger.info("The command is not set, so no command was executed.")
            return

        if not self.validate_password():
            return None

        if not self.confirmDialog():
            return None

        if (self.process is None or self.process.poll() is not None) or self._allow_multiple:
            cmd = os.path.expanduser(os.path.expandvars(command))
            args = shlex.split(cmd, posix='win' not in sys.platform)
            try:
                logger.debug("Launching process: %s", repr(args))
                stdout = subprocess.PIPE

                if self.env_var:
                    env_var = literal_eval(self.env_var)
                else:
                    env_var = None

                if self._redirect_output:
                    stdout = None
                self.process = subprocess.Popen(
                    args, stdout=stdout, stderr=subprocess.PIPE, env=env_var)
            except Exception as exc:
                self.show_warning_icon()
                logger.error("Error in shell command: %s", exc)
        else:
            logger.error("Command '%s' already active.", command)

