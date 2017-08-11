from ..PyQt.QtGui import QWidget, QComboBox, QHBoxLayout
from ..PyQt.QtCore import pyqtSignal, pyqtSlot
from .base import PyDMWritableWidget


class PyDMEnumComboBox(QWidget, PyDMWritableWidget):
    activated = pyqtSignal([int], [str])
    currentIndexChanged = pyqtSignal([int], [str])
    highlighted = pyqtSignal([int], [str])
    
    def __init__(self, parent=None):
        super(PyDMEnumComboBox, self).__init__(parent=parent)
        self.horizontal_layout = QHBoxLayout(self)
        self.combo_box = QComboBox(self)

        self.horizontal_layout.addWidget(self.combo_box)
        #Internal values for properties
        self._has_enums = False
        self.combo_box.activated[int].connect(self.internal_combo_box_activated_int)
        self.combo_box.activated[str].connect(self.internal_combo_box_activated_str)
        self.combo_box.currentIndexChanged[int].connect(self.internal_combo_box_index_changed_int)
        self.combo_box.currentIndexChanged[str].connect(self.internal_combo_box_index_changed_str)
        self.combo_box.highlighted[int].connect(self.internal_combo_box_highlighted_int)
        self.combo_box.highlighted[str].connect(self.internal_combo_box_highlighted_str)

    #Internal methods    
    def set_items(self, enums):
        self.combo_box.clear()
        for enum in enums:
            self.combo_box.addItem(enum)
        self._has_enums = True
        self.check_enable_state()
    
    def check_enable_state(self):
        status = self._write_access and self._connected and self._has_enums
        tooltip = ""
        if not self._connected:
            tooltip += "PV is disconnected."
        elif not self._write_access:
            tooltip += "Access denied by Channel Access Security."
        elif not self._has_enums:
            tooltip += "Enums not available."
                
        self.setToolTip(tooltip)
        self.setEnabled(status)
    
    def enum_strings_changed(self, new_enum_strings):
        super().enum_strings_changed(new_enum_strings)
        self.set_items(new_enum_strings)
    
    def value_changed(self, new_val):
        if new_val:
            super().value_changed(new_val)
            self.combo_box.setCurrentIndex(new_val)
    
    #Internal combo box signal handling.
    #In places where we just forward the signal, we may want to instead just do self.signal = self.combo_box.signal
    #in __init__...
    @pyqtSlot(int)
    def internal_combo_box_activated_int(self, index):
        if self.value != index:
            self.send_value_signal.emit(index)
            self.activated[int].emit(index)
    
    @pyqtSlot(str)
    def internal_combo_box_activated_str(self, text):
        self.activated[str].emit(text)
    
    @pyqtSlot(int)
    def internal_combo_box_index_changed_int(self, index):
        self.currentIndexChanged[int].emit(index)
    
    @pyqtSlot(str)
    def internal_combo_box_index_changed_str(self, text):
        self.currentIndexChanged[str].emit(text)
    
    @pyqtSlot(int)
    def internal_combo_box_highlighted_int(self, index):
        self.highlighted[int].emit(index)
    
    @pyqtSlot(str)
    def internal_combo_box_highlighted_str(self, text):
        self.highlighted[str].emit(text)

