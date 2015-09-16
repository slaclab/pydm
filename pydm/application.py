from PyQt4.QtGui import QApplication, QMainWindow, QColor
import re
from .epics_plugin import EPICSPlugin
from .fake_plugin import FakePlugin
from .archiver_plugin import ArchiverPlugin
from .pydm_ui import Ui_MainWindow
from PyQt4 import uic
from os import path
import imp
import sys

class PyDMMainWindow(QMainWindow):
  def __init__(self, parent=None):
    super(PyDMMainWindow, self).__init__(parent)
    self.ui = Ui_MainWindow()
    self.ui.setupUi(self)
    self._display_widget = None
    
  def set_display_widget(self, new_widget):
    if new_widget == self._display_widget:
      return
    if self._display_widget != None:
      self.ui.verticalLayout.removeWidget(self._display_widget)
    self._display_widget = new_widget
    self.ui.verticalLayout.addWidget(self._display_widget)
    self.setWindowTitle(self._display_widget.windowTitle() + " - PyDM")
      
class PyDMApplication(QApplication):
  plugins = { "ca": EPICSPlugin(), "fake": FakePlugin(), "archiver": ArchiverPlugin() }
  
  #HACK. To be replaced with some stylesheet stuff eventually.
  alarm_severity_color_map = {
    0: QColor(0, 0, 0), #NO_ALARM
    1: QColor(200, 200, 20), #MINOR_ALARM
    2: QColor(240, 0, 0), #MAJOR_ALARM
    3: QColor(240, 0, 240) #INVALID_ALARM
  }
  
  #HACK. To be replaced with some stylesheet stuff eventually.
  connection_status_color_map = {
    False: QColor(255, 255, 255),
    True: QColor(0, 0, 0,)
  }
  
  def __init__(self, command_line_args):
    super(PyDMApplication, self).__init__(command_line_args)
    #Add the path to the widgets module, so that qt knows where to find custom widgets.  This seems like a really awful way to do this.
    sys.path.append(path.join(path.dirname(path.realpath(__file__)), 'widgets'))
    
    try:
      self.main_window = PyDMMainWindow()
      ui_file = command_line_args[1]
      (filename, extension) = path.splitext(ui_file)
      if extension == '.ui':
        self.load_ui_file(ui_file)
      elif extension == '.py':
        self.load_py_file(ui_file)
    except IndexError:
      #This must be an old-style, stand-alone PyDMApplication.  Do nothing!
      pass
  
  def load_ui_file(self, uifile):
    display_widget = uic.loadUi(uifile)
    self.main_window.set_display_widget(display_widget)
    
  def load_py_file(self, pyfile):
    #Add the intelligence module directory to the python path, so that submodules can be loaded.  Eventually, this should go away, and intelligence modules should behave as real python modules.
    module_dir = path.dirname(path.abspath(pyfile))
    sys.path.append(module_dir)

    #Now load the intelligence module.
    module = imp.load_source('intelclass', pyfile)
    intelligence_instance = module.intelclass(self.main_window)
    self.main_window.set_display_widget(intelligence_instance.ui())
    self.start_connections()
  
  def start_connections(self):
    for widget in self.allWidgets():
      if hasattr(widget, 'channels'):
        for channel in widget.channels():
          self.add_connection(channel)
  
  def add_connection(self, channel):
    match = re.match('.*://', channel.address)
    if match:
      try:
        protocol = match.group(0)[:-3]
        plugin_to_use = self.plugins[str(protocol)]
        plugin_to_use.add_connection(channel)
      except KeyError:
        print "Couldn't find plugin: {0}".format(match.group(0)[:-3])
