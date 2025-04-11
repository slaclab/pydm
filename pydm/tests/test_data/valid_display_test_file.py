"""This file is intended for use in Display related test files."""

import os
from pydm import Display
from pydm.widgets import PyDMPushButton, PyDMLabel

# Ensure loading of modules in the same directory works as expected when this file is loaded as a PyDM Display
import no_display_test_file


class DisplayExample(Display):
    """An example of a simple display that can be loaded by `load_py_file` in `display.py`"""

    def __init__(self, parent=None, args=None, macros=None):
        super().__init__(parent=parent, args=args, macros=macros)
        self.button = PyDMPushButton()
        self.button.clicked.connect(self.delete_widget)

        self.label = PyDMLabel(init_channel="TST:Val1")

    def print_file(self):
        print(f"{no_display_test_file}")

    def delete_widget(self):
        self.label.deleteLater()

    def ui_filename(self):
        return "test.ui"

    def ui_filepath(self):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), self.ui_filename())
