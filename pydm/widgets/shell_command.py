import os
import shlex
import subprocess
from functools import partial
import sys
import logging
import warnings

from qtpy.QtWidgets import QPushButton, QMenu
from qtpy.QtGui import QCursor, QIcon, QColor
from qtpy.QtCore import Property, QSize, Qt, QTimer
from .base import PyDMPrimitiveWidget
from ..utilities import IconFont

logger = logging.getLogger(__name__)

class PyDMShellCommand(QPushButton, PyDMPrimitiveWidget):
    """
    A QPushButton capable of execute shell commands.
    """

    def __init__(self, parent=None, command=None, title=None):
        QPushButton.__init__(self, parent)
        PyDMPrimitiveWidget.__init__(self)
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

    @Property(bool)
    def showIcon(self):
        """
        Whether or not we should show the selected Icon.

        Returns
        -------
        bool
        """
        return self._show_icon

    @showIcon.setter
    def showIcon(self, value):
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
    def redirectCommandOutput(self):
        """
        Whether or not we should redirect the output of command to the shell.

        Returns
        -------
        bool
        """
        return self._redirect_output

    @redirectCommandOutput.setter
    def redirectCommandOutput(self, value):
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
    def allowMultipleExecutions(self):
        """
        Whether or not we should allow the same command
        to be executed even if it is still running.

        Returns
        -------
        bool
        """
        return self._allow_multiple

    @allowMultipleExecutions.setter
    def allowMultipleExecutions(self, value):
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
    def titles(self):
        return self._titles

    @titles.setter
    def titles(self, val):
        self._titles = val
        self._menu_needs_rebuild = True

    @Property('QStringList')
    def commands(self):
        return self._commands

    @commands.setter
    def commands(self, val):
        if not val:
            self._commands = []
        else:
            self._commands = val
        self._menu_needs_rebuild = True

    @Property(str, designable=False)
    def command(self):
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
    def command(self, value):
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

    def _rebuild_menu(self):
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

    def mousePressEvent(self, event):
        if self._menu_needs_rebuild:
            self._rebuild_menu()
        super(PyDMShellCommand, self).mousePressEvent(event)

    def mouseReleaseEvent(self, mouse_event):
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

    def show_warning_icon(self):
        """ Show the warning icon.  This is called when a shell command fails
        (i.e. exits with nonzero status) """
        self.setIcon(self._warning_icon)
        QTimer.singleShot(5000, self.hide_warning_icon)

    def hide_warning_icon(self):
        """ Hide the warning icon.  This is called on a timer after the warning
        icon is shown."""
        if self._show_icon:
            self.setIcon(self._icon)
        else:
            self.setIcon(QIcon())

    def execute_command(self, command):
        """
        Execute the shell command given by ```command```.
        The process is available through the ```process``` member.
        """
        if not command:
            logger.info("The command is not set, so no command was executed.")
            return

        if (self.process is None or self.process.poll() is not None) or self._allow_multiple:
            cmd = os.path.expanduser(os.path.expandvars(command))
            args = shlex.split(cmd, posix='win' not in sys.platform)
            try:
                logger.debug("Launching process: %s", repr(args))
                stdout = subprocess.PIPE
                if self._redirect_output:
                    stdout = None
                self.process = subprocess.Popen(
                    args, stdout=stdout, stderr=subprocess.PIPE)
            except Exception as exc:
                self.show_warning_icon()
                logger.error("Error in shell command: %s", exc)
        else:
            logger.error("Command '%s' already active.", command)
