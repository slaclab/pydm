import os
import shlex
import subprocess
from functools import partial
import sys
import logging
import warnings
import hashlib
from ast import literal_eval
from qtpy.QtWidgets import QPushButton, QMenu, QMessageBox, QInputDialog, QLineEdit, QWidget, QStyle
from qtpy.QtGui import QCursor, QIcon, QMouseEvent, QColor
from qtpy.QtCore import Property, QSize, Qt, QTimer
from qtpy import QtDesigner
from .base import PyDMWidget, only_if_channel_set, PostParentClassInitSetup
from pydm.utilities import IconFont, ACTIVE_QT_WRAPPER, QtWrapperTypes
from typing import Optional, Union, List

logger = logging.getLogger(__name__)


class TermOutputMode:
    """
    Enum to select the behavior of the stdout/stderr output from a subprocess.
    """

    HIDE = 0
    SHOW = 1
    STORE = 2


if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYSIDE6:
    from PySide6.QtCore import QEnum
    from enum import Enum

    @QEnum
    # overrides prev enum def
    class TermOutputMode(Enum):  # noqa: F811
        HIDE = 0
        SHOW = 1
        STORE = 2


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

    if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYQT5:
        from PyQt5.QtCore import Q_ENUM

        Q_ENUM(TermOutputMode)
    TermOutputMode = TermOutputMode

    # Make enum definitions known to this class
    HIDE = TermOutputMode.HIDE
    SHOW = TermOutputMode.SHOW
    STORE = TermOutputMode.STORE

    DEFAULT_CONFIRM_MESSAGE = "Are you sure you want to proceed?"

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        command: Optional[Union[str, List[str]]] = None,
        title: Optional[Union[str, List[str]]] = None,
        init_channel: Optional[str] = None,
    ) -> None:
        QPushButton.__init__(self, parent)
        PyDMWidget.__init__(self, init_channel=init_channel)
        self.iconFont = IconFont()
        self._icon = self.iconFont.icon("cog")
        self._warning_icon = self.iconFont.icon("exclamation-circle")
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
        self._stdout = TermOutputMode.HIDE
        self._stderr = TermOutputMode.HIDE
        self._uses_stdout_intf = False
        # shell allows for more options such as command chaining ("cmd1;cmd2", "cmd1 && cmd2", etc ...),
        # use of environment variables, glob expansion ('ls *.txt'), etc...
        self._run_commands_in_full_shell = False

        self._password_protected = False
        self._password = ""
        self._protected_password = ""
        self.env_var = None

        self._show_confirm_dialog = False
        self._confirm_message = PyDMShellCommand.DEFAULT_CONFIRM_MESSAGE

        # Standard icons (which come with the qt install, and work cross-platform),
        # and icons from the "Font Awesome" icon set (https://fontawesome.com/)
        # can not be set with a widget's "icon" property in designer, only in python.
        # so we provide our own property to specify standard icons and set them with python in the prop's setter.
        self._pydm_icon_name = ""
        # The color of "Font Awesome" icons can be set,
        # but standard icons are already colored and can not be set.
        self._pydm_icon_color = QColor(90, 90, 90)
        # Execute setup calls that must be done here in the widget class's __init__,
        # and after it's parent __init__ calls have completed.
        # (so we can avoid pyside6 throwing an error, see func def for more info)
        PostParentClassInitSetup(self)

    def confirmDialog(self) -> bool:
        """
        Show the confirmation dialog with the proper message in case
        ```showConfirmMessage``` is True.

        Returns
        -------
        bool
            True if the message was confirmed or if ```showConfirmMessage```
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

    @Property(str)
    def PyDMIcon(self) -> str:
        """
        Name of icon to be set from Qt provided standard icons or from the fontawesome icon-set.
        See "enum QStyle::StandardPixmap" in Qt's QStyle documentation for full list of usable standard icons.
        See https://fontawesome.com/icons?d=gallery for list of usable fontawesome icons.

        Returns
        -------
        str
        """
        return self._pydm_icon_name

    @PyDMIcon.setter
    def PyDMIcon(self, value: str) -> None:
        """
        Name of icon to be set from Qt provided standard icons or from the "Font Awesome" icon-set.
        See "enum QStyle::StandardPixmap" in Qt's QStyle documentation for full list of usable standard icons.
        See https://fontawesome.com/icons?d=gallery for list of usable "Font Awesome" icons.

        Parameters
        ----------
        value : str
        """
        if self._pydm_icon_name == value:
            return

        # We don't know if user is trying to use a standard icon or an icon from "Font Awesome",
        # so 1st try to create a Font Awesome one, which hits exception if icon name is not valid.
        try:
            icon_f = IconFont()
            i = icon_f.icon(value, color=self._pydm_icon_color)
            self.setIcon(i)
        except Exception:
            icon = getattr(QStyle, value, None)
            if icon:
                self.setIcon(self.style().standardIcon(icon))

        self._pydm_icon_name = value

    @Property(QColor)
    def PyDMIconColor(self) -> QColor:
        """
        The color of the icon (color is only applied if using icon from the "Font Awesome" set)
        Returns
        -------
        QColor
        """
        return self._pydm_icon_color

    @PyDMIconColor.setter
    def PyDMIconColor(self, state_color: QColor) -> None:
        """
        The color of the icon (color is only applied if using icon from the "Font Awesome" set)
        Parameters
        ----------
        new_color : QColor
        """
        if state_color != self._pydm_icon_color:
            self._pydm_icon_color = state_color
            # apply the new color
            try:
                icon_f = IconFont()
                i = icon_f.icon(self._pydm_icon_name, color=self._pydm_icon_color)
                self.setIcon(i)
            except Exception:
                return

    @Property(bool)
    def showConfirmDialog(self) -> bool:
        """
        Whether or not to display a confirmation dialog.

        Returns
        -------
        bool
        """
        return self._show_confirm_dialog

    @showConfirmDialog.setter
    def showConfirmDialog(self, value: bool) -> None:
        """
        Whether or not to display a confirmation dialog.

        Parameters
        ----------
        value : bool
        """
        if self._show_confirm_dialog != value:
            self._show_confirm_dialog = value

    @Property(bool)
    def runCommandsInFullShell(self) -> bool:
        """
        Whether or not to run cmds with Popen's option for running them through a shell subprocess.

        Returns
        -------
        bool
        """
        return self._run_commands_in_full_shell

    @runCommandsInFullShell.setter
    def runCommandsInFullShell(self, value: bool) -> None:
        """
        Whether or not to run cmds with Popen's option for running them through a shell subprocess.

        Parameters
        ----------
        value : bool
        """
        if self._run_commands_in_full_shell != value:
            self._run_commands_in_full_shell = value

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
            if tooltip != "":
                tooltip += "\n"
            tooltip += "Alarm PV is disconnected."
            tooltip += "\n"
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

    @Property(bool, designable=False)
    def redirectCommandOutput(self) -> bool:
        """
        Whether or not we should redirect the output of command to the shell.

        This is deprecated in favor of the `stdout` property.
        If `stdout` has already been set, this property will be ignored
        and will log a warning when changed.

        If the `stdout` property has not been changed, setting and checking
        this property will still work as it always had for backwards
        compatibility.
        """
        return self._stdout == TermOutputMode.SHOW

    @redirectCommandOutput.setter
    def redirectCommandOutput(self, value: bool) -> None:
        if self._uses_stdout_intf:
            logger.warning(
                f"In PydmShellCommand named {self.objectName()}, "
                'tried to use deprecated "redirectCommandOutput" property to '
                'override "stdout" property. This has been ignored.'
            )
            return
        if value:
            self._stdout = TermOutputMode.SHOW
        else:
            self._stdout = TermOutputMode.HIDE

    @Property(TermOutputMode)
    def stdout(self) -> TermOutputMode:
        """
        The behavior of the subprocess's standard output stream.

        The options are:

        - `HIDE` (default): hide the stdout
        - `SHOW`: print stdout to terminal
        - `STORE`: capture stdout for programmatic retrieval

        This is implicitly linked to the older, soft deprecated
        parameter `redirectCommandOutput`, which can still be
        set to `False` to `HIDE` the stdout or `True` to `SHOW`
        the stdout, provided that stdout itself has not yet been
        set.
        """
        return self._stdout

    @stdout.setter
    def stdout(self, value: TermOutputMode) -> None:
        self._uses_stdout_intf = True
        self._stdout = value

    @Property(TermOutputMode)
    def stderr(self) -> TermOutputMode:
        """
        The behavior of the subprocess's standard error stream.

        The options are:

        - `HIDE` (default): hide the stderr
        - `SHOW`: print stderr to terminal
        - `STORE`: capture stderr for programmatic retrieval
        """
        return self._stderr

    @stderr.setter
    def stderr(self, value: TermOutputMode) -> None:
        self._stderr = value

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

    @Property("QStringList")
    def titles(self) -> List[str]:
        return self._titles

    @titles.setter
    def titles(self, val: List[str]) -> None:
        self._titles = val
        self._menu_needs_rebuild = True

    @Property("QStringList")
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
        warnings.warn("'PyDMShellCommand.command' is deprecated, use 'PyDMShellCommand.commands' instead.")
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
          To avoid issues exposing the password this method always returns an empty string.

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

            # Make sure designer knows it should save the protectedPassword field
            formWindow = QtDesigner.QDesignerFormWindowInterface.findFormWindow(self)
            if formWindow:
                formWindow.cursor().setProperty("protectedPassword", self.protectedPassword)

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
        super().mousePressEvent(event)

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
            return super().mouseReleaseEvent(mouse_event)
        if self.menu() is not None:
            return super().mouseReleaseEvent(mouse_event)
        assert len(self.commands) == 1, "More than one command present, but no menu created."
        self.execute_command(self.commands[0])
        super().mouseReleaseEvent(mouse_event)

    def show_warning_icon(self) -> None:
        """Show the warning icon.  This is called when a shell command fails
        (i.e. exits with nonzero status)"""
        self.setIcon(self._warning_icon)
        QTimer.singleShot(5000, self.hide_warning_icon)

    def hide_warning_icon(self) -> None:
        """Hide the warning icon.  This is called on a timer after the warning
        icon is shown."""
        if self._show_icon:
            self.setIcon(self._icon)
        else:
            self.setIcon(QIcon())

    def validate_password(self) -> bool:
        """
        If the widget is ```passwordProtected```, this method will prompt
        the user for the correct password.

        Returns
        -------
        bool
            True in case the password was correct of if the widget is not
            password protected.
        """
        if not self._password_protected:
            return True

        pwd, ok = QInputDialog().getText(None, "Authentication", "Please enter your password:", QLineEdit.Password, "")
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
            args = shlex.split(cmd, posix="win" not in sys.platform)
            # when shell enabled, Popen should take the cmds as a single string (not list)
            if self._run_commands_in_full_shell:
                args = cmd
            try:
                logger.debug("Launching process: %s", repr(args))

                if self._stdout == TermOutputMode.HIDE:
                    stdout = subprocess.DEVNULL
                elif self._stdout == TermOutputMode.SHOW:
                    stdout = None
                elif self._stdout == TermOutputMode.STORE:
                    stdout = subprocess.PIPE
                else:
                    raise ValueError(f"Invalid stdout configuration {self._stdout}")

                if self._stderr == TermOutputMode.HIDE:
                    stderr = subprocess.DEVNULL
                elif self._stderr == TermOutputMode.SHOW:
                    stderr = None
                elif self._stderr == TermOutputMode.STORE:
                    stderr = subprocess.PIPE
                else:
                    raise ValueError(f"Invalid stderr configuration {self._stderr}")

                if self.env_var:
                    env_var = literal_eval(self.env_var)
                else:
                    env_var = None

                self.process = subprocess.Popen(
                    args, stdout=stdout, stderr=stderr, env=env_var, shell=self._run_commands_in_full_shell
                )

            except Exception as exc:
                self.show_warning_icon()
                logger.error("Error in shell command: %s", exc)
        else:
            logger.error("Command '%s' already active.", command)
