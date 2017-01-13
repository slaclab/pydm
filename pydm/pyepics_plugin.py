import epics
import numpy as np
from .plugin import PyDMPlugin, PyDMConnection
from .PyQt.QtCore import pyqtSlot, pyqtSignal, QObject, Qt

class Connection(PyDMConnection):
  protocol = "ca://"
  def __init__(self, channel_name, parent=None):
    super(Connection, self).__init__(channel_name, parent)
    self.pv = epics.PV(self.address, callback=self.send_new_value, connection_callback=self.send_connection_state, form='ctrl', auto_monitor=True)
    self.add_listener()
  
  def send_new_value(self, pvname=None, value=None, char_value=None, units=None, enum_strs=None, severity=None, count=None, write_access=None, ftype=None, timestamp=None, *args, **kws):
    if severity != None:
      self.data_message_signal.emit(self.severity_message(int(severity), timestamp))
    if write_access != None:
      self.data_message_signal.emit(self.write_access_message(write_access, timestamp))
    if enum_strs != None:
      enum_strs = tuple(b.decode(encoding='ascii') for b in enum_strs)
      self.data_message_signal.emit(self.enum_strings_message(enum_strs, timestamp))
    if units != None and len(units) > 0:
      self.data_message_signal.emit(self.unit_message(units, timestamp))
    if count > 1:
      self.data_message_signal.emit(self.new_value_message(value, timestamp))
    else:
      if ftype in (epics.dbr.INT, epics.dbr.CTRL_INT, epics.dbr.TIME_INT, epics.dbr.ENUM, epics.dbr.CTRL_ENUM, epics.dbr.TIME_ENUM):
        self.data_message_signal.emit(self.new_value_message(int(value), timestamp))
      elif ftype in (epics.dbr.CTRL_FLOAT, epics.dbr.FLOAT, epics.dbr.TIME_FLOAT, epics.dbr.CTRL_DOUBLE, epics.dbr.DOUBLE, epics.dbr.TIME_DOUBLE):
        self.data_message_signal.emit(self.new_value_message(float(value), timestamp))
      else:
        self.data_message_signal.emit(self.new_value_message(char_value, str, timestamp))
    
  def send_connection_state(self, pvname=None, conn=None, *args, **kws):
    self.data_message_signal.emit(self.connection_state_message(conn))
  
  @pyqtSlot(int)
  @pyqtSlot(float)
  @pyqtSlot(str)
  @pyqtSlot(np.ndarray)
  def put_value(self, new_val):
    self.pv.put(new_val)
    
  def add_listener(self, channel):
    super(Connection, self).add_listener()
    #If we are adding a listener to an already existing PV, we need to
    #manually send the signals indicating that the PV is connected, what the latest value is, etc.
    if epics.ca.isConnected(self.pv.chid):
      self.send_connection_state(conn=True)
      self.pv.run_callbacks()
      
    #try:
    #  channel.value_signal[str].connect(self.put_value, Qt.QueuedConnection)
    #  channel.value_signal[int].connect(self.put_value, Qt.QueuedConnection)
    #  channel.value_signal[float].connect(self.put_value, Qt.QueuedConnection)
    #except:
    #  pass
      
    #try:
    #  channel.waveform_signal.connect(self.put_waveform, Qt.QueuedConnection)
    #except:
    #  pass

  def close(self):
    self.pv.disconnect()

class PyEPICSPlugin(PyDMPlugin):
  protocol = "ca://"
  connection_class = Connection
