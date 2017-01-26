import numpy as np
from ..PyQt.QtCore import pyqtSlot, pyqtSignal, QObject, Qt, QByteArray
import os
import capnp
import time
capnp.remove_import_hook()
ipc_protocol = capnp.load(os.path.join(os.path.dirname(__file__),'../ipc_protocol.capnp'))

class PyDMConnection(QObject):
    """PyDMConnection represents a connection to a plugin data channel."""
    protocol = None
    data_message_signal =     pyqtSignal(object)
    severity_map = {0: "noAlarm",
                    1: "minor",
                    2: "major",
                    3: "invalid",
                    4: "disconnected"}
    
    def __init__(self, channel_name, parent=None):
        self.channel_name = str(channel_name)
        self.address = self.get_address(channel_name)
        super(PyDMConnection, self).__init__(parent)
        self.listener_count = 0
  
    def get_address(self, channel):
        return str(channel.split(self.protocol)[1])
  
    def add_listener(self):
        self.listener_count = self.listener_count + 1
        
    def remove_listener(self):
        self.listener_count = self.listener_count - 1
        if self.listener_count < 1:
            self.close()
  
    def new_value_message(self, val, timestamp=None):
        msg = ipc_protocol.ServerMessage.new_message()
        msg.channelName = self.channel_name
        val_msg = msg.init('value')
        if isinstance(val, int):
            val_msg.value.int = val
        elif isinstance(val, float):
            val_msg.value.double = val
        elif isinstance(val, str):
            val_msg.value.string = val
        elif isinstance(val, np.ndarray):
            if val.dtype == np.float64:
                val_msg.value.init('floatWaveform', len(val))
                val_msg.value.floatWaveform = val.tolist()
            elif val.dtype == np.int64:
                val_msg.value.init('intWaveform', len(val))
                val_msg.value.intWaveform = val.tolist()
            elif val.dtype == np.uint8:
                val_msg.value.init('charWaveform', len(val))
                val_msg.value.charWaveform = val.tolist()
            else:
                raise Exception("Unhandled dtype for waveform: {}".format(val.dtype))
        else:
            raise Exception("Unhandled val type: {}".format(type(val)))  
        if timestamp is None:
            timestamp = time.time()
        msg.timestamp = timestamp
        return msg
    
    def connection_state_message(self, state, timestamp=None):
        msg = ipc_protocol.ServerMessage.new_message()
        msg.channelName = self.channel_name
        msg.connectionState = state
        if timestamp is None:
            timestamp = time.time()
        msg.timestamp = timestamp
        return msg
        
    def severity_message(self, severity, timestamp=None):
        msg = ipc_protocol.ServerMessage.new_message()
        msg.channelName = self.channel_name
        msg.severity = self.severity_map[severity]
        msg.timestamp = timestamp
        return msg
    
    def write_access_message(self, write_access, timestamp=None):
        msg = ipc_protocol.ServerMessage.new_message()
        msg.channelName = self.channel_name
        msg.writeAccess = write_access
        if timestamp is None:
            timestamp = time.time()
        msg.timestamp = timestamp
        return msg
    
    def enum_strings_message(self, enum_strings, timestamp=None):
        msg = ipc_protocol.ServerMessage.new_message()
        msg.channelName = self.channel_name
        msg.init('enumStrings', len(enum_strings))
        for i, v in enumerate(enum_strings):
          msg.enumStrings[i] = v
        #msg.enumStrings = enum_strings
        msg.timestamp = timestamp
        return msg
    
    def unit_message(self, unit, timestamp=None):
        msg = ipc_protocol.ServerMessage.new_message()
        msg.channelName = self.channel_name
        msg.unit = unit
        msg.timestamp = timestamp
        return msg
    
    def precision_message(self, prec, timestamp=None):
        msg = ipc_protocol.ServerMessage.new_message()
        msg.channelName = self.channel_name
        msg.precision = prec
        msg.timestamp = timestamp
        return msg
        
    def close(self):
        pass
    
    def put_value(self, value):
        raise NotImplementedError("Put Value not implemented.")

class PyDMPlugin(QObject):
    protocol = None
    connection_class = PyDMConnection
    data_message_signal = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super(PyDMPlugin, self).__init__(parent)
        self.connections = {}

    def add_connection(self, channel):
        if channel not in self.connections:
          conn = self.connection_class(channel, parent=self)
          self.connections[channel] = conn
          conn.data_message_signal.connect(self.send_data_message)
        self.connections[channel].add_listener()
            
    def remove_connection(self, channel):
        if channel in self.connections:
            self.connections[channel].remove_listener()
        if self.connections[channel].listener_count < 1:
            del self.connections[channel]
            
    def remove_all_connections(self):
      for (channel, connection) in self.connections.items():
        connection.close()
        del connection
    
    def put_value_for_channel(self, channel, value):
        conn = self.connections[channel]
        conn.put_value(value)
    
    @pyqtSlot(object)
    def send_data_message(self, msg):
        self.data_message_signal.emit(msg)