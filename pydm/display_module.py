from os import path
from .PyQt import uic
from .PyQt.QtGui import QWidget

class Display(QWidget):
  def __init__(self, parent=None):
    super(Display, self).__init__(parent=parent)
    self.ui = None
    self.load_ui(parent=parent)
  
  def ui_filepath(self):
    raise NotImplementedError
      
  def ui_filename(self):
    raise NotImplementedError
  
  def load_ui(self, parent=None):
    if self.ui:
      return self.ui
    self.ui = uic.loadUi(self.ui_filepath(), baseinstance=self)
