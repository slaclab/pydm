from ..PyQt.QtGui import QPushButton
from ..PyQt.QtCore import pyqtSlot, pyqtProperty
import shlex, subprocess
from .base import PyDMPrimitiveWidget

class PyDMShellCommand(QPushButton, PyDMPrimitiveWidget):
    """
    A QPushButton capable of execute shell commands.
    """

    def __init__(self, parent=None, command=None):
        QPushButton.__init__(self, parent)
        PyDMPrimitiveWidget.__init__(self)
        self._command = command
        self.process = None

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

        if self.process is None or self.process.poll() is not None:
            args = shlex.split(self._command)
            self.process = subprocess.Popen(args)
        else:
            print("Command already active.")
