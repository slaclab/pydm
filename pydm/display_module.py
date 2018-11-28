import sys
from os import path
from qtpy import uic
from qtpy.QtWidgets import QWidget
from .utilities import macro


class Display(QWidget):
    def __init__(self, parent=None, args=None, macros=None, ui_filename=None):
        super(Display, self).__init__(parent=parent)
        self.ui = None
        self._ui_filename = ui_filename
        self.load_ui(parent=parent, macros=macros)

    def ui_filepath(self):
        """ Returns the path to the ui file relative to the file of the class
        calling this function."""
        if not self.ui_filename():
            return None
        path_to_class = sys.modules[self.__module__].__file__
        return path.join(path.dirname(path.realpath(path_to_class)), self.ui_filename())

    def ui_filename(self):
        """ Returns the name of the ui file.  In modern PyDM, it is preferable
        specify this via the ui_filename argument in Display's constructor,
        rather than reimplementing this in Display subclasses."""
        if self._ui_filename is None:
            raise NotImplementedError
        else:
            return self._ui_filename

    def load_ui(self, parent=None, macros=None):
        """ Load and parse the ui file, and make the file's widgets available
        in self.ui.  Called by the initializer."""
        if self.ui:
            return self.ui
        if self.ui_filepath() is not None and self.ui_filepath() != "":
            if macros is not None:
                f = macro.substitute_in_file(self.ui_filepath(), macros)
            else:
                f = self.ui_filepath()
            self.ui = uic.loadUi(f, baseinstance=self)
