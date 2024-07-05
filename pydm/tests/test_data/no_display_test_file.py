# A sample test file of a python class that does not inherit from PyDM's display, but we try to load as a display anyway
from qtpy.QtCore import QObject


class InvalidDisplayExample(QObject):
    """A simple class that inherits from QObject only"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
