from PyQt4.QtCore import pyqtSlot, pyqtSignal, QObject, Qt
from numpy import ndarray
class PyDMConnection(QObject):
  new_value_signal = pyqtSignal(str)
  new_waveform_signal = pyqtSignal(ndarray)
  connection_state_signal = pyqtSignal(bool)
  new_severity_signal = pyqtSignal(int)
  write_access_signal = pyqtSignal(bool)
  def __init__(self, channel, address, parent=None):
    super(PyDMConnection, self).__init__(parent)
  
  def add_listener(self, channel):
    try:
      self.connection_state_signal.connect(channel.connection_slot, Qt.QueuedConnection)
    except:
      pass
    try:
      self.new_value_signal.connect(channel.value_slot, Qt.QueuedConnection)
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

class PyDMPlugin:
  protocol = None
  connection_class = PyDMConnection
  def __init__(self):
    self.connections = {}
    
  def add_connection(self, channel):  
    address = str(channel.address.split(self.protocol)[1])
    if address in self.connections:
      self.connections[address].add_listener(channel)
    else:
      self.connections[address] = self.connection_class(channel, address)
      
