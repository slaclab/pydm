"""
Data Server

Contains the PyDMDataServer class with core connection logic, and window process handling logic.
PyDM starts by launching a data server.  The data server can spawn child window processes, and communiates with them
via QLocalSocket connections (which Qt implements via a local domain socket on Unix).

The data server:
  # Recieves channel connection requests from child windows
  # Recieves channel disconnection requests from child windows
  # Recieves requests to open new windows from child windows
  # Recieves window about to close notifications from child windows
  # Recieves channel put requests from child windows.
  # Sends new channel data to child windows
"""
import os
import sys
import signal
import subprocess
import re
from ..PyQt.QtCore import Qt, QTimer, QCoreApplication, QByteArray, pyqtSlot
from ..PyQt.QtNetwork import QLocalServer
from ..widgets.channel import PyDMChannel
from .client_connection import DataClientConnection

#If the user has PSP and pyca installed, use psp, which is faster.
#Otherwise, use PyEPICS, which is slower, but more commonly used.
EPICS_LIB = os.getenv("PYDM_EPICS_LIB")
if EPICS_LIB == "pyepics":
  from ..data_plugins.pyepics_plugin import PyEPICSPlugin
  EPICSPlugin = PyEPICSPlugin
elif EPICS_LIB == "pyca":
  from ..data_plugins.psp_plugin import PSPPlugin
  EPICSPlugin = PSPPlugin
else:
  try:
    from ..data_plugins.psp_plugin import PSPPlugin
    EPICSPlugin = PSPPlugin
  except ImportError:
    from ..data_plugins.pyepics_plugin import PyEPICSPlugin
    EPICSPlugin = PyEPICSPlugin  
from ..data_plugins.fake_plugin import FakePlugin
from ..data_plugins.archiver_plugin import ArchiverPlugin

class PyDMDataServer(QCoreApplication):
  plugins = { "ca": EPICSPlugin(), "fake": FakePlugin(), "archiver": ArchiverPlugin() }
  
  def __init__(self, ui_file=None, command_line_args=[]):
    super(PyDMDataServer, self).__init__(command_line_args)
    #A dictionary of child processes, keyed on the child process' pid.
    self.child_processes = {}
    self.connections = []
    self.clients_for_channel = {}
    #Re-enable sigint (usually blocked by pyqt)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    #This regex is used to separate a protocol specifier from a channel address
    self.plugin_regex = re.compile('.*://')
    #Setup the socket server
    self.server = DataSocketServer(self)
    self.server.newConnection.connect(self.establish_local_socket_connection)
    if not self.server.listen(self.socket_name()):
      print("Local socket server could not start listening on socket named {}".format(self.socket_name()))
      print("Server error: {}".format(self.server.errorString()))
    for (protocol, plugin) in self.plugins.iteritems():
      plugin.data_message_signal.connect(self.send_data_message_to_clients)
    #Open a child window if a filename was provided.
    if ui_file is not None:
      self.spawn_window(ui_file)
    #QTimer.singleShot(10000, self.test_spawn)
      
  def socket_name(self):
    return "pydm-{}".format(self.applicationPid())    
      
  @pyqtSlot()
  def establish_local_socket_connection(self):
      conn = self.server.nextPendingConnection()
      self.connections.append(conn)
      conn.disconnected.connect(self.client_disconnected)
      conn.channelConnectRequested.connect(self.connect_to_channel)
      conn.channelDisconnectRequested.connect(self.disconnect_from_channel)
      conn.channelPutRequested.connect(self.put_value_for_channel)
      conn.newWindowRequested.connect(self.spawn_window, Qt.QueuedConnection)
      
  @pyqtSlot()
  def client_disconnected(self):
    conn = self.sender()
    for channel in conn.channels:
      self.disconnect_from_channel(channel)
    conn.channels.clear()
    self.connections.remove(conn)
    if len(self.connections) < 1:
      print("No remaining client connections, server is quitting in 1 second.")
      QTimer.singleShot(1000, self.exit)
      #self.exit(0)
  
  def exit(self, return_code=0):
    for name, plugin in self.plugins.iteritems():
      plugin.remove_all_connections()
    self.server.close()
    super(PyDMDataServer, self).exit(return_code)
  
  @pyqtSlot(object)
  def send_data_message_to_clients(self, msg):
    b = QByteArray(msg.to_bytes())
    for client in self.clients_for_channel[msg.channelName]:
      client.send_bytes(b)
      
  @pyqtSlot(str, object)
  def put_value_for_channel(self, channel, val):
    channel = str(channel)
    plugin = self.plugin_for_channel(channel)
    if plugin:
      plugin.put_value_for_channel(channel, val)
  
  @pyqtSlot()
  def test_spawn(self):
    self.spawn_window("examples/home.ui")
  
  @pyqtSlot(str)
  def spawn_window(self, ui_file):
    ui_file = str(ui_file)
    pydm_display_app_path = "pydm.py"
    if os.environ.get("PYDM_PATH") is not None:
      pydm_display_app_path = os.path.join(os.environ["PYDM_PATH"], pydm_display_app_path)
    p = subprocess.Popen([sys.executable, pydm_display_app_path, "-c", self.socket_name(), ui_file], shell=False)
    self.child_processes[p.pid] = p
  
  def close_child_process(self, pid):
    self.child_processes[pid].terminate()
    del self.child_processes[pid]

  def plugin_for_channel(self, channel):
    match = self.plugin_regex.match(channel)
    if match:
      try:
        protocol = match.group(0)[:-3]
        plugin_to_use = self.plugins[str(protocol)]
        return plugin_to_use
      except KeyError:
        print("Couldn't find plugin: {0}".format(match.group(0)[:-3]))
    return None
  
  @pyqtSlot(str)
  def connect_to_channel(self, channel):
    channel = str(channel)
    client = self.sender()
    plugin = self.plugin_for_channel(channel)
    if plugin:
      plugin.add_connection(channel)
      if channel in self.clients_for_channel:
        self.clients_for_channel[channel].add(client)
      else:
        self.clients_for_channel[channel] = set([client])
      client.channels.add(channel)
  
  @pyqtSlot(str)
  def disconnect_from_channel(self, channel):
    channel = str(channel)
    client = self.sender()
    plugin = self.plugin_for_channel(channel)
    if plugin:
      plugin.remove_connection(channel)
      self.clients_for_channel[channel].remove(client)

class DataSocketServer(QLocalServer):
  def __init__(self, parent=None):
    super(DataSocketServer, self).__init__(parent)
    self.pending_connections = []
        
  def incomingConnection(self, socketDescriptor):
    conn = DataClientConnection(self)
    conn.setSocketDescriptor(socketDescriptor)
    if len(self.pending_connections) < self.maxPendingConnections():
      self.pending_connections.append(conn)
      self.newConnection.emit()
  
  def hasPendingConnections(self):
    return len(self.pending_connections)>0
  
  def nextPendingConnection(self):
    if not self.hasPendingConnections():
      return None
    return self.pending_connections.pop(0)
    
