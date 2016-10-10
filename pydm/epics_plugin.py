import epics
import numpy as np
from .plugin import PyDMPlugin, PyDMConnection
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, Qt

class Connection(PyDMConnection):
  def __init__(self, channel, pv, parent=None):
    super(Connection, self).__init__(channel, pv, parent)
    self.pv = epics.PV(pv, callback=self.send_new_value, connection_callback=self.send_connection_state, form='ctrl', auto_monitor=True)
    self.add_listener(channel)
  
  def send_new_value(self, pvname=None, value=None, char_value=None, units=None, enum_strs=None, severity=None, count=None, write_access=None, ftype=None, *args, **kws):
    if severity != None:
      self.new_severity_signal.emit(int(severity))
    if write_access != None:
      self.write_access_signal.emit(write_access)
    if enum_strs != None:
      self.enum_strings_signal.emit(enum_strs)
    if units != None and len(units) > 0:
      self.unit_signal.emit(units)
    if count > 1:
      self.new_waveform_signal.emit(value)
    else:
      if ftype in (epics.dbr.INT, epics.dbr.CTRL_INT, epics.dbr.TIME_INT, epics.dbr.ENUM, epics.dbr.CTRL_ENUM, epics.dbr.TIME_ENUM):
        self.new_value_signal[int].emit(int(value))
      elif ftype in (epics.dbr.CTRL_FLOAT, epics.dbr.FLOAT, epics.dbr.TIME_FLOAT, epics.dbr.CTRL_DOUBLE, epics.dbr.DOUBLE, epics.dbr.TIME_DOUBLE):
        self.new_value_signal[float].emit(float(value))
      else:
        self.new_value_signal[str].emit(char_value)
    
      
  def send_connection_state(self, pvname=None, conn=None, *args, **kws):
    self.connection_state_signal.emit(conn)
  
  @pyqtSlot(str)
  def put_value(self, new_val):
    self.pv.put(str(new_val))
  
  @pyqtSlot(np.ndarray)
  def put_value(self, new_waveform_val):
    self.pv.put(new_waveform_val)
    
  def add_listener(self, channel):
    super(Connection, self).add_listener(channel)
    #If we are adding a listener to an already existing PV, we need to
    #manually send the signals indicating that the PV is connected, what the latest value is, etc.
    if epics.ca.isConnected(self.pv.chid):
      self.send_connection_state(conn=True)
      self.pv.run_callbacks()
      
    try:
      channel.value_signal.connect(self.put_value, Qt.QueuedConnection)
    except:
      pass
      
  def close(self):
    self.pv.disconnect()

class EPICSPlugin(PyDMPlugin):
  protocol = "ca://"
  connection_class = Connection
