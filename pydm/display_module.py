from os import path
# Try PyQt5
try:
    pyqt5 = True
    from PyQt5 import uic
    from PyQt5.QtWidgets import QWidget
except ImportError:
    pyqt5 = False
    from PyQt4 import uic
    from PyQt4.QtGui import QWidget

class Display(QWidget):
  def __init__(self, display_manager_window):
    super(Display, self).__init__(display_manager_window)
    self.display_manager_window = display_manager_window
    self.ui = None
    self.load_ui(parent=self.display_manager_window)
  
  def ui_filepath(self):
    raise NotImplementedError
      
  def ui_filename(self):
    raise NotImplementedError
  
  def load_ui(self, parent=None):
    if self.ui:
      return self.ui
    if not parent:
      parent = self.display_manager_window
    self.ui = uic.loadUi(self.ui_filepath(), baseinstance=self)
