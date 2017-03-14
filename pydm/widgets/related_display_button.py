from ..PyQt.QtGui import QPushButton, QApplication
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, Qt
import json

class PyDMRelatedDisplayButton(QPushButton):
  __pyqtSignals__ = ("request_open_signal(str)")
  
  #Constants for determining where to open the display.
  EXISTING_WINDOW = 0;
  NEW_WINDOW = 1;
  
  def __init__(self, parent=None, filename=None):
    super(PyDMRelatedDisplayButton, self).__init__(parent)
    self._display_filename = filename
    self._macros = {}
    self.app = QApplication.instance()
    
  def getDisplayFilename(self):
    return str(self._display_filename)
  
  def setDisplayFilename(self, value):
    if self._display_filename != value:
      self._display_filename = str(value)

  def resetDisplayFilename(self):
    if self._display_filename != None:
      self._display_filename = None
  
  displayFilename = pyqtProperty(str, getDisplayFilename, setDisplayFilename, resetDisplayFilename)
  
  def getMacros(self):
    if len(self._macros) < 1:
      return ""
    return json.dumps(self._macros)
  
  def setMacros(self, new_macros):
    if len(new_macros) < 1:
      self._macros = {}
    else:
      try:
        self._macros = json.loads(str(new_macros))
      except ValueError:
        pass
  
  def resetMacros(self):
    self._macros = {}
  
  macros = pyqtProperty(str, getMacros, setMacros, resetMacros, doc=
  """
  The macro substitutions to use when launching the display, in JSON object format.
  """)
  
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
    if target == self.EXISTING_WINDOW:
      self.window().go(self.displayFilename, macros=self._macros)
    if target == self.NEW_WINDOW:
      self.window().new_window(self.displayFilename, macros=self._macros)
    
  