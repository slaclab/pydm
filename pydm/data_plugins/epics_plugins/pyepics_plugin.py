import epics
import numpy as np
from ..plugin import PyDMPlugin, PyDMConnection
from ...PyQt.QtCore import pyqtSlot, pyqtSignal, QObject, Qt

int_types = set((epics.dbr.INT, epics.dbr.CTRL_INT, epics.dbr.TIME_INT, epics.dbr.ENUM, epics.dbr.CTRL_ENUM, epics.dbr.TIME_ENUM, epics.dbr.TIME_LONG, epics.dbr.LONG, epics.dbr.CTRL_LONG, epics.dbr.CHAR, epics.dbr.TIME_CHAR, epics.dbr.CTRL_CHAR, epics.dbr.TIME_SHORT, epics.dbr.CTRL_SHORT))
float_types = set((epics.dbr.CTRL_FLOAT, epics.dbr.FLOAT, epics.dbr.TIME_FLOAT, epics.dbr.CTRL_DOUBLE, epics.dbr.DOUBLE, epics.dbr.TIME_DOUBLE))
class Connection(PyDMConnection):
  def __init__(self, channel, pv, parent=None):
    super(Connection, self).__init__(channel, pv, parent)
    self.pv = epics.PV(pv, callback=self.send_new_value, connection_callback=self.send_connection_state, form='ctrl', auto_monitor=True)
    self.add_listener(channel)
  
  def send_new_value(self, pvname=None, value=None, char_value=None, units=None, enum_strs=None, severity=None, count=None, write_access=None, ftype=None, upper_ctrl_limit=None, lower_ctrl_limit=None, *args, **kws):
    if severity != None:
      self.new_severity_signal.emit(int(severity))
    if write_access != None:
      self.write_access_signal.emit(write_access)
    if enum_strs != None:
      enum_strs = tuple(b.decode(encoding='ascii') for b in enum_strs)
      self.enum_strings_signal.emit(enum_strs)
    if units != None and len(units) > 0:
      if type(units) == bytes:
        units = units.decode()
      self.unit_signal.emit(units)
    if value is not None:
      if count > 1:
        self.new_waveform_signal.emit(value)
      else:
        if ftype in int_types:
          self.new_value_signal[int].emit(int(value))
        elif ftype in float_types:
          self.new_value_signal[float].emit(float(value))
        else:
          self.new_value_signal[str].emit(char_value)

    if upper_ctrl_limit != None:
      self.upper_ctrl_limit_signal.emit(upper_ctrl_limit)

    if lower_ctrl_limit != None:
      self.lower_ctrl_limit_signal.emit(lower_ctrl_limit)
    
      
  def send_connection_state(self, pvname=None, conn=None, *args, **kws):
    self.connection_state_signal.emit(conn)
  
  @pyqtSlot(int)
  @pyqtSlot(float)
  @pyqtSlot(str)
  def put_value(self, new_val):
    self.pv.put(new_val)
  
  @pyqtSlot(np.ndarray)
  def put_waveform(self, new_waveform_val):
    self.pv.put(new_waveform_val)
    
  def add_listener(self, channel):
    super(Connection, self).add_listener(channel)
    #If we are adding a listener to an already existing PV, we need to
    #manually send the signals indicating that the PV is connected, what the latest value is, etc.
    if epics.ca.isConnected(self.pv.chid):
      self.send_connection_state(conn=True)
      self.pv.run_callbacks()
    #If the channel is used for writing to PVs, hook it up to the 'put' methods.  
    if channel.value_signal is not None:
        try:
            channel.value_signal[str].connect(self.put_value, Qt.QueuedConnection)
        except KeyError:
            pass
        try:
            channel.value_signal[int].connect(self.put_value, Qt.QueuedConnection)
        except KeyError:
            pass
        try:
            channel.value_signal[float].connect(self.put_value, Qt.QueuedConnection)
        except KeyError:
            pass
    if channel.waveform_signal is not None:
        try:
            channel.waveform_signal.connect(self.put_value, Qt.QueuedConnection)
        except KeyError:
            pass

  def close(self):
    self.pv.disconnect()

class PyEPICSPlugin(PyDMPlugin):
  #NOTE: protocol is intentionally "None" to keep this plugin from getting directly imported.
  #If this plugin is chosen as the One True EPICS Plugin in epics_plugin.py, the protocol will
  #be properly set before it is used.
  protocol = None
  connection_class = Connection
