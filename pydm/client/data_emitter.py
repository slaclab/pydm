from os import path
import numpy as np
from ..PyQt.QtCore import QObject, pyqtSignal, pyqtSlot
import capnp
capnp.remove_import_hook()
ipc_protocol = capnp.load(path.join(path.dirname(__file__),'../ipc_protocol.capnp'))

class DataEmitter(QObject):
  """DataEmitter emits signals whenever a data channel updates.
  Multiple PyDMChannels may be connected to the same DataEmitter.
  The DataEmitter also recieves put value signals from PyDMChannels,
  and generates an IPC message, and emits a signal with the message."""
  #These signals get connected to PyDMChannels
  new_value_signal =        pyqtSignal([float],[int],[str])
  new_waveform_signal =     pyqtSignal(np.ndarray)
  connection_state_signal = pyqtSignal(bool)
  new_severity_signal =     pyqtSignal(int)
  write_access_signal =     pyqtSignal(bool)
  enum_strings_signal =     pyqtSignal(tuple)
  unit_signal =             pyqtSignal(str)
  prec_signal =             pyqtSignal(int)
  
  #This signal gets connected to the application
  put_value_signal = pyqtSignal(object)
  
  def __init__(self, channel_name, parent=None):
    super(DataEmitter, self).__init__(parent)
    self.listener_count = 0
    self.channel_name = channel_name
    
  def add_listener(self, channel):
    self.listener_count += 1    
    if channel.value_signal is not None:
      channel.value_signal[str].connect(self.put_value)
      channel.value_signal[int].connect(self.put_value)
      channel.value_signal[float].connect(self.put_value)
    if channel.waveform_signal is not None:
      channel.waveform_signal.connect(self.put_value)
      
  @pyqtSlot(int)
  @pyqtSlot(float)
  @pyqtSlot(str)
  @pyqtSlot(np.ndarray)
  def put_value(self, val):
    msg = ipc_protocol.ClientMessage.new_message()
    put_msg = msg.init('putRequest')
    put_msg.channelName = self.channel_name
    val_msg = put_msg.init('value')
    if isinstance(val, int):
      val_msg.value.int = val
    elif isinstance(val, float):
      val_msg.value.double = val
    elif isinstance(val, str):
      val_msg.value.string = val
    elif isinstance(val, np.ndarray):
      w = None
      if val.dtype == np.float64:
        w = val_msg.value.init('floatWaveform', len(val))
      elif val.dtype == np.int64:
        w = val_msg.value.init('intWaveform', len(val))
      elif val.dtype == np.uint8:
        w = val_msg.value.init('charWaveform', len(val))
      if w:
        w = val.tolist()
      else:
        raise Exception("Unhandled dtype for waveform put: {}".format(val.dtype))
    else:
      raise Exception("Unhandled value type for put request: {}".format(type(val)))  
    self.put_value_signal.emit(msg)
      
  def remove_listener(self, channel=None):
    if self.listener_count < 1:
      return
    self.listener_count -= 1