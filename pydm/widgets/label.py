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
        #If the value is a string, just display it as-is, no formatting needed.
        if isinstance(new_value, str):
            self.setText(new_value)
            return
        #If the value is an enum, display the appropriate enum string for the value.
        if self.enum_strings is not None and isinstance(new_value, int):
            self.setText(self.enum_strings[new_value])
            return
        #If the value is a number (float or int), display it using a format string if necessary.
        if isinstance(new_value, (int, float)):
            self.setText(self.format_string.format(new_value))
            return
        #If you made it this far, just turn whatever the heck the value is into a string and display it.
        self.setText(str(new_value))
