from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, Qt
from numpy import ndarray
class PyDMConnection(QObject):
  new_value_signal = pyqtSignal([float],[int],[str])
  new_waveform_signal = pyqtSignal(ndarray)
  connection_state_signal = pyqtSignal(bool)
  new_severity_signal = pyqtSignal(int)
  write_access_signal = pyqtSignal(bool)
  enum_strings_signal = pyqtSignal(tuple)
  unit_signal = pyqtSignal(str)
  def __init__(self, channel, address, parent=None):
    super(PyDMConnection, self).__init__(parent)
    self.listener_count = 0
  
  def add_listener(self, channel):
    self.listener_count = self.listener_count + 1
    try:
      self.connection_state_signal.connect(channel.connection_slot, Qt.QueuedConnection)
    except:
      pass
    try:
      self.new_value_signal[int].connect(channel.value_slot, Qt.QueuedConnection)
    except:
      pass
    try:
      self.new_value_signal[float].connect(channel.value_slot, Qt.QueuedConnection)
    except:
      pass
    try:
      self.new_value_signal[str].connect(channel.value_slot, Qt.QueuedConnection)
    except:
      pass
    try:
      self.new_waveform_signal.connect(channel.waveform_slot, Qt.QueuedConnection)
    except:
      pass
    try:
      self.new_severity_signal.connect(channel.severity_slot, Qt.QueuedConnection)
    except:
      pass
    try:
      self.write_access_signal.connect(channel.write_access_slot, Qt.QueuedConnection)
    except:
      pass
    try:
      self.enum_strings_signal.connect(channel.enum_strings_slot, Qt.QueuedConnection)
    except:
      pass
    try:
      self.unit_signal.connect(channel.unit_slot, Qt.QueuedConnection)
    except:
      pass
      
  def remove_listener(self):
    self.listener_count = self.listener_count - 1
    if self.listener_count < 1:
      self.close()
  
  def close(self):
    pass

class PyDMPlugin:
  protocol = None
  connection_class = PyDMConnection
  def __init__(self):
    self.connections = {}
  
  def get_address(self, channel):
    return str(channel.address.split(self.protocol)[1])
    
  def add_connection(self, channel):  
    address = self.get_address(channel)
    if address in self.connections:
      self.connections[address].add_listener(channel)
    else:
      self.connections[address] = self.connection_class(channel, address)
  
  def remove_connection(self, channel):
    address = self.get_address(channel)
    if address in self.connections:
      self.connections[address].remove_listener()
      if self.connections[address].listener_count < 1:
        del self.connections[address]
      
