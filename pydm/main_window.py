import os
from os import path, environ
from .PyQt.QtGui import QApplication, QMainWindow, QFileDialog, QWidget
from .PyQt.QtCore import Qt, QTimer, pyqtSlot, QSize
from .utilities import IconFont
from .pydm_ui import Ui_MainWindow
import subprocess
import platform

class PyDMMainWindow(QMainWindow):
    def __init__(self, parent=None, hide_nav_bar=False):
        super(PyDMMainWindow, self).__init__(parent)
        self.app = QApplication.instance()
        self.iconFont = IconFont()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._display_widget = None
        self._showing_file_path_in_title_bar = False
        self.ui.navbar.setIconSize(QSize(24,24))
        self.ui.navbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setMinimumWidth(300)
        #No search bar for now, since there isn't really any capability to search yet.
        #self.searchBar = QLineEdit(self)
        #self.searchBar.setPlaceholderText("Search")
        #self.searchBar.setMinimumWidth(150)
        #self.searchAction = self.ui.navbar.insertWidget(self.ui.actionHome, self.searchBar)
        self.ui.actionHome.triggered.connect(self.home)
        self.ui.actionHome.setIcon(self.iconFont.icon("home"))
        self.home_file = None
        self.back_stack = []
        self.forward_stack = []
        self.ui.actionBack.triggered.connect(self.back)
        self.ui.actionBack.setIcon(self.iconFont.icon("angle-left"))
        self.ui.actionForward.triggered.connect(self.forward)
        self.ui.actionForward.setIcon(self.iconFont.icon("angle-right"))
        #self.ui.goButton.clicked.connect(self.go_button_pressed)
        self.ui.actionEdit_in_Designer.triggered.connect(self.edit_in_designer)
        self.ui.actionOpen_File.triggered.connect(self.open_file_action)
        self.ui.actionReload_Display.triggered.connect(self.reload_display)
        self.ui.actionIncrease_Font_Size.triggered.connect(self.increase_font_size)
        self.ui.actionDecrease_Font_Size.triggered.connect(self.decrease_font_size)
        self.ui.actionShow_File_Path_in_Title_Bar.triggered.connect(self.toggle_file_path_in_title_bar)
        self.ui.actionShow_Navigation_Bar.triggered.connect(self.toggle_nav_bar)
        if hide_nav_bar:
            self.toggle_nav_bar(False)
        self.designer_path = None
        if environ.get('QTHOME') is None:
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
        if not new_widget.layout():
            new_widget.setMinimumSize(new_widget.size())
        self._display_widget = new_widget
        self.setCentralWidget(self._display_widget)
        self.update_window_title()
        QTimer.singleShot(0, self.resizeToMinimum)
        
    def clear_display_widget(self):
        if self._display_widget is not None:
            self.setCentralWidget(QWidget())
            self.app.close_widget_connections(self._display_widget)
            self._display_widget.deleteLater()
            self._display_widget = None
    
    def join_to_current_file_path(self, ui_file):
        ui_file = str(ui_file)
        if path.isabs(ui_file) or len(self.back_stack) == 0:
            return str(ui_file)
        else:
            return path.join(path.dirname(self.current_file()), ui_file)
    
    def open_file(self, ui_file, macros=None, command_line_args=None):
        filename = self.join_to_current_file_path(ui_file)
        self.open_abs_file(filename, macros, command_line_args)
    
    def open_abs_file(self, filename, macros=None, command_line_args=None):
        if command_line_args is None:
            command_line_args = []
        merged_macros = self.merge_with_current_macros(macros)
        widget = self.app.open_file(filename, merged_macros, command_line_args)
        if (len(self.back_stack) == 0) or (self.current_file() != filename):
            self.back_stack.append((filename, merged_macros, command_line_args))
        self.set_display_widget(widget)
        self.ui.actionForward.setEnabled(len(self.forward_stack) > 0)
        self.ui.actionBack.setEnabled(len(self.back_stack) > 1)
        if self.home_file is None:
            self.home_file = (filename, merged_macros, command_line_args)
            
    def new_window(self, ui_file, macros=None, command_line_args=None):
        filename = self.join_to_current_file_path(ui_file)
        self.new_abs_window(filename, macros, command_line_args)
    
    def new_abs_window(self, filename, macros=None, command_line_args=None):
        merged_macros = self.merge_with_current_macros(macros)
        self.app.new_window(filename, merged_macros, command_line_args)
    
    def go_button_pressed(self):
        filename = str(self.ui.panelSearchLineEdit.text())
        if not filename:
            return
        try:
            if QApplication.keyboardModifiers() == Qt.ShiftModifier:
                self.app.new_window(filename)
            else:
                self.go(filename)
        except (IOError, OSError, ValueError, ImportError) as e:
            self.handle_open_file_error(filename, e)
    
    def handle_open_file_error(self, filename, error):
        self.statusBar().showMessage("Cannot open file: '{0}', reason: '{1}'...".format(filename, error), 5000)

    #Note: in go(), back(), and forward(), always do history stack manipulation *before* opening the file.
    #That way, the navigation button enable/disable state will work correctly.  This is stupid, and will be fixed eventually.
    def go(self, ui_file, macros=None, command_line_args=None):
        self.forward_stack = []
        self.open_file(ui_file, macros, command_line_args)
    
    def go_abs(self, ui_file, macros=None, command_line_args=None):
        self.forward_stack = []
        self.open_abs_file(filename=ui_file, macros=macros, command_line_args=command_line_args)
        
    def back(self):
        if len(self.back_stack) > 1:
            if QApplication.keyboardModifiers() == Qt.ShiftModifier:
                stack_item = self.back_stack[-2]
                self.new_abs_window(filename=stack_item[0], macros=stack_item[1], command_line_args=stack_item[2])
            else:
                self.forward_stack.append(self.back_stack.pop())
                stack_item = self.back_stack[-1]
                self.open_abs_file(filename=stack_item[0], macros=stack_item[1], command_line_args=stack_item[2])
    
    def forward(self):
        if len(self.forward_stack) > 0:
            if QApplication.keyboardModifiers() == Qt.ShiftModifier:
                stack_item = self.forward_stack[-1]
                self.new_abs_window(filename=stack_item[0], macros=stack_item[1], command_line_args=stack_item[2])
            else:
                stack_item = self.forward_stack.pop()
                self.open_abs_file(filename=stack_item[0], macros=stack_item[1], command_line_args=stack_item[2])
    
    def home(self):
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            self.new_abs_window(filename=self.home_file[0], macros=self.home_file[1], command_line_args=self.home_file[2])
        else:
            self.go_abs(self.home_file[0], macros=self.home_file[1], command_line_args=self.home_file[2])
    
    def current_stack_item(self):
        if len(self.back_stack) == 0:
            raise IndexError("The display manager does not have a display loaded.")
        return self.back_stack[-1]
    
    def current_file(self):
        return self.current_stack_item()[0]
    
    def current_macros(self):
        try:
            return self.current_stack_item()[1]
        except IndexError:
            return None
    
    def current_args(self):
        try:
            return self.current_stack_item()[2]
        except IndexError:
            return None
    
    def merge_with_current_macros(self, macros_to_merge):
        if self.current_macros() is None:
            return macros_to_merge
        if macros_to_merge is None:
            return self.current_macros()
        m = self.current_macros().copy()
        m.update(macros_to_merge)
        return m
    
    def update_window_title(self):
        if self.showing_file_path_in_title_bar:
            self.setWindowTitle(self.current_file() + " - PyDM")
        else:
            self.setWindowTitle(self._display_widget.windowTitle() + " - PyDM")
    
    @property
    def showing_file_path_in_title_bar(self):
        return self._showing_file_path_in_title_bar
    
    @showing_file_path_in_title_bar.setter
    def showing_file_path_in_title_bar(self, checked):
        self._showing_file_path_in_title_bar = checked
        self.update_window_title()
    
    @pyqtSlot(bool)
    def toggle_file_path_in_title_bar(self, checked):
        self.showing_file_path_in_title_bar = checked
    
    @pyqtSlot(bool)
    def toggle_nav_bar(self, checked):
        self.ui.navbar.setHidden(not checked)
            
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
    def open_file_action(self, checked):
        modifiers = QApplication.keyboardModifiers()
        filename = QFileDialog.getOpenFileName(self, 'Open File...', os.path.dirname(self.current_file()), 'PyDM Display Files (*.ui *.py)')
        filename = filename[0] if isinstance(filename, (list, tuple)) else filename

        if filename:
            filename = str(filename)
            try:
                if modifiers == Qt.ShiftModifier:
                    self.app.new_window(filename)
                else:
                    self.open_file(filename)
            except (IOError, OSError, ValueError, ImportError) as e:
                self.handle_open_file_error(filename, e)

    @pyqtSlot(bool)
    def reload_display(self, checked):
        self.statusBar().showMessage("Reloading '{0}'...".format(self.current_file()), 5000)
        self.go_abs(self.current_file())
    
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
        self.app.close_window(self)
