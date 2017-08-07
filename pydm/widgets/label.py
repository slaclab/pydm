from .base import PyDMWidget
from ..PyQt.QtGui import QLabel
from ..PyQt.QtCore import Qt

class PyDMLabel(QLabel, PyDMWidget):    
    def __init__(self, parent=None, init_channel=None):
        super(PyDMLabel, self).__init__(parent, init_channel=init_channel)
        self.setTextFormat(Qt.PlainText)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setText("PyDMLabel")
    
    def value_changed(self, new_value):
        super().value_changed(new_value)
        if isinstance(new_value, str):
            self.setText(new_value)
            return
        if isinstance(new_value, float):
            if self.format_string:
                self.setText(self.format_string.format(new_value))
                return
        if self.enum_strings is not None and isinstance(new_value, int):
            self.setText(self.enum_strings[new_value])
            return
        self.setText(str(new_value))
