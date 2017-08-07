from ..PyQt.QtGui import QCheckBox
from .base import PyDMWidget

class PyDMCheckbox(QCheckBox, PyDMWidget):    
    def __init__(self, parent=None, init_channel=None):
        super(PyDMCheckbox, self).__init__(parent, init_channel=init_channel)
        self.value_changed = self.receive_value
        self.clicked.connect(self.send_value)
    
    def receive_value(self, new_val):
        if new_val is None:
            return
        if new_val > 0:
            self.setChecked(True)
        else:
            self.setChecked(False)
    
    def send_value(self, checked):
        if checked:
            self.send_value_signal.emit(str(1))
        else:
            self.send_value_signal.emit(str(0))
    