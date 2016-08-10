from PyQt4.QtGui import QPushButton
from PyQt4.QtCore import pyqtSlot, pyqtProperty, QString
import shlex, subprocess

class PyDMShellCommand(QPushButton):
  def __init__(self, command=None, parent=None):
    super(PyDMShellCommand, self).__init__(parent)
    self._command = command
    self.process = None

  def getCommand(self):
    return QString.fromAscii(self._command)

  def setCommand(self, value):
    if self._command != value:
      self._command = str(value)

  def resetCommand(self):
    if self._command is not None:
      self._command = None

  def mouseReleaseEvent(self, mouse_event):
    self.execute_command()
    super(PyDMShellCommand, self).mouseReleaseEvent(mouse_event)

  @pyqtSlot()
  def execute_command(self):
    if self.process is None or self.process.poll() is not None:
      args = shlex.split(self._command)
      self.process = subprocess.Popen(args)
    else:
      print "Command already active."

  command = pyqtProperty("QString", getCommand, setCommand, resetCommand)
