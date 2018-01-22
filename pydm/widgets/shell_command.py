from ..PyQt.QtGui import QPushButton, QCursor, QIcon
from ..PyQt.QtCore import pyqtSlot, pyqtProperty, QSize
import shlex, subprocess
from .base import PyDMPrimitiveWidget
from ..utilities import IconFont


class PyDMShellCommand(QPushButton, PyDMPrimitiveWidget):
    """
    A QPushButton capable of execute shell commands.
    """

    def __init__(self, parent=None, command=None):
        QPushButton.__init__(self, parent)
        PyDMPrimitiveWidget.__init__(self)
        self.iconFont = IconFont()
        self._icon = self.iconFont.icon("cog")
        self.setIconSize(QSize(16, 16))
        self.setIcon(self._icon)
        self.setCursor(QCursor(self._icon.pixmap(16, 16)))

        self._command = command
        self._allow_multiple = False
        self.process = None
        self._show_icon = True

    @pyqtProperty(bool)
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

    @pyqtProperty(bool)
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

    @pyqtProperty(str)
    def command(self):
        """
        The Shell Command to be executed

        Returns
        -------
        str
        """
        return self._command

    @command.setter
    def command(self, value):
        """
        The Shell Command to be executed

        Parameters
        ----------
        value : str
        """
        if self._command != value:
            self._command = value

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

        self.execute_command()
        super(PyDMShellCommand, self).mouseReleaseEvent(mouse_event)

    @pyqtSlot()
    def execute_command(self):
        """
        Execute the shell command given by ```command```.
        The process is available through the ```process``` member.
        """

        if self._command is None or self._command == "":
            return

        if (self.process is None or self.process.poll() is not None) or self._allow_multiple:
            args = shlex.split(self._command)
            try:
                self.process = subprocess.Popen(args)
            except Exception as exc:
                print("Error in command: ", exc)
        else:
            print("Command already active.")
