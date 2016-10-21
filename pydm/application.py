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
from PyQt4.QtCore import Qt, QEvent
from PyQt4.QtGui import QApplication, QColor, QWidget
from PyQt4 import uic
from .main_window import PyDMMainWindow
import re

#If the user has PSP and pyca installed, use psp, which is faster.
#Otherwise, use PyEPICS, which is slower, but more commonly used.
try:
  from .psp_plugin import PSPPlugin
  EPICSPlugin = PSPPlugin
except ImportError:
  from .pyepics_plugin import PyEPICSPlugin
  EPICSPlugin = PyEPICSPlugin  
from .fake_plugin import FakePlugin
from .archiver_plugin import ArchiverPlugin
  
class PyDMApplication(QApplication):
  plugins = { "ca": EPICSPlugin(), "fake": FakePlugin(), "archiver": ArchiverPlugin() }
  
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
  
  def __init__(self, command_line_args):
    super(PyDMApplication, self).__init__(command_line_args)
    self.directory_stack = ['']
    self.windows = {}
    #Open a window if one was provided.
    if len(command_line_args) > 1:
      ui_file = command_line_args[1]
      self.make_window(ui_file)
      self.had_file = True
    else:
      self.had_file = False
    #Re-enable sigint (usually blocked by pyqt)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

  def exec_(self):
      """
      Execute the QApplication
      """
      # Connect to top-level widgets that were not loaded from file
      # These are usually testing/debug widgets
      if not self.had_file:
        self.make_connections()
      return super(PyDMApplication,self).exec_()

  def make_connections(self):
    for widget in self.topLevelWidgets():
      self.establish_widget_connections(widget)
 
  def new_pydm_process(self, ui_file):
    subprocess.Popen('python $PYDM_PATH/pydm.py "{file}"'.format(file=ui_file), shell=True)
  
  def new_window(self, ui_file):
    """new_window() gets called whenever a request to open a new window is made."""
    (filename, extension) = path.splitext(ui_file)
    if extension == '.ui':
      self.make_window(ui_file)
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

  def plugin_for_channel(self, channel):
    match = re.match('.*://', channel.address)
    if match:
      try:
        protocol = match.group(0)[:-3]
        plugin_to_use = self.plugins[str(protocol)]
        return plugin_to_use
      except KeyError:
        print("Couldn't find plugin: {0}".format(match.group(0)[:-3]))
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
    #Strip the scheme out of the address before putting it in the clipboard.
    m = re.match('(.+?):/{2,3}(.+?)$',addr)
    QApplication.clipboard().setText(m.group(2), mode=QClipboard.Selection)
 
  def establish_widget_connections(self, widget):
    widgets = [widget]
    widgets.extend(widget.findChildren(QWidget))
    for child_widget in widgets:
      if hasattr(child_widget, 'channels'):
        for channel in child_widget.channels():
          self.add_connection(channel)
        #Take this opportunity to install a filter that intercepts middle-mouse clicks, which we use to display a tooltip with the address of the widget's first channel.
        child_widget.installEventFilter(self)

  def close_widget_connections(self, widget):
    widgets = [widget]
    widgets.extend(widget.findChildren(QWidget))
    for child_widget in widgets:
      if hasattr(child_widget, 'channels'):
        for channel in child_widget.channels():
          self.remove_connection(channel)
