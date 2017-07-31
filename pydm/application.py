"""
Main Application Module

Contains our PyDMApplication class with core connection and loading logic and
our PyDMMainWindow class with navigation logic.
"""
import os
import imp
import sys
import signal
import subprocess
import re
import shlex
import psutil
import json
import inspect
import warnings
from .display_module import Display
from .PyQt.QtCore import Qt, QEvent, QTimer, pyqtSlot
from .PyQt.QtGui import QApplication, QColor, QWidget, QToolTip, QClipboard
from .PyQt import uic
from .main_window import PyDMMainWindow
from .utilities import macro
from . import data_plugins

DEFAULT_PROTOCOL = os.getenv("PYDM_DEFAULT_PROTOCOL")
if DEFAULT_PROTOCOL is not None:
  #Get rid of the "://" part if it exists
  DEFAULT_PROTOCOL = DEFAULT_PROTOCOL.split("://")[0]
  
class PyDMApplication(QApplication):
  #Instantiate our plugins.
  plugins = {plugin.protocol: plugin() for plugin in data_plugins.plugin_modules}
  
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
  
  def __init__(self, ui_file=None, command_line_args=[], display_args=[], perfmon=False, macros=None):
    super(PyDMApplication, self).__init__(command_line_args)
    self.directory_stack = ['']
    self.windows = {}
    self.display_args = display_args
    #Open a window if one was provided.
    if ui_file is not None:
      self.make_window(ui_file, macros, command_line_args)
      self.had_file = True
    else:
      self.had_file = False
    #Re-enable sigint (usually blocked by pyqt)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    #Performance monitoring
    if perfmon:
      self.perf = psutil.Process()
      self.perf_timer = QTimer()
      self.perf_timer.setInterval(2000)
      self.perf_timer.timeout.connect(self.get_CPU_usage)
      self.perf_timer.start()

  def exec_(self):
      """
      Execute the QApplication
      """
      # Connect to top-level widgets that were not loaded from file
      # These are usually testing/debug widgets
      if not self.had_file:
        self.make_connections()
      return super(PyDMApplication,self).exec_()


  @pyqtSlot()
  def get_CPU_usage(self):
    with self.perf.oneshot():
        total_percent = self.perf.cpu_percent(interval=None)
        total_time = sum(self.perf.cpu_times())
        usage = [total_percent * ((t.system_time + t.user_time)/total_time) for t in self.perf.threads()]
    print("Total: {tot}, Per Thread: {percpu}".format(tot=total_percent, percpu=usage))

  def make_connections(self):
    for widget in self.topLevelWidgets():
      self.establish_widget_connections(widget)
 
  def new_pydm_process(self, ui_file, macros=None, command_line_args=None):
    path_and_args = shlex.split(str(ui_file))
    filepath = path_and_args[0]
    filepath_args = path_and_args[1:]
    pydm_display_app_path = "pydm.py"
    if os.environ.get("PYDM_PATH") is not None:
      pydm_display_app_path = os.path.join(os.environ["PYDM_PATH"], pydm_display_app_path)
    args = [sys.executable, pydm_display_app_path]
    if macros is not None:
      args.extend(["-m", json.dumps(macros)])
    args.append(filepath)
    args.extend(self.display_args)
    args.extend(filepath_args)
    subprocess.Popen(args, shell=False)
  
  def new_window(self, ui_file, macros=None, command_line_args=None):
    """new_window() gets called whenever a request to open a new window is made."""
    # All new windows are spawned as new processes.
    self.new_pydm_process(ui_file, macros, command_line_args)
  
  def make_window(self, ui_file, macros=None, command_line_args=None):
    """make_window instantiates a new PyDMMainWindow, adds it to the
    application's list of windows, and opens ui_file in the window."""
    main_window = PyDMMainWindow()
    main_window.open_file(ui_file, macros, command_line_args)
    main_window.show()
    self.windows[main_window] = os.path.dirname(ui_file)
    #If we are launching a new window, we don't want it to sit right on top of an existing window.
    if len(self.windows) > 1:
      main_window.move(main_window.x() + 10, main_window.y() + 10)

  def close_window(self, window):
    del self.windows[window]

  def load_ui_file(self, uifile, macros=None):
    if macros is not None:
      f = macro.substitute_in_file(uifile, macros)
    else:
      f = uifile
    return uic.loadUi(f)
    
  def load_py_file(self, pyfile, args=None):
    #Add the intelligence module directory to the python path, so that submodules can be loaded.  Eventually, this should go away, and intelligence modules should behave as real python modules.
    module_dir = os.path.dirname(os.path.abspath(pyfile))
    sys.path.append(module_dir)

    #Now load the intelligence module.
    module = imp.load_source('intelclass', pyfile)
    if hasattr(module, 'intelclass'):
      cls = module.intelclass
      if not issubclass(cls, Display):
        raise ValueError("Invalid class definition at file {}. {} does not inherit from Display. Nothing to open at this time.".format(pyfile, cls.__name__))
    else:
      classes = [obj for name, obj in inspect.getmembers(module) if inspect.isclass(obj) and issubclass(obj, Display) and obj != Display]
      if len(classes) == 0:
        raise ValueError("Invalid File Format. {} has no class inheriting from Display. Nothing to open at this time.".format(pyfile))
      if len(classes) > 1:
        warnings.warn("More than one Display class in file {}. The first occurence (in alphabetical order) will be opened: {}".format(pyfile, classes[0].__name__), RuntimeWarning, stacklevel=2)
      cls = classes[0]

    try:
      #This only works in python 3 and up.
      module_params = inspect.signature(cls).parameters
    except AttributeError:
      #Works in python 2, deprecated in 3.0 and up.
      module_params = inspect.getargspec(cls.__init__).args

    if 'args' in module_params:
      return cls(args=args)
    else:
      return cls()

  def open_file(self, ui_file, macros=None, command_line_args=[]):
    #First split the ui_file string into a filepath and arguments
    args = command_line_args
    split = shlex.split(ui_file)
    filepath = split[0]
    args.extend(split[1:])
    self.directory_stack.append(os.path.dirname(filepath))
    (filename, extension) = os.path.splitext(filepath)
    if extension == '.ui':
      widget = self.load_ui_file(filepath, macros)
    elif extension == '.py':
      widget = self.load_py_file(filepath, args)
    else:
      self.directory_stack.pop()
      raise ValueError("invalid file type: {}".format(extension))
    self.establish_widget_connections(widget)
    self.directory_stack.pop()
    return widget

  #get_path gives you the path to ui_file relative to where you are running pydm from.
  #Many widgets handle file paths (related display, embedded display, and drawing image come to mind)
  #and the standard is that they expect paths to be given relative to the .ui or .py file in which the
  #widget lives.  But, python and Qt want the file path relative to the directory you are running
  #pydm from.  This function does that translation.
  def get_path(self, ui_file):
    dirname = self.directory_stack[-1]
    full_path = os.path.join(dirname, str(ui_file))
    return full_path

  def open_relative(self, ui_file, widget, macros=None, command_line_args=[]):
    """open_relative opens a ui file with a relative path.  This is
    really only used by embedded displays."""
    full_path = self.get_path(ui_file)
    return self.open_file(full_path, macros=macros, command_line_args=command_line_args)

  def initialize_plugins(self):
    module = imp.load_source('intelclass', pyfile)
    if hasattr(module, 'intelclass'):
      cls = module.intelclass
      if not issubclass(cls, Display):
        raise ValueError("Invalid class definition at file {}. {} does not inherit from Display. Nothing to open at this time.".format(pyfile, cls.__name__))
    else:
      classes = [obj for name, obj in inspect.getmembers(module) if inspect.isclass(obj) and issubclass(obj, Display) and obj != Display]
      if len(classes) == 0:
        raise ValueError("Invalid File Format. {} has no class inheriting from Display. Nothing to open at this time.".format(pyfile))
      if len(classes) > 1:
        warnings.warn("More than one Display class in file {}. The first occurence (in alphabetical order) will be opened: {}".format(pyfile, classes[0].__name__), RuntimeWarning, stacklevel=2)
      cls = classes[0]

  def plugin_for_channel(self, channel):
    if channel.address is None or channel.address == "":
      return None
    match = re.match('.*://', channel.address)
    if match:
      protocol = match.group(0)[:-3]
    elif DEFAULT_PROTOCOL is not None:
      #If no protocol was specified, and the default protocol environment variable is specified, try to use that instead.
      protocol = DEFAULT_PROTOCOL
    try:
      plugin_to_use = self.plugins[str(protocol)]
      return plugin_to_use
    except KeyError:
      print("Couldn't find plugin for protocol: {0}".format(match.group(0)[:-3]))
    warnings.warn("Channel {addr} did not specify a valid protocol and no default protocol is defined.  This channel will receive no data.  To specify a default protocol, set the PYDM_DEFAULT_PROTOCOL environment variable.", RuntimeWarning, stacklevel=2)
    return None
  
  def add_connection(self, channel):
    plugin = self.plugin_for_channel(channel)
    if plugin:
      plugin.add_connection(channel)
        
  def remove_connection(self, channel):
    plugin = self.plugin_for_channel(channel)
    if plugin:
      plugin.remove_connection(channel)

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
    #If the address has a protocol, and it is the default protocol, strip it out before putting it on the clipboard.
    m = re.match('(.+?):/{2,3}(.+?)$',addr)
    if m is not None and DEFAULT_PROTOCOL is not None and m.group(1) == DEFAULT_PROTOCOL:
      QApplication.clipboard().setText(m.group(2), mode=QClipboard.Selection)
    else:
      QApplication.clipboard().setText(addr, mode=QClipboard.Selection)
 
  def establish_widget_connections(self, widget):
    widgets = [widget]
    widgets.extend(widget.findChildren(QWidget))
    for child_widget in widgets:
      try:
        if hasattr(child_widget, 'channels'):
          for channel in child_widget.channels():
            self.add_connection(channel)
          # Take this opportunity to install a filter that intercepts middle-mouse clicks, 
          # which we use to display a tooltip with the address of the widget's first channel.
          child_widget.installEventFilter(self)
      except NameError:
        pass
      
  def close_widget_connections(self, widget):
    widgets = [widget]
    widgets.extend(widget.findChildren(QWidget))
    for child_widget in widgets:
      try:
          if hasattr(child_widget, 'channels'):
            for channel in child_widget.channels():
              self.remove_connection(channel)
      except NameError:
          pass
