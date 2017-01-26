from os import path
import numpy as np
from ..PyQt.QtCore import Qt, QThread, QByteArray, QDataStream, QReadWriteLock, QReadLocker, QWriteLocker, pyqtSlot, pyqtSignal
from ..PyQt.QtNetwork import QLocalSocket
import capnp
capnp.remove_import_hook()

class ServerConnection(QLocalSocket):
  server_connection_established = pyqtSignal()
  def __init__(self, servername, pid, parent=None):
    super(ServerConnection, self).__init__(parent=parent)
    self.servername = servername
    self.pid = pid
    self.lock = QReadWriteLock()
    self.data_for_channel = {}
    self.ipc_protocol = capnp.load(path.join(path.dirname(__file__),'../ipc_protocol.capnp'))
    self.setReadBufferSize(100000)    
    self.stream = QDataStream(self)
    self.inc_message_size = 0
    self.buffer = QByteArray()
    self.max_buffer_size = 100000000 #100 Mb max buffer size, really big but probably not large enough to really screw anything up.
    self.stream.setVersion(QDataStream.Qt_4_8)
    self.connected.connect(self.socket_connected)
    self.readyRead.connect(self.read_from_socket)
    self.error.connect(self.handle_socket_error)
    
  @pyqtSlot()
  def start_connection(self):
    self.connectToServer(self.servername)
  
  @pyqtSlot()
  def disconnect(self):
    print("Disconnecting")
    self.disconnectFromServer()
    
  @pyqtSlot()
  def socket_connected(self):
    msg = self.ipc_protocol.ClientMessage.new_message()
    init_msg = msg.init('initialize')
    init_msg.clientPid = self.pid
    self.send_msg(msg)
    self.server_connection_established.emit()
    
  @pyqtSlot(object)
  def send_msg(self, msg):
    b = QByteArray(msg.to_bytes())
    self.stream << b

  @pyqtSlot(QLocalSocket.LocalSocketError)
  def handle_socket_error(self, err):
    if err == QLocalSocket.ConnectionRefusedError:
      print("CLIENT ERROR: Socket connection refused.")
    elif err == QLocalSocket.PeerClosedError:
      print("CLIENT ERROR: Socket closed by host.")
    elif err == QLocalSocket.ServerNotFoundError:
      print("CLIENT ERROR: Server not found.")
    elif err == QLocalSocket.SocketAccessError:
      print("CLIENT ERROR: Client process doesn't have sufficient privileges.")
    elif err == QLocalSocket.SocketResourceError:
      print("CLIENT ERROR: System out of resources (Probably too many sockets open).")
    elif err == QLocalSocket.SocketTimeoutError:
      print("CLIENT ERROR: Socket operation timed out.")
    elif err == QLocalSocket.DatagramTooLargeError:
      print("CLIENT ERROR: Datagram too large.")
    elif err == QLocalSocket.ConnectionError:
      print("CLIENT ERROR: An error occured with the connection.")
    elif err == QLocalSocket.UnsupportedSocketOperationError:
      print("CLIENT ERROR: Socket operation not supported by operating system.")
    elif err == QLocalSocket.UnknownSocketError:
      print("CLIENT ERROR: An unknown socket error occured.")
  
  @pyqtSlot()
  def read_from_socket(self):
    if self.inc_message_size == 0:
      self.inc_message_size = self.stream.readInt32()
      self.buffer.reserve(self.inc_message_size)
    
    while (self.bytesAvailable() > 0) and (self.buffer.size() < self.inc_message_size):
      bytes_remaining = self.inc_message_size - self.buffer.size()
      if self.bytesAvailable() >= bytes_remaining and (self.buffer.size() + bytes_remaining) < self.max_buffer_size:
        self.buffer.append(self.read(bytes_remaining))
      elif (self.buffer.size() + self.bytesAvailable()) < self.max_buffer_size:
        self.buffer.append(self.readAll())  
      else:
        break
    
    if self.buffer.size() < self.inc_message_size:
      #We are out of bytes at this point, but still don't have the complete message.
      #Return and wait for more bytes to come in.
      return
    
    #If we get this far, we have a complete message.
    try:
      msg = self.ipc_protocol.ServerMessage.from_bytes(bytes(self.buffer))
      self.process_message(msg)
    except capnp.lib.capnp.KjException:
      print("Failed to decode message of length {}".format(self.buffer.size()))
    self.inc_message_size = 0
    self.buffer.clear()
    #If there are still bytes available, we'll read more from the socket.
    if self.bytesAvailable() > 0:
      self.read_from_socket()
  
  def process_message(self, msg):
    try:
      #Probably don't need a read lock here since this thread is the only one that writes to the structure.
      cd = self.data_for_channel[msg.channelName]
    except KeyError:
      return
    w = msg.which()
    #print("Recieved {} message for {} of size {}".format(w, msg.channelName, self.buffer.size()))
    which = msg.which()
    if which == "value":
      v = msg.value
      vtype = v.value.which()
      if vtype == "string":
        with QWriteLocker(self.lock):
          cd.value = v.value.string
          cd.needs_update = True
      elif vtype == "int":
        with QWriteLocker(self.lock):
          cd.value = v.value.int
          cd.needs_update = True
      elif vtype == "float":
        with QWriteLocker(self.lock):
          cd.value = v.value.float
          cd.needs_update = True
      elif vtype == "double":
        with QWriteLocker(self.lock):
          cd.value = v.value.double
          cd.needs_update = True
      elif vtype == "intWaveform":
        with QWriteLocker(self.lock):
          cd.value = np.array(v.value.intWaveform, dtype=np.int64)
          cd.needs_update = True
      elif vtype == "floatWaveform":
        with QWriteLocker(self.lock):
          cd.value = np.array(v.value.floatWaveform, dtype=np.float64)
          cd.needs_update = True
      elif vtype == "charWaveform":
        with QWriteLocker(self.lock):
          cd.value = np.array(v.value.charWaveform, dtype=np.uint8)
          cd.needs_update = True
      else:
        raise Exception("Server sent value message with unhandled value type: {}".format(vtype))
    elif which == "connectionState":
      with QWriteLocker(self.lock):
        cd.connection_state = msg.connectionState
        cd.needs_update = True
    elif which == "severity":
      if msg.severity == "noAlarm":
        with QWriteLocker(self.lock):
          cd.severity = 0
          cd.needs_update = True
      elif msg.severity == "minor":
        with QWriteLocker(self.lock):
          cd.severity = 1
          cd.needs_update = True
      elif msg.severity == "major":
        with QWriteLocker(self.lock):
          cd.severity = 2
          cd.needs_update = True
      elif msg.severity == "invalid":
        with QWriteLocker(self.lock):
          cd.severity = 3
          cd.needs_update = True
      elif msg.severity == "disconnected":
        with QWriteLocker(self.lock):
          cd.severity = 4
          cd.needs_update = True
    elif which == "writeAccess":
      with QWriteLocker(self.lock):
        cd.write_access = msg.writeAccess
        cd.needs_update = True
    elif which == "enumStrings":
      pass
    elif which == "unit":
      with QWriteLocker(self.lock):
        cd.units = msg.unit
        cd.needs_update = True
    elif which == "precision":
      with QWriteLocker(self.lock):
        cd.precision = msg.precision
        cd.needs_update = True
    else:
      print("Server sent unknown message type: {}".format(which))

  @pyqtSlot(str)
  def connect_to_data_channel(self, address):
    if address is None:
      return
    address = str(address)
    if address not in self.data_for_channel:
      cd = ChannelData()
      cd.listeners = 1
      with QWriteLocker(self.lock):
        self.data_for_channel[address] = cd
    else:
      cd = self.data_for_channel[address]  
      with QWriteLocker(self.lock):
        cd.listeners += 1
    #print("Sending channel request for: {}".format(address))
    msg = self.ipc_protocol.ClientMessage.new_message()
    msg.channelRequest = address
    self.send_msg(msg)
  
  @pyqtSlot(str)
  def disconnect_from_data_channel(self, address): 
    if address is None:
      return
    address = str(address)
    cd = self.data_for_channel[address]
    with QWriteLocker(self.lock):
      cd.listeners -= 1
      if cd.listeners < 1:
        del self.data_for_channel[address]      
    #print("Sending channel disconnect request for: {}".format(address))
    msg = self.ipc_protocol.ClientMessage.new_message()
    msg.channelDisconnect = address
    self.send_msg(msg)
    
  @pyqtSlot(str)
  def new_pydm_process(self, ui_file):
    print("Requesting to launch new display process for file {}".format(ui_file))
    msg = self.ipc_protocol.ClientMessage.new_message()
    win_msg = msg.init('newWindowRequest')
    win_msg.filename = ui_file
    self.send_msg(msg)

class ChannelData(object):
  __slots__ = ('value', 'connection_state', 'severity', 'write_access', 'units', 'precision', 'enum_strings', 'listeners', 'needs_update')
  def __init__(self):
    self.value = None
    self.connection_state = False
    self.severity = 4
    self.write_access = False
    self.units = None
    self.precision = None
    self.listeners = 0
    self.needs_update = False
  
