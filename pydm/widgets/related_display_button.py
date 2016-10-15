from PyQt4.QtGui import QPushButton, QApplication
from PyQt4.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, Qt

class PyDMRelatedDisplayButton(QPushButton):
  __pyqtSignals__ = ("request_open_signal(str)")
  
  #Constants for determining where to open the display.
  EXISTING_WINDOW = 0;
  NEW_WINDOW = 1;
  
  def __init__(self, filename=None, parent=None):
    super(PyDMRelatedDisplayButton, self).__init__(parent)
    self._display_filename = filename
    self.app = QApplication.instance()
    
  def getDisplayFilename(self):
    return self._display_filename
  
  def setDisplayFilename(self, value):
    if self._display_filename != value:
      self._display_filename = str(value)

  def resetDisplayFilename(self):
    if self._display_filename != None:
      self._display_filename = None
  
  def mouseReleaseEvent(self, mouse_event):
    if mouse_event.modifiers() == Qt.ShiftModifier:
      self.open_display(target=self.NEW_WINDOW)
    else:
      self.open_display()
    super(PyDMRelatedDisplayButton, self).mouseReleaseEvent(mouse_event)
      
  @pyqtSlot() 
  def open_display(self, target=EXISTING_WINDOW):
    if self.displayFilename == None:
      return
    if self.displayFilename[0] == "/":
      filename = str(self.displayFilename)
    else:
      filename = self.app.get_path(self.displayFilename, self)
    if target == self.EXISTING_WINDOW:
      self.window().go(str(self.displayFilename))
    if target == self.NEW_WINDOW:
      self.app.new_window(filename)
    
  displayFilename = pyqtProperty(str, getDisplayFilename, setDisplayFilename, resetDisplayFilename)
