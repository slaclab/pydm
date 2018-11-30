import os
from os import path
from qtpy.QtWidgets import QApplication, QMainWindow, QFileDialog, QWidget, QAction
from qtpy.QtCore import Qt, QTimer, Slot, QSize, QLibraryInfo
from .utilities import IconFont, find_display_in_path
from .pydm_ui import Ui_MainWindow
from .display_module import Display
from .connection_inspector import ConnectionInspector
from .about_pydm import AboutWindow
from .widgets import rules
from . import data_plugins
from . import tools
import subprocess
import platform
import logging

logger = logging.getLogger(__name__)


class PyDMMainWindow(QMainWindow):

    def __init__(self, parent=None, hide_nav_bar=False, hide_menu_bar=False, hide_status_bar=False):
        super(PyDMMainWindow, self).__init__(parent)
        self.app = QApplication.instance()
        self.iconFont = IconFont()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._display_widget = None
        self._showing_file_path_in_title_bar = False
        self.default_font_size = QApplication.instance().font().pointSizeF()
        self.ui.navbar.setIconSize(QSize(24, 24))
        self.ui.navbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        # No search bar for now, since there isn't really any capability to search yet.
        # self.searchBar = QLineEdit(self)
        # self.searchBar.setPlaceholderText("Search")
        # self.searchBar.setMinimumWidth(150)
        # self.searchAction = self.ui.navbar.insertWidget(self.ui.actionHome, self.searchBar)
        self.ui.actionHome.triggered.connect(self.home)
        self.ui.actionHome.setIcon(self.iconFont.icon("home"))
        self.home_file = None
        self.back_stack = []
        self.forward_stack = []
        self.ui.actionBack.triggered.connect(self.back)
        self.ui.actionBack.setIcon(self.iconFont.icon("angle-left"))
        self.ui.actionForward.triggered.connect(self.forward)
        self.ui.actionForward.setIcon(self.iconFont.icon("angle-right"))
        # self.ui.goButton.clicked.connect(self.go_button_pressed)
        self.ui.actionEdit_in_Designer.triggered.connect(self.edit_in_designer)
        self.ui.actionOpen_File.triggered.connect(self.open_file_action)
        self.ui.actionReload_Display.triggered.connect(self.reload_display)
        self.ui.actionIncrease_Font_Size.triggered.connect(self.increase_font_size)
        self.ui.actionDecrease_Font_Size.triggered.connect(self.decrease_font_size)
        self.ui.actionDefault_Font_Size.triggered.connect(self.reset_font_size)
        self.ui.actionEnter_Fullscreen.triggered.connect(self.enter_fullscreen)
        self.ui.actionShow_File_Path_in_Title_Bar.triggered.connect(self.toggle_file_path_in_title_bar)
        self.ui.actionShow_Navigation_Bar.triggered.connect(self.toggle_nav_bar)
        self.ui.actionShow_Menu_Bar.triggered.connect(self.toggle_menu_bar)
        self.ui.actionShow_Status_Bar.triggered.connect(self.toggle_status_bar)
        self.ui.actionShow_Connections.triggered.connect(self.show_connections)
        self.ui.actionAbout_PyDM.triggered.connect(self.show_about_window)
        self.ui.actionLoadTool.triggered.connect(self.load_tool)
        self.ui.actionLoadTool.setIcon(self.iconFont.icon("rocket"))

        self._saved_menu_geometry = None
        self._saved_menu_height = None
        self._new_widget_size = None
        if hide_nav_bar:
            self.toggle_nav_bar(False)
        if hide_menu_bar:
            # Toggle the menu bar via the QAction so that the menu item
            # stays in sync with menu visibility.
            self.ui.actionShow_Menu_Bar.activate(QAction.Trigger)
        if hide_status_bar:
            self.toggle_status_bar(False)
        #Try to find the designer binary.
        self.ui.actionEdit_in_Designer.setEnabled(False)
        self.designer_path = None
        possible_designer_bin_paths = (QLibraryInfo.location(QLibraryInfo.BinariesPath), QLibraryInfo.location(QLibraryInfo.LibraryExecutablesPath))
        for bin_path in possible_designer_bin_paths:
            if platform.system() == 'Darwin':
                designer_path = os.path.join(bin_path, 'Designer.app/Contents/MacOS/Designer')
            elif platform.system() == 'Linux':
                designer_path = os.path.join(bin_path, 'designer')
            else:
                designer_path = os.path.join(bin_path, 'designer.exe')
            if os.path.isfile(designer_path):
                self.designer_path = designer_path
                break

        self.update_tools_menu()

    def set_display_widget(self, new_widget):
        if new_widget == self._display_widget:
            return
        self.clear_display_widget()
        if not new_widget.layout():
            new_widget.setMinimumSize(new_widget.size())
        self._new_widget_size = new_widget.size()
        self._display_widget = new_widget
        self.setCentralWidget(self._display_widget)
        self.update_window_title()
        # Resizing to the new widget's dimensions needs to be
        # done on the event loop for some reason - you can't
        # just do it here.
        QTimer.singleShot(0, self.resizeForNewDisplayWidget)

    def clear_display_widget(self):
        if self._display_widget is not None:
            self.setCentralWidget(QWidget())
            rules.unregister_widget_rules(self._display_widget)
            self._display_widget.deleteLater()
            self._display_widget = None
            self.ui.actionEdit_in_Designer.setEnabled(False)

    def join_to_current_file_path(self, ui_file):
        ui_file = str(ui_file)
        # Expand user (~ or ~user) and environment variables.
        ui_file = os.path.expanduser(os.path.expandvars(ui_file))
        if path.isabs(ui_file) or len(self.back_stack) == 0:
            return str(ui_file)
        else:
            return path.join(path.dirname(self.current_file()), ui_file)

    def open_file(self, ui_file, macros=None, command_line_args=None):
        filename = self.join_to_current_file_path(ui_file)
        try:
            if not os.path.exists(filename):
                new_fname = find_display_in_path(ui_file)
                if new_fname is None or new_fname == "":
                    raise IOError("File {} not found".format(filename))
                filename = new_fname
            self.open_abs_file(filename, macros, command_line_args)
        except (IOError, OSError, ValueError, ImportError) as e:
            error_msg = "Cannot open file: '{0}'. Reason: '{1}'.".format(filename, e)
            logger.error(error_msg)
            self.statusBar().showMessage(error_msg, 5000)

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
        # Update here the Menu Editor text...
        ui_file, py_file = self.get_files_in_display()
        edit_in_text = "Open in "
        editors = []
        if ui_file is not None and ui_file != "":
            editors.append("Designer")
        if py_file is not None and py_file != "":
            editors.append("Text Editor")
        edit_in_text += ' and '.join(editors)
        self.ui.actionEdit_in_Designer.setText(edit_in_text)
        if self.designer_path:
            self.ui.actionEdit_in_Designer.setEnabled(True)

    def new_window(self, ui_file, macros=None, command_line_args=None):
        filename = self.join_to_current_file_path(ui_file)
        try:
            if not os.path.exists(filename):
                new_fname = find_display_in_path(ui_file)
                if new_fname is None or new_fname == "":
                    raise IOError("File {} not found".format(filename))
                filename = new_fname
            self.new_abs_window(filename, macros, command_line_args)
        except (IOError, OSError, ValueError, ImportError) as e:
            error_msg = "Cannot open file: '{0}'. Reason: '{1}'.".format(filename, e)
            logger.error(error_msg)
            self.statusBar().showMessage(error_msg, 5000)

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

    # Note: in go(), back(), and forward(), always do history stack manipulation *before* opening the file.
    # That way, the navigation button enable/disable state will work correctly.  This is stupid, and will be fixed eventually.
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
        if self.home_file is None:
            return

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
            title = self.current_file()
        else:
            title = self._display_widget.windowTitle()
        title += " - PyDM"
        if data_plugins.is_read_only():
            title += " [Read Only Mode]"
        self.setWindowTitle(title)

    @property
    def showing_file_path_in_title_bar(self):
        return self._showing_file_path_in_title_bar

    @showing_file_path_in_title_bar.setter
    def showing_file_path_in_title_bar(self, checked):
        self._showing_file_path_in_title_bar = checked
        self.update_window_title()

    @Slot(bool)
    def toggle_file_path_in_title_bar(self, checked):
        self.showing_file_path_in_title_bar = checked

    @Slot(bool)
    def toggle_nav_bar(self, checked):
        self.ui.navbar.setHidden(not checked)

    @Slot(bool)
    def toggle_menu_bar(self, checked=None):
        if checked is None:
            checked = not self.ui.menubar.isVisible()
        # Crazy hack: we can't just do menubar.setVisible(), because that
        # will disable all the QActions and their keyboard shortcuts when
        # we hide the menu.  So instead, we set it to a height of 0 to hide
        # it, and then restore the previous height value to show it again.
        if checked:
            self.ui.menubar.restoreGeometry(self._saved_menu_geometry)
            self.ui.menubar.setFixedHeight(self._saved_menu_height)
        else:
            self._saved_menu_geometry = self.ui.menubar.saveGeometry()
            self._saved_menu_height = self.ui.menubar.height()
            self.ui.menubar.setFixedHeight(0)

    @Slot(bool)
    def toggle_status_bar(self, checked):
        self.ui.statusbar.setHidden(not checked)

    def get_files_in_display(self):
        try:
            curr_file = self.current_file()
        except IndexError:
            logger.error("The display manager does not have a display loaded.")
            return None, None

        _, extension = path.splitext(curr_file)
        if extension == '.ui':
            return self.current_file(), None
        else:
            central_widget = self.centralWidget() if isinstance(self.centralWidget(), Display) else None
            if central_widget is not None:
                ui_file = central_widget.ui_filepath()
            return ui_file, self.current_file()

    @Slot(bool)
    def edit_in_designer(self, checked):

        def open_editor_ui(fname):
            if self.designer_path is None or fname is None or fname == "":
                return
            self.statusBar().showMessage("Launching '{0}' in Qt Designer...".format(fname), 5000)
            _ = subprocess.Popen('{0} "{1}"'.format(self.designer_path, fname), shell=True)

        def open_editor_generic(fname):
            if platform.system() == "Darwin":
                subprocess.call(('open', fname))
            elif platform.system() == "Linux":
                subprocess.call(('xdg-open', fname))
            elif platform.system() == "Windows":
                os.startfile(fname)

        ui_file, py_file = self.get_files_in_display()
        if ui_file is not None and ui_file != "":
            open_editor_ui(fname=ui_file)
        if py_file is not None and py_file != "":
            open_editor_generic(fname=py_file)

    @Slot(bool)
    def open_file_action(self, checked):
        modifiers = QApplication.keyboardModifiers()
        try:
            curr_file = self.current_file()
            folder = os.path.dirname(curr_file)
        except IndexError:
            folder = os.getcwd()

        filename = QFileDialog.getOpenFileName(self, 'Open File...', folder, 'PyDM Display Files (*.ui *.py)')
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

    def load_tool(self, checked):
        try:
            curr_dir = os.path.dirname(self.current_file())
        except IndexError:
            logger.error("The display manager does not have a display loaded. Suggesting current work directory.")
            curr_dir = os.getcwd()
        filename = QFileDialog.getOpenFileName(self, 'Load tool...', curr_dir, 'PyDM External Tool Files (*_tool.py)')
        filename = filename[0] if isinstance(filename, (list, tuple)) else filename

        if filename:
            filename = str(filename)
            tools.install_external_tool(filename)
            self.update_tools_menu()

    def update_tools_menu(self):
        """
        Update the Main Window Tools menu.
        """
        kwargs = {'channels': None, 'sender': self}
        tools.assemble_tools_menu(self.ui.menuTools,
                                  clear_menu=True,
                                  **kwargs)

        self.ui.menuTools.addSeparator()
        self.ui.menuTools.addAction(self.ui.actionLoadTool)

    @Slot(bool)
    def reload_display(self, checked):
        try:
            curr_file = self.current_file()
        except IndexError:
            logger.error("The display manager does not have a display loaded.")
            return
        self.statusBar().showMessage("Reloading '{0}'...".format(self.current_file()), 5000)
        self.go_abs(self.current_file())

    @Slot(bool)
    def increase_font_size(self, checked):
        current_font = QApplication.instance().font()
        current_font.setPointSizeF(current_font.pointSizeF() * 1.1)
        QApplication.instance().setFont(current_font)
        QTimer.singleShot(0, self.resizeForNewDisplayWidget)

    @Slot(bool)
    def decrease_font_size(self, checked):
        current_font = QApplication.instance().font()
        current_font.setPointSizeF(current_font.pointSizeF() / 1.1)
        QApplication.instance().setFont(current_font)
        QTimer.singleShot(0, self.resizeForNewDisplayWidget)
    
    @Slot(bool)
    def reset_font_size(self, checked):
        current_font = QApplication.instance().font()
        current_font.setPointSizeF(self.default_font_size)
        QApplication.instance().setFont(current_font)
        QTimer.singleShot(0, self.resizeForNewDisplayWidget)

    @Slot(bool)
    def enter_fullscreen(self, checked=False):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    @Slot(bool)
    def show_connections(self, checked):
        c = ConnectionInspector(self)
        c.show()

    @Slot(bool)
    def show_about_window(self, checked):
        a = AboutWindow(self)
        a.show()

    def resizeForNewDisplayWidget(self):
        if not self.isFullScreen():
            self.resize(self._new_widget_size)

    def closeEvent(self, event):
        self.clear_display_widget()
        self.app.close_window(self)
