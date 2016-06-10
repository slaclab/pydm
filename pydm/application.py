from PyQt4.QtGui import QApplication, QMainWindow, QColor, QWidget, QToolTip, QClipboard
from PyQt4.QtCore import Qt, pyqtSlot, QTimer, QEvent
import re
from .epics_plugin import EPICSPlugin
from .fake_plugin import FakePlugin
from .archiver_plugin import ArchiverPlugin
from .pydm_ui import Ui_MainWindow
from PyQt4 import uic
from os import path, environ
import imp
import sys
import subprocess
import platform

class PyDMMainWindow(QMainWindow):
  def __init__(self, parent=None):
    super(PyDMMainWindow, self).__init__(parent)
    self.ui = Ui_MainWindow()
    self.ui.setupUi(self)
    self._display_widget = None
    self.ui.homeButton.clicked.connect(self.home)
    self.home_file = 'examples/home.ui'
    self.back_stack = []
    self.forward_stack = []
    self.ui.backButton.clicked.connect(self.back)
    self.ui.forwardButton.clicked.connect(self.forward)
    self.ui.goButton.clicked.connect(self.go_button_pressed)
    self.ui.actionEdit_in_Designer.triggered.connect(self.edit_in_designer)
    self.ui.actionReload_Display.triggered.connect(self.reload_display)
    self.ui.actionIncrease_Font_Size.triggered.connect(self.increase_font_size)
    self.ui.actionDecrease_Font_Size.triggered.connect(self.decrease_font_size)
    self.designer_path = None
    if environ.get('QTHOME') == None:
      self.ui.actionEdit_in_Designer.setEnabled(False)
    else:
      qt_path = environ.get('QTHOME')
      if platform.system() == 'Darwin':
        #On OS X we have to launch designer in this ugly way if we want it to get access to environment variables.  Ugh.
        self.designer_path = path.join(qt_path, 'Designer.app/Contents/MacOS/Designer')
      else:
        #This assumes some non-OS X unix.  No windows support right now.
        self.designer_path = path.join(qt_path, 'bin/designer')
    
  def set_display_widget(self, new_widget):
    if new_widget == self._display_widget:
      return
    self.clear_display_widget()
    self._display_widget = new_widget
    self.ui.verticalLayout.addWidget(self._display_widget)
    self.setWindowTitle(self._display_widget.windowTitle() + " - PyDM")
    self.establish_widget_connections(self._display_widget)
    QTimer.singleShot(0, self.resizeToMinimum)
    
    
  def clear_display_widget(self):
    if self._display_widget != None:
      self.ui.verticalLayout.removeWidget(self._display_widget)
      self.close_widget_connections(self._display_widget)
      self._display_widget.deleteLater()
      self._display_widget = None
  
  def load_ui_file(self, uifile):
    display_widget = uic.loadUi(uifile)
    self.set_display_widget(display_widget)
    
  def load_py_file(self, pyfile):
    #Add the intelligence module directory to the python path, so that submodules can be loaded.  Eventually, this should go away, and intelligence modules should behave as real python modules.
    module_dir = path.dirname(path.abspath(pyfile))
    sys.path.append(module_dir)

    #Now load the intelligence module.
    module = imp.load_source('intelclass', pyfile)
    intelligence_instance = module.intelclass(self)
    self.set_display_widget(intelligence_instance)

  def eventFilter(self, obj, event):
    if event.type() == QEvent.MouseButtonPress:
      if event.button() == Qt.MiddleButton:
        self.show_address_tooltip(obj, event)
        return True
    return False

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
          QApplication.instance().add_connection(channel)
        #Take this opportunity to install a filter that intercepts middle-mouse clicks, which we use to display a tooltip with the address of the widget's first channel.
        child_widget.installEventFilter(self)
  
  def close_widget_connections(self, widget):
    widgets = [widget]
    widgets.extend(widget.findChildren(QWidget))
    for child_widget in widgets:
      if hasattr(child_widget, 'channels'):
        for channel in child_widget.channels():
          QApplication.instance().remove_connection(channel)
  
  def open_file(self, ui_file):
    (filename, extension) = path.splitext(ui_file)
    if extension == '.ui':
      self.load_ui_file(ui_file)
    elif extension == '.py':
      self.load_py_file(ui_file)
    if (len(self.back_stack) == 0) or (self.current_file() != ui_file):
      self.back_stack.append(ui_file)
    self.ui.forwardButton.setEnabled(len(self.forward_stack) > 0)
    self.ui.backButton.setEnabled(len(self.back_stack) > 1)
  
  def go_button_pressed(self):
    filename = str(self.ui.panelSearchLineEdit.text())
    if QApplication.keyboardModifiers() == Qt.ShiftModifier:
      QApplication.instance().new_window(filename)
    else:
      self.go(filename)
  
  #Note: in go(), back(), and forward(), always do history stack manipulation *before* opening the file.
  #That way, the navigation button enable/disable state will work correctly.  This is stupid, and will be fixed eventually.
  def go(self, ui_file):
    self.forward_stack = []
    self.open_file(ui_file)
    
  def back(self):
    if len(self.back_stack) > 1:
      if QApplication.keyboardModifiers() == Qt.ShiftModifier:
        QApplication.instance().new_window(self.back_stack[-2])
      else:
        self.forward_stack.append(self.back_stack.pop())
        self.open_file(self.back_stack[-1])
  
  def forward(self):
    if len(self.forward_stack) > 0:
      if QApplication.keyboardModifiers() == Qt.ShiftModifier:
        QApplication.instance().new_window(self.forward_stack[-1])
      else:
        self.open_file(self.forward_stack.pop())
  
  def home(self):
    if QApplication.keyboardModifiers() == Qt.ShiftModifier:
      QApplication.instance().new_window(self.home_file)
    else:
      self.go(self.home_file)
  
  def current_file(self):
    if len(self.back_stack) == 0:
      raise IndexError("The display manager does not have a display loaded.")
    return self.back_stack[-1]
      
  @pyqtSlot(bool)
  def edit_in_designer(self, checked):
    if not self.designer_path:
      return
    filename, extension = path.splitext(self.current_file())
    if extension == '.ui':
      process = subprocess.Popen('{0} "{1}"'.format(self.designer_path, self.current_file()), shell=True)
      self.statusBar().showMessage("Launching '{0}' in Qt Designer...".format(self.current_file()), 5000)
    else:
      self.statusBar().showMessage("{0} is a Python file, and cannot be edited in Qt Designer.".format(self.current_file()), 5000)
  
  @pyqtSlot(bool)
  def reload_display(self, checked):
    self.statusBar().showMessage("Reloading '{0}'...".format(self.current_file()), 5000)
    self.go(self.current_file())
  
  @pyqtSlot(bool)
  def increase_font_size(self, checked):
    current_font = QApplication.instance().font()
    current_font.setPointSizeF(current_font.pointSizeF() * 1.1)
    QApplication.instance().setFont(current_font)
    QTimer.singleShot(0, self.resizeToMinimum)
  
  @pyqtSlot(bool)
  def decrease_font_size(self, checked):
    current_font = QApplication.instance().font()
    current_font.setPointSizeF(current_font.pointSizeF() / 1.1)
    QApplication.instance().setFont(current_font)
    QTimer.singleShot(0, self.resizeToMinimum)
  
  def resizeToMinimum(self):
    self.resize(self.minimumSizeHint())
  
  def closeEvent(self, event):
    self.clear_display_widget()
    
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
    True: QColor(0, 0, 0,)
  }
  
  def __init__(self, command_line_args):
    super(PyDMApplication, self).__init__(command_line_args)
    #Add the path to the widgets module, so that qt knows where to find custom widgets.  This seems like a really awful way to do this.
    sys.path.append(path.join(path.dirname(path.realpath(__file__)), 'widgets'))
    self.windows = []
    ui_file = None
    try:
      ui_file = command_line_args[1]
    except IndexError:
      #This must be an old-style, stand-alone PyDMApplication.  Do nothing!
      pass
    if ui_file:  
      self.new_window(ui_file)
  
  def new_window(self, ui_file):
    main_window = PyDMMainWindow()  
    self.windows.append(main_window)
    main_window.open_file(ui_file)
    main_window.show()
    #If we are launching a new window, we don't want it to sit right on top of an existing window.
    if len(self.windows) > 1:
      main_window.move(main_window.x() + 10, main_window.y() + 10)
      
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
    
