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
    self._macro_string = None
    self._open_in_new_window = False
    self.app = QApplication.instance()
    
  def getDisplayFilename(self):
    return str(self._display_filename)
  
  def setDisplayFilename(self, value):
    if self._display_filename != value:
      self._display_filename = str(value)
      if self._display_filename is None or len(self._display_filename) < 1:
        self.setEnabled(False)

  def resetDisplayFilename(self):
    if self._display_filename != None:
      self._display_filename = None
  
  displayFilename = pyqtProperty(str, getDisplayFilename, setDisplayFilename, resetDisplayFilename)
  
  def getMacros(self):
    if self._macro_string is None:
      return ""
    return self._macro_string
  
  def setMacros(self, new_macros):
    if len(new_macros) < 1:
      self._macro_string = None
    else:
      self._macro_string = new_macros
  
  def resetMacros(self):
    self._macro_string = None
  
  macros = pyqtProperty(str, getMacros, setMacros, resetMacros, doc=
  """
  The macro substitutions to use when launching the display, in JSON object format.
  """)
  
  @pyqtProperty(bool, doc=
  """
  If true, the button will open the display in a new window, rather than in the existing window.
  """)
  def openInNewWindow(self):
    return self._open_in_new_window
  
  @openInNewWindow.setter
  def openInNewWindow(self, open_in_new):
    self._open_in_new_window = open_in_new
  
  def mouseReleaseEvent(self, mouse_event):
    if mouse_event.modifiers() == Qt.ShiftModifier or self._open_in_new_window:
      self.open_display(target=self.NEW_WINDOW)
    else:
      self.open_display()
    super(PyDMRelatedDisplayButton, self).mouseReleaseEvent(mouse_event)
      
  @pyqtSlot() 
  def open_display(self, target=EXISTING_WINDOW):
    if self.displayFilename == None:
      return
    macros = None
    if self._macro_string is not None:
      macros = json.loads(self._macro_string)
    try:
      if target == self.EXISTING_WINDOW:
        self.window().go(self.displayFilename, macros=macros)
      if target == self.NEW_WINDOW:
        self.window().new_window(self.displayFilename, macros=macros)
    except (IOError, OSError, ValueError, ImportError) as e:
      self.window().statusBar().showMessage("Cannot open file: '{0}'. Reason: '{1}'.".format(self.displayFilename, e), 5000)
    
  