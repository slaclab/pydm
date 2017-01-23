import os
from ..PyQt.QtNetwork import QLocalSocket
from ..PyQt.QtCore import Qt, QDataStream, QByteArray, pyqtSlot, pyqtSignal
import capnp
import binascii
capnp.remove_import_hook()
ipc_protocol = capnp.load(os.path.join(os.path.dirname(__file__),'../ipc_protocol.capnp'))

class DataClientConnection(QLocalSocket):
  channelConnectRequested = pyqtSignal(str)
  channelDisconnectRequested = pyqtSignal(str)
  channelPutRequested = pyqtSignal([str, object])
  newWindowRequested = pyqtSignal(str)
  
  def __init__(self, parent=None):
    super(DataClientConnection,self).__init__(parent)
    #NOTE: Arbitrarily setting a read buffer size of 100 kB.  This is to protect us from something
    #happening that ends up allocating a huge amount of memory.  When transmitting large waveforms, this might be too small.
    self.setReadBufferSize(100000)
    self.pid = None
    self.channels = set()
    self.buffer = QByteArray()
    self.max_buffer_size = 100000000 #100 MB limit on the message buffer.
    self.inc_message_size = 0
    self.stream = QDataStream(self)
    self.stream.setVersion(QDataStream.Qt_4_8)
    self.readyRead.connect(self.read_from_socket)
    self.error.connect(self.handle_socket_error)
    
  @pyqtSlot()
  def read_from_socket(self):
    if self.inc_message_size == 0:
      self.inc_message_size = self.stream.readInt32()
    
    while (self.bytesAvailable() > 0) and (self.buffer.size() < self.inc_message_size):
      self.buffer.append(self.read(1))
      if self.buffer.size() > self.max_buffer_size:
        raise Exception("Data message size exceeded buffer capacity.")
        self.buffer.clear()
        break
    
    if self.buffer.size() < self.inc_message_size:
      #We are out of bytes at this point, but still don't have the complete message.
      #Keep what we have in the buffer, return, and wait for more bytes to come in.
      return
    
    #If we get this far, we have a complete message.
    try:
      msg = ipc_protocol.ClientMessage.from_bytes(str(self.buffer))
      self.process_message(msg)
    except capnp.lib.capnp.KjException:
      print("Failed to decode message of length {}".format(self.buffer.size()))
    self.inc_message_size = 0
    self.buffer.clear()
    #If there are still bytes available, we'll read more from the socket.
    if self.bytesAvailable() > 0:
      self.read_from_socket()    
  
  def process_message(self, message):
    which = message.which()
    if which == "initialize":
      if self.pid is not None:
        print("Initialize message sent, but client is already initialized.")
        return
      self.pid = message.initialize.clientPid
      #print("Local socket established to client with pid={}".format(self.pid))
    elif which == "channelRequest":
      chan = message.channelRequest
      #print("Channel requested from client {pid}: {channel}".format(pid=self.pid, channel=chan))
      self.channelConnectRequested.emit(chan)
    elif which == "channelDisconnect":
      chan = message.channelDisconnect
      #print("Channel disconnect requested from client {pid}: {channel}".format(pid=self.pid, channel=chan))
      if chan in self.channels:
        self.channelDisconnectRequested.emit(chan)
        self.channels.remove(chan)
    elif which == "newWindowRequest":
      self.newWindowRequested.emit(message.newWindowRequest.filename)
    elif which == "putRequest":
      chan = message.putRequest.channelName
      #print("Put requested from client {pid} for channel {channel}".format(pid=self.pid, channel=chan))
      valtype = message.putRequest.value.value.which()
      val = None
      if valtype == "string":
        val = message.putRequest.value.value.string
      elif valtype == "int":
        val = message.putRequest.value.value.int
      elif valtype == "float":
        val = message.putRequest.value.value.float
      elif valtype == "double":
        val = message.putRequest.value.value.double
      elif valtype == "intWaveform":
        val = np.array(message.putRequest.value.value.intWaveform)
      elif valtype == "floatWaveform":
        val = np.array(message.putRequest.value.value.floatWaveform)
      else:
        print("Client sent unhandled value type for put request: {}".format(valtype))
      self.channelPutRequested.emit(chan, val)
    else:
      print("Client sent unknown message type: {}".format(which))
    self.buffer.clear()
  
  def send_bytes(self, b):
    #This only works with QByteArray.
    self.stream << b
  
  def send_message(self, msg):
    b = msg.to_bytes()
    #print("Sending {0} message for channel {1} of size {2} to client.".format(msg.which(), msg.channelName, len(b)))
    self.stream << QByteArray(b)
    
  @pyqtSlot(int)
  def handle_socket_error(self, err):
    if err == QLocalSocket.ConnectionRefusedError:
      print("SERVER ERROR: Socket connection refused.")
    elif err == QLocalSocket.PeerClosedError:
      pass
      #print("SERVER ERROR: Socket closed by client.")
    elif err == QLocalSocket.ServerNotFoundError:
      print("SERVER ERROR: Server not found.")
    elif err == QLocalSocket.SocketAccessError:
      print("SERVER ERROR: Client process doesn't have sufficient privileges.")
    elif err == QLocalSocket.SocketResourceError:
      print("SERVER ERROR: System out of resources (Probably too many sockets open).")
    elif err == QLocalSocket.SocketTimeoutError:
      print("SERVER ERROR: Socket operation timed out.")
    elif err == QLocalSocket.DatagramTooLargeError:
      print("SERVER ERROR: Datagram too large.")
    elif err == QLocalSocket.ConnectionError:
      print("SERVER ERROR: An error occured with the connection.")
    elif err == QLocalSocket.UnsupportedSocketOperationError:
      print("SERVER ERROR: Socket operation not supported by operating system.")
    elif err == QLocalSocket.UnknownSocketError:
      print("SERVER ERROR: An unknown socket error occured.")