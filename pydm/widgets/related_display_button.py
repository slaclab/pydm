from PyQt4.QtGui import QPushButton
from PyQt4.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QString

class PyDMRelatedDisplayButton(QPushButton):
  __pyqtSignals__ = ("request_open_signal(QString)")
  def __init__(self, filename=None, parent=None):
    super(PyDMRelatedDisplayButton, self).__init__(parent)
    self._display_filename = filename
    self.clicked.connect(self.open_display)
    
  def getDisplayFilename(self):
    return QString.fromAscii(self._display_filename)
  
  def setDisplayFilename(self, value):
    if self._display_filename != value:
      self._display_filename = str(value)

  def resetDisplayFilename(self):
    if self._display_filename != None:
      self._display_filename = None
      
  @pyqtSlot()
  def open_display(self):
    self.window().go(str(self.displayFilename))
    
  displayFilename = pyqtProperty("QString", getDisplayFilename, setDisplayFilename, resetDisplayFilename)