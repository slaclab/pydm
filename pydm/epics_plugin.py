import epics
import numpy as np
from .plugin import PyDMPlugin, PyDMConnection
from PyQt4.QtCore import pyqtSlot, pyqtSignal, QObject, Qt, QString

class Connection(PyDMConnection):
  def __init__(self, channel, pv, parent=None):
    super(Connection, self).__init__(channel, pv, parent)
    self.add_listener(channel)
    self.pv = epics.PV(pv, callback=self.send_new_value, connection_callback=self.send_connection_state, form='ctrl')
  
  def send_new_value(self, pvname=None, value=None, severity=None, count=None, write_access=None, *args, **kws):
    if count > 1:
      self.new_waveform_signal.emit(value)
    else:
      self.new_value_signal.emit(str(value))
    if severity != None:
      self.new_severity_signal.emit(int(severity))
    if write_access != None:
      self.write_access_signal.emit(write_access)
      
  def send_connection_state(self, pvname=None, conn=None, *args, **kws):
    self.connection_state_signal.emit(conn)
  
  @pyqtSlot(QString)
  def put_value(self, new_val):
    self.pv.put(str(new_val))
    
  def add_listener(self, channel):
    super(Connection, self).add_listener(channel)
    try:
      channel.value_signal.connect(self.put_value, Qt.QueuedConnection)
    except:
      pass

class EPICSPlugin(PyDMPlugin):
  protocol = "ca://"
  connection_class = Connection