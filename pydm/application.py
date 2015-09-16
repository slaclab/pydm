from PyQt4.QtGui import QApplication, QMainWindow, QColor, QWidget
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
    self.ui.homeButton.clicked.connect(self.clear_display_widget) #Just for debug purposes.
    
  def set_display_widget(self, new_widget):
    if new_widget == self._display_widget:
      return
    self.clear_display_widget()
    self._display_widget = new_widget
    self.ui.verticalLayout.addWidget(self._display_widget)
    self.setWindowTitle(self._display_widget.windowTitle() + " - PyDM")
    self.establish_widget_connections(self._display_widget)
    
  def clear_display_widget(self):
    if self._display_widget != None:
      self.ui.verticalLayout.removeWidget(self._display_widget)
      self.close_widget_connections(self._display_widget)
      self._display_widget = None
      
  def establish_widget_connections(self, widget):
    for child_widget in widget.findChildren(QWidget):
      if hasattr(child_widget, 'channels'):
        for channel in child_widget.channels():
          QApplication.instance().add_connection(channel)
  
  def close_widget_connections(self, widget):
    for child_widget in widget.findChildren(QWidget):
      if hasattr(child_widget, 'channels'):
        for channel in child_widget.channels():
          QApplication.instance().remove_connection(channel)
      
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
    self.windows = []
    try:
      main_window = PyDMMainWindow()
      self.windows.append(main_window)
      ui_file = command_line_args[1]
      (filename, extension) = path.splitext(ui_file)
      if extension == '.ui':
        self.load_ui_file(ui_file, main_window)
      elif extension == '.py':
        self.load_py_file(ui_file, main_window)
      main_window.show()
    except IndexError:
      #This must be an old-style, stand-alone PyDMApplication.  Do nothing!
      pass
  
  def load_ui_file(self, uifile, target_window):
    display_widget = uic.loadUi(uifile)
    target_window.set_display_widget(display_widget)
    
  def load_py_file(self, pyfile, target_window):
    #Add the intelligence module directory to the python path, so that submodules can be loaded.  Eventually, this should go away, and intelligence modules should behave as real python modules.
    module_dir = path.dirname(path.abspath(pyfile))
    sys.path.append(module_dir)

    #Now load the intelligence module.
    module = imp.load_source('intelclass', pyfile)
    intelligence_instance = module.intelclass(target_window)
    target_window.set_display_widget(intelligence_instance.ui())
  
  def plugin_for_channel(self, channel):
    match = re.match('.*://', channel.address)
    if match:
      try:
        protocol = match.group(0)[:-3]
        plugin_to_use = self.plugins[str(protocol)]
        return plugin_to_use
      except KeyError:
        print "Couldn't find plugin: {0}".format(match.group(0)[:-3])
    return None
  
  def add_connection(self, channel):
    plugin = self.plugin_for_channel(channel)
    if plugin:
      plugin.add_connection(channel)
        
  def remove_connection(self, channel):
    plugin = self.plugin_for_channel(channel)
    if plugin:
      plugin.remove_connection(channel)
    
