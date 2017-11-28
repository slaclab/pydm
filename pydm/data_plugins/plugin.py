from numpy import ndarray
from ..PyQt.QtCore import pyqtSlot, pyqtSignal, QObject, Qt

class PyDMConnection(QObject):
    new_value_signal =        pyqtSignal([float],[int],[str], [ndarray])
    connection_state_signal = pyqtSignal(bool)
    new_severity_signal =     pyqtSignal(int)
    write_access_signal =     pyqtSignal(bool)
    enum_strings_signal =     pyqtSignal(tuple)
    unit_signal =             pyqtSignal(str)
    prec_signal =             pyqtSignal(int)
    upper_ctrl_limit_signal = pyqtSignal([float],[int])
    lower_ctrl_limit_signal = pyqtSignal([float],[int])

    def __init__(self, channel, address, parent=None):
        super(PyDMConnection, self).__init__(parent)
        self.listener_count = 0
  
    def add_listener(self, channel):
        self.listener_count = self.listener_count + 1
        if channel.connection_slot is not None:
            self.connection_state_signal.connect(channel.connection_slot, Qt.QueuedConnection)
        if channel.value_slot is not None:
            try:
                self.new_value_signal[int].connect(channel.value_slot, Qt.QueuedConnection)
            except TypeError:
                pass
            try:
                self.new_value_signal[float].connect(channel.value_slot, Qt.QueuedConnection)
            except TypeError:
                pass
            try:
                self.new_value_signal[str].connect(channel.value_slot, Qt.QueuedConnection)
            except TypeError:
                pass
            try:
                self.new_value_signal[ndarray].connect(channel.value_slot, Qt.QueuedConnection)
            except TypeError:
                pass

        if channel.severity_slot is not None:
            self.new_severity_signal.connect(channel.severity_slot, Qt.QueuedConnection)

        if channel.write_access_slot is not None:
            self.write_access_signal.connect(channel.write_access_slot, Qt.QueuedConnection)

        if channel.enum_strings_slot is not None:
            self.enum_strings_signal.connect(channel.enum_strings_slot, Qt.QueuedConnection)

        if channel.unit_slot is not None:
            self.unit_signal.connect(channel.unit_slot, Qt.QueuedConnection)

        if channel.upper_ctrl_limit_slot is not None:
            self.upper_ctrl_limit_signal.connect(channel.upper_ctrl_limit_slot, Qt.QueuedConnection)

        if channel.lower_ctrl_limit_slot is not None:
            self.lower_ctrl_limit_signal.connect(channel.lower_ctrl_limit_slot, Qt.QueuedConnection)

        if channel.prec_slot is not None:
            self.prec_signal.connect(channel.prec_slot, Qt.QueuedConnection)
      
    def remove_listener(self, channel):
        if channel.connection_slot is not None:
            self.connection_state_signal.disconnect(channel.connection_slot)
        if channel.value_slot is not None:
            try:
                self.new_value_signal[int].disconnect(channel.value_slot)
            except TypeError:
                pass
            try:
                self.new_value_signal[float].disconnect(channel.value_slot)
            except TypeError:
                pass
            try:
                self.new_value_signal[str].disconnect(channel.value_slot)
            except TypeError:
                pass
            try:
                self.new_value_signal[ndarray].disconnect(channel.value_slot)
            except TypeError:
                pass

        if channel.severity_slot is not None:
            self.new_severity_signal.disconnect(channel.severity_slot)

        if channel.write_access_slot is not None:
            self.write_access_signal.disconnect(channel.write_access_slot)

        if channel.enum_strings_slot is not None:
            self.enum_strings_signal.disconnect(channel.enum_strings_slot)

        if channel.unit_slot is not None:
            self.unit_signal.disconnect(channel.unit_slot)

        if channel.upper_ctrl_limit_slot is not None:
            self.upper_ctrl_limit_signal.disconnect(channel.upper_ctrl_limit_slot)

        if channel.lower_ctrl_limit_slot is not None:
            self.lower_ctrl_limit_signal.disconnect(channel.lower_ctrl_limit_slot)

        if channel.prec_slot is not None:
            self.prec_signal.disconnect(channel.prec_slot)
 
        self.listener_count = self.listener_count - 1
        if self.listener_count < 1:
            self.close()
  
    def close(self):
        pass

class PyDMPlugin(object):
    protocol = None
    connection_class = PyDMConnection
    def __init__(self):
        self.connections = {}
    
    def get_address(self, channel):
        return str(channel.address.split(self.protocol + "://")[-1])
    
    def add_connection(self, channel):  
        address = self.get_address(channel)
        if address in self.connections:
            self.connections[address].add_listener(channel)
        else:
            self.connections[address] = self.connection_class(channel, address)
  
    def remove_connection(self, channel):
        address = self.get_address(channel)
        if address in self.connections:
            self.connections[address].remove_listener(channel)
            if self.connections[address].listener_count < 1:
                del self.connections[address]
