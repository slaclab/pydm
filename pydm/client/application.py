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
from ..PyQt.QtCore import Qt, QObject, QTimer, QThread, QEvent, QReadLocker, pyqtSlot, pyqtSignal
from ..PyQt.QtGui import QApplication, QColor, QWidget
from ..PyQt import uic
from .main_window import PyDMMainWindow
from .message_handler import ServerConnection

class PyDMApplication(QApplication):
  new_process = pyqtSignal(str)
  connect_to_channel = pyqtSignal(str)
  disconnect_from_channel = pyqtSignal(str)
  put_to_channel = pyqtSignal(str, object)
  disconnect_from_server = pyqtSignal()
  
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
    self.setQuitOnLastWindowClosed(False)
    self.directory_stack = ['']
    self.windows = {}
    self.pydm_widgets = set()
    self._connected = False
    self.network_thread = QThread(self)
    self.server_connection = ServerConnection(servername, self.applicationPid())
    self.server_connection.server_connection_established.connect(self.make_connections)
    self.new_process.connect(self.server_connection.new_pydm_process)
    self.connect_to_channel.connect(self.server_connection.connect_to_data_channel)
    self.disconnect_from_channel.connect(self.server_connection.disconnect_from_data_channel)
    self.disconnect_from_server.connect(self.server_connection.disconnect)
    self.aboutToQuit.connect(self.server_connection.disconnect)
    self.server_connection.disconnected.connect(self.network_thread.quit)
    self.lock = self.server_connection.lock
    self.network_thread.started.connect(self.server_connection.start_connection)
    self.network_thread.finished.connect(self.network_thread.deleteLater)
    self.server_connection.moveToThread(self.network_thread)
    #Open a window if a file was provided.
    if ui_file is not None:
      self.make_window(ui_file)
      self.had_file = True
    else:
      self.had_file = False
    #Re-enable sigint (usually blocked by pyqt)
    #signal.signal(signal.SIGINT, signal.SIG_DFL)
    self.network_thread.start()
    self.update_timer = QTimer(self)
    self.update_timer.setInterval(17)
    self.update_timer.timeout.connect(self.update_widgets)
    
  def is_connected(self):
    return self._connected
      
  def exec_(self):
      """
      Execute the QApplication
      """
      # Connect to top-level widgets that were not loaded from file
      # These are usually testing/debug widgets.
      if not self.had_file:
        self.make_connections()
      return super(PyDMApplication,self).exec_()

  def exit(self, return_code=0):
    print("Application quitting")
    self.disconnect_from_server.emit()
    self.network_thread.wait()
    super(PyDMApplication, self).exit(return_code)

  @pyqtSlot()
  def make_connections(self):
    self._connected = True
    for widget in self.topLevelWidgets():
      self.establish_widget_connections(widget)
    self.update_timer.start()
  
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
    self.new_process.emit(str(ui_file))
    
  def close_window(self, window):
    print("Closing window.")
    del self.windows[window]
    if len(self.windows) < 1:
      self.disconnect_from_server.emit()
      self.network_thread.quit()
      self.network_thread.wait()
      self.quit()

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
    self.connect_to_channel.emit(address)
 
  def establish_widget_connections(self, widget):
    widgets = [widget]
    widgets.extend(widget.findChildren(QWidget))
    for child_widget in widgets:
      if hasattr(child_widget, 'channels'):
        for channel in child_widget.channels():
          self.connect_to_data_channel(channel)
        #Take this opportunity to install a filter that intercepts middle-mouse clicks, which we use to display a tooltip with the address of the widget's first channel.
        child_widget.installEventFilter(self)
        self.pydm_widgets.add(child_widget)
        
  def disconnect_from_data_channel(self, channel): 
    if channel is None:
      return
    address = str(channel.address)
    self.disconnect_from_channel.emit(address)
    
  def close_widget_connections(self, widget):
    widgets = [widget]
    widgets.extend(widget.findChildren(QWidget))
    for child_widget in widgets:
      if hasattr(child_widget, 'channels'):
        for channel in child_widget.channels():
          self.disconnect_from_data_channel(channel)
        self.pydm_widgets.remove(child_widget)
          
  @pyqtSlot()
  def update_widgets(self):
    for child_widget in self.pydm_widgets:
      for channel in child_widget.channels():
        with QReadLocker(self.lock):
          try:
            cd = self.server_connection.data_for_channel[str(channel.address)]
            child_widget.receiveValue(cd.value)
            child_widget.alarmSeverityChanged(cd.severity)
            child_widget.connectionStateChanged(cd.connection_state)
          except KeyError:
            pass
          except AttributeError:
            pass

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