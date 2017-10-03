from os import path
from .PyQt import uic
from .PyQt.QtGui import QWidget
from .utilities import macro

class Display(QWidget):
    def __init__(self, parent=None, args=None, macros=None):
        super(Display, self).__init__(parent=parent)
        self.ui = None
        self.load_ui(parent=parent, macros=macros)
    
    def ui_filepath(self):
        raise NotImplementedError
            
    def ui_filename(self):
        raise NotImplementedError
    
    def load_ui(self, parent=None, macros=None):
        if self.ui:
            return self.ui
        if macros is not None:
            f = macro.substitute_in_file(self.ui_filepath(), macros)
        else:
            f = self.ui_filepath()
        self.ui = uic.loadUi(f, baseinstance=self)
