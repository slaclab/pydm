"""
Main Application Module

Contains our PyDMApplication class with core connection and loading logic and
our PyDMMainWindow class with navigation logic.
"""
from os import path
import imp
import sys
import signal
import subprocess
import re
import numpy as np
from .PyQt.QtCore import Qt, QObject, QEvent, QByteArray, QDataStream, QIODevice, pyqtSlot, pyqtSignal
from .PyQt.QtNetwork import QLocalSocket
from .PyQt.QtGui import QApplication, QColor, QWidget
from .PyQt import uic
from .main_window import PyDMMainWindow
import capnp
import binascii
capnp.remove_import_hook()
ipc_protocol = capnp.load(path.join(path.dirname(__file__),'ipc_protocol.capnp'))
  
class PyDMApplication(QApplication):  
  severity_map = {"noAlarm": 0,
                  "minor": 1,
                  "major": 2,
                  "invalid": 3,
                  "disconnected": 4}
  
  #HACK. To be replaced with some stylesheet stuff eventually.
  alarm_severity_color_map = {
    0: QColor(0, 0, 0), #NO_ALARM
    1: QColor(220, 220, 20), #MINOR_ALARM
    2: QColor(240, 0, 0), #MAJOR_ALARM
    3: QColor(240, 0, 240) #INVALID_ALARM
  }
  
  #HACK. To be replaced with some stylesheet stuff eventually.
  connection_status_color_map = {
    False: QColor(255, 255, 255),
    True: QColor(0, 0, 0)
  }
  
  def __init__(self, servername, ui_file=None, command_line_args=[]):
    super(PyDMApplication, self).__init__(command_line_args)
    self.directory_stack = ['']
    self.windows = {}
    self.socket = QLocalSocket(self)
    self.socket.setReadBufferSize(100000)
    #Open a window if a file was provided.
    if ui_file is not None:
      self.make_window(ui_file)
      self.had_file = True
    else:
      self.had_file = False
    #Re-enable sigint (usually blocked by pyqt)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    self.data_emitters = {}
    
    self.stream = QDataStream(self.socket)
    self.inc_message_size = 0
    self.buffer = QByteArray()
    self.max_buffer_size = 100000000 #100 Mb max buffer size, really big but probably not large enough to really screw anything up.
    self.stream.setVersion(QDataStream.Qt_4_8)
    self.socket.connected.connect(self.socket_connected)
    self.socket.readyRead.connect(self.read_from_socket)
    self.socket.error.connect(self.handle_socket_error)
    self.socket.connectToServer(servername)
  
  def is_connected(self):
    return self.socket.state() == QLocalSocket.ConnectedState
  
  @pyqtSlot(object)
  def send_msg(self, msg):
    b = msg.to_bytes()
    self.stream << QByteArray(b)
  
  @pyqtSlot()
  def socket_connected(self):
    #print("Client successfully connected to server!")
    msg = ipc_protocol.ClientMessage.new_message()
    init_msg = msg.init('initialize')
    init_msg.clientPid = self.applicationPid()
    self.send_msg(msg)
    self.make_connections()
  
  @pyqtSlot(int)
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
    
    while (self.socket.bytesAvailable() > 0) and (self.buffer.size() < self.inc_message_size):
      self.buffer.append(self.socket.read(1))
      if self.buffer.size() > self.max_buffer_size:
        raise Exception("Data message size exceeded buffer capacity.")
        self.buffer.clear()
        break
    
    if self.buffer.size() < self.inc_message_size:
      #We are out of bytes at this point, but still don't have the complete message.
      #Return and wait for more bytes to come in.
      return
    
    #If we get this far, we have a complete message.
    try:
      msg = ipc_protocol.ServerMessage.from_bytes(str(self.buffer))
      self.process_message(msg)
    except capnp.lib.capnp.KjException:
      print("Failed to decode message of length {}".format(self.buffer.size()))
    self.inc_message_size = 0
    self.buffer.clear()
    #If there are still bytes available, we'll read more from the socket.
    if self.socket.bytesAvailable() > 0:
      self.read_from_socket()  
      
  def process_message(self, msg):
    try:
      emitter = self.data_emitters[msg.channelName]
    except KeyError:
      return
    w = msg.which()
    #print("Recieved {} message for {} of size {}".format(w, msg.channelName, self.buffer.size()))
    which = msg.which()
    if which == "value":
      v = msg.value
      vtype = v.value.which()
      if vtype == "string":
        emitter.new_value_signal[str].emit(v.value.string)
      elif vtype == "int":
        emitter.new_value_signal[int].emit(v.value.int)
      elif vtype == "float":
        emitter.new_value_signal[float].emit(v.value.float)
      elif vtype == "double":
        emitter.new_value_signal[float].emit(v.value.double)
      elif vtype == "intWaveform":
        emitter.new_waveform_signal.emit(np.array(v.value.intWaveform))
      elif vtype == "floatWaveform":
        emitter.new_waveform_signal.emit(np.array(v.value.floatWaveform))
      elif vtype == "charWaveform":
        emitter.new_waveform_signal.emit(np.array(v.value.charWaveform, dtype=np.uint8))
      else:
        raise Exception("Server sent value message with unhandled value type: {}".format(vtype))
    elif which == "connectionState":
      emitter.connection_state_signal.emit(msg.connectionState)
    elif which == "severity":
      #emitter.new_severity_signal.emit(self.severity_map[str(msg.severity)])
      #NOTE: This doesn't use the severity_map we define at the top, because capnp enums can't be used as dictionary keys right now.
      #If this gets fixed (looks like it is in the pycapnp dev branch but not released as of 1/23/2017), use that map!
      if msg.severity == "noAlarm":
        emitter.new_severity_signal.emit(0)
      elif msg.severity == "minor":
        emitter.new_severity_signal.emit(1)
      elif msg.severity == "major":
        emitter.new_severity_signal.emit(2)
      elif msg.severity == "invalid":
        emitter.new_severity_signal.emit(3)
      elif msg.severity == "disconnected":
        emitter.new_severity_signal.emit(4)
    elif which == "writeAccess":
      emitter.write_access_signal.emit(msg.writeAccess)
    elif which == "enumStrings":
      pass
    elif which == "unit":
      emitter.unit_signal.emit(msg.unit)
    elif which == "precision":
      emitter.prec_signal.emit(msg.precision)
    else:
      print("Server sent unknown message type: {}".format(which))
      
  def exec_(self):
      """
      Execute the QApplication
      """
      # Connect to top-level widgets that were not loaded from file
      # These are usually testing/debug widgets.
      if not self.had_file:
        self.make_connections()
      return super(PyDMApplication,self).exec_()

  def exit(self, return_code):
    self.socket.flush()
    self.socket.disconnectFromServer()
    super(PyDMApplication, self).exit(return_code)

  def make_connections(self):
    for widget in self.topLevelWidgets():
      self.establish_widget_connections(widget)
  
  def new_window(self, ui_file):
    """new_window() gets called whenever a request to open a new window is made."""
    (filename, extension) = path.splitext(ui_file)
    if extension == '.ui':
      self.new_pydm_process(ui_file)
    elif extension == '.py':
      self.new_pydm_process(ui_file)
  
  def make_window(self, ui_file):
    """make_window instantiates a new PyDMMainWindow, adds it to the
    application's list of windows, and opens ui_file in the window."""
    main_window = PyDMMainWindow()
    main_window.open_file(ui_file)
    main_window.show()
    self.windows[main_window] = path.dirname(ui_file)
    #If we are launching a new window, we don't want it to sit right on top of an existing window.
    if len(self.windows) > 1:
      main_window.move(main_window.x() + 10, main_window.y() + 10)

  def new_pydm_process(self, ui_file):
    print("Requesting to launch new display process for file {}".format(ui_file))
    msg = ipc_protocol.ClientMessage.new_message()
    win_msg = msg.init('newWindowRequest')
    win_msg.filename = ui_file
    self.send_msg(msg)
    
  def close_window(self, window):
    del self.windows[window]

  def load_ui_file(self, uifile):
    return uic.loadUi(uifile)
    
  def load_py_file(self, pyfile):
    #Add the intelligence module directory to the python path, so that submodules can be loaded.  Eventually, this should go away, and intelligence modules should behave as real python modules.
    module_dir = path.dirname(path.abspath(pyfile))
    sys.path.append(module_dir)

    #Now load the intelligence module.
    module = imp.load_source('intelclass', pyfile)
    return module.intelclass()

  def open_file(self, ui_file):
    self.directory_stack.append(path.dirname(ui_file))
    (filename, extension) = path.splitext(ui_file)
    if extension == '.ui':
      widget = self.load_ui_file(ui_file)
    elif extension == '.py':
      widget = self.load_py_file(ui_file)
    else:
      raise Exception("invalid file type: {}".format(extension))
    if self.is_connected():
      self.establish_widget_connections(widget)
    self.directory_stack.pop()
    return widget

  def get_path(self, ui_file, widget):
    dirname = self.directory_stack[-1]
    full_path = path.join(dirname, str(ui_file))
    return full_path

  def open_relative(self, ui_file, widget):
    """open_relative opens a ui file with a relative path.  This is
    really only used by embedded displays."""
    full_path = self.get_path(ui_file, widget)
    return self.open_file(full_path)

  def eventFilter(self, obj, event):
    if event.type() == QEvent.MouseButtonPress:
      if event.button() == Qt.MiddleButton:
        self.show_address_tooltip(obj, event)
        return True
    return False
  
  #Not sure if showing the tooltip should be the job of the app,
  #may want to revisit this.
  def show_address_tooltip(self, obj, event):
    addr = obj.channels()[0].address
    QToolTip.showText(event.globalPos(), addr)
    #Strip the scheme out of the address before putting it in the clipboard.
    m = re.match('(.+?):/{2,3}(.+?)$',addr)
    QApplication.clipboard().setText(m.group(2), mode=QClipboard.Selection)

  def connect_to_data_channel(self, channel):
    if channel is None:
      return
    address = str(channel.address)
    if address not in self.data_emitters:
      e = DataEmitter(address, parent=self)
      e.put_value_signal.connect(self.send_msg)
      self.data_emitters[address] = e
    emitter = self.data_emitters[address]
    emitter.add_listener(channel)
    #print("Sending channel request for: {}".format(address))
    msg = ipc_protocol.ClientMessage.new_message()
    msg.channelRequest = address
    self.send_msg(msg)
 
  def establish_widget_connections(self, widget):
    widgets = [widget]
    widgets.extend(widget.findChildren(QWidget))
    for child_widget in widgets:
      if hasattr(child_widget, 'channels'):
        for channel in child_widget.channels():
          self.connect_to_data_channel(channel)
        #Take this opportunity to install a filter that intercepts middle-mouse clicks, which we use to display a tooltip with the address of the widget's first channel.
        child_widget.installEventFilter(self)
        
  def disconnect_from_data_channel(self, channel): 
    if channel is None:
      return
    address = str(channel.address)
    emitter = self.data_emitters[address]
    emitter.remove_listener(channel)
    if emitter.listener_count < 1:
      del self.data_emitters[address]
    #print("Sending channel disconnect request for: {}".format(address))
    msg = ipc_protocol.ClientMessage.new_message()
    msg.channelDisconnect = address
    self.send_msg(msg)
    
  def close_widget_connections(self, widget):
    widgets = [widget]
    widgets.extend(widget.findChildren(QWidget))
    for child_widget in widgets:
      if hasattr(child_widget, 'channels'):
        for channel in child_widget.channels():
          self.disconnect_from_data_channel(channel)

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
    #Hook this channel up to the appropriate data emitter
    if channel.connection_slot is not None:
      self.connection_state_signal.connect(channel.connection_slot)
      
    if channel.value_slot is not None:
        self.new_value_signal[int].connect(channel.value_slot)
        self.new_value_signal[float].connect(channel.value_slot)
        self.new_value_signal[str].connect(channel.value_slot)

    if channel.waveform_slot is not None:
        self.new_waveform_signal.connect(channel.waveform_slot)

    if channel.severity_slot is not None:
      self.new_severity_signal.connect(channel.severity_slot)

    if channel.write_access_slot is not None:
      self.write_access_signal.connect(channel.write_access_slot)

    if channel.enum_strings_slot is not None:
      self.enum_strings_signal.connect(channel.enum_strings_slot)

    if channel.unit_slot is not None:
      self.unit_signal.connect(channel.unit_slot)

    if channel.prec_slot is not None:
      self.prec_signal.connect(channel.prec_slot)
    
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
      if w:
        for i, v in enumerate(list(val)):
          w[i] = v
      else:
        raise Exception("Unhandled dtype for waveform put: {}".format(val.dtype))  
    self.put_value_signal.emit(msg)
      
  def remove_listener(self, channel):
    if self.listener_count < 1:
      return
    #Disconnect channel from the data emitter.  Maybe not really necessary to do this.
    if channel.connection_slot is not None:
      self.connection_state_signal.disconnect(channel.connection_slot)
      
    if channel.value_slot is not None:
        self.new_value_signal[int].disconnect(channel.value_slot)
        self.new_value_signal[float].disconnect(channel.value_slot)
        self.new_value_signal[str].disconnect(channel.value_slot)

    if channel.waveform_slot is not None:
        self.new_waveform_signal.disconnect(channel.waveform_slot)

    if channel.severity_slot is not None:
      self.new_severity_signal.disconnect(channel.severity_slot)

    if channel.write_access_slot is not None:
      self.write_access_signal.disconnect(channel.write_access_slot)

    if channel.enum_strings_slot is not None:
      self.enum_strings_signal.disconnect(channel.enum_strings_slot)

    if channel.unit_slot is not None:
      self.unit_signal.disconnect(channel.unit_slot)

    if channel.prec_slot is not None:
      self.prec_signal.disconnect(channel.prec_slot)
    self.listener_count -= 1