import os
from os import path
from qtpy.QtWidgets import (QApplication, QMainWindow, QFileDialog,
                            QWidget, QAction, QMessageBox)
from qtpy.QtCore import Qt, QTimer, Slot, QSize, QLibraryInfo
from .utilities import (IconFont, find_file, establish_widget_connections,
                        close_widget_connections)
from .pydm_ui import Ui_MainWindow
from .display import Display, ScreenTarget, load_file
from .connection_inspector import ConnectionInspector
from .about_pydm import AboutWindow
from . import data_plugins
from . import tools
from .widgets.rules import register_widget_rules, unregister_widget_rules
from . import config
import subprocess
import platform
import logging

logger = logging.getLogger(__name__)


class PyDMMainWindow(QMainWindow):

    def __init__(self, parent=None, hide_nav_bar=False, hide_menu_bar=False, hide_status_bar=False):
        super(PyDMMainWindow, self).__init__(parent)
        self.app = QApplication.instance()
        self.font_factor = 1
        self.iconFont = IconFont()
        self._display_widget = None
        self._showing_file_path_in_title_bar = False

        self._saved_menu_geometry = None
        self._saved_menu_height = None
        self._new_widget_size = None

        self.default_font_size = QApplication.instance().font().pointSizeF()

        self.home_file = None
        self.home_widget = None

        self.designer_path = None

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.navbar.setIconSize(QSize(24, 24))
        self.ui.navbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.ui.actionHome.triggered.connect(self.home_triggered)
        self.ui.actionHome.setIcon(self.iconFont.icon("home"))
        self.ui.actionBack.triggered.connect(self.back_triggered)
        self.ui.actionBack.setIcon(self.iconFont.icon("angle-left"))
        self.ui.actionForward.triggered.connect(self.forward_triggered)
        self.ui.actionForward.setIcon(self.iconFont.icon("angle-right"))
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
        self.ui.actionQuit.triggered.connect(self.quit_main_window)

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
        self.enable_disable_navigation()

    def display_widget(self):
        return self._display_widget

    def set_display_widget(self, new_widget):
        if new_widget == self._display_widget:
            return
        self.clear_display_widget()
        if not new_widget.layout():
            new_widget.setMinimumSize(new_widget.size())
        self._new_widget_size = new_widget.size()
        new_widget.setVisible(True)
        self._display_widget = new_widget
        self.setCentralWidget(self._display_widget)
        self.enable_disable_navigation()
        self.update_window_title()
        # Resizing to the new widget's dimensions needs to be
        # done on the event loop for some reason - you can't
        # just do it here.
        QTimer.singleShot(0, self.resizeForNewDisplayWidget)

    def clear_display_widget(self):
        if self._display_widget is not None:
            close_widget_connections(self._display_widget)
            unregister_widget_rules(self._display_widget)
            self._display_widget.setVisible(False)
            self._display_widget.setParent(None)
            self.ui.actionEdit_in_Designer.setEnabled(False)

    def handle_open_file_error(self, filename, error):
        self.statusBar().showMessage("Cannot open file: '{0}', reason: '{1}'...".format(filename, error), 5000)

    def back_triggered(self):
        new_process = QApplication.keyboardModifiers() == Qt.ShiftModifier
        self.back(open_in_new_process=new_process)

    def back(self, open_in_new_process=False):
        curr_display = self.display_widget()
        prev_display = None
        if curr_display:
            prev_display = curr_display.previous_display

        if not prev_display:
            logger.error('No display history to execute back navigation.')
            return

        if open_in_new_process:
            load_file(prev_display.loaded_file(),
                      macros=prev_display.macros,
                      args=prev_display.args,
                      target=ScreenTarget.NEW_PROCESS)
        else:
            prev_display.next_display = curr_display
            establish_widget_connections(prev_display)
            register_widget_rules(prev_display)
            self.set_display_widget(prev_display)

    def forward_triggered(self):
        new_process = QApplication.keyboardModifiers() == Qt.ShiftModifier
        self.forward(open_in_new_process=new_process)

    def forward(self, open_in_new_process=False):
        curr_display = self.display_widget()
        next_display = None
        if curr_display:
            next_display = curr_display.next_display

        if not next_display:
            logger.error('No display history to execute forward navigation.')
            return

        if open_in_new_process:
            load_file(next_display.loaded_file(),
                      macros=next_display.macros,
                      args=next_display.args,
                      target=ScreenTarget.NEW_PROCESS)
        else:
            establish_widget_connections(next_display)
            register_widget_rules(next_display)
            next_display.previous_display = curr_display
            self.set_display_widget(next_display)

    def home_triggered(self):
        new_process = QApplication.keyboardModifiers() == Qt.ShiftModifier
        self.home(open_in_new_process=new_process)

    def home(self, open_in_new_process=False):
        if self.home_widget is None:
            return

        if open_in_new_process:
            fname = self.home_widget.loaded_file()
            macros = self.home_widget.macros()
            args = self.home_widget.args()
            load_file(fname,
                      macros=macros,
                      args=args,
                      target=ScreenTarget.NEW_PROCESS)
        else:
            self.set_display_widget(self.home_widget)

    def enable_disable_navigation(self):
        w = self.display_widget()
        if not isinstance(w, Display):
            # We can't do much if it is not a Display and we don't have the
            # previous_display and next_display properties since we don't
            # have the navigation stack set.
            nav_stack_methods = hasattr(w, 'previous_display') \
                                and hasattr(w, 'next_display')
            if not nav_stack_methods:
                return
        if not w:
            self.ui.actionBack.setDisabled(True)
            self.ui.actionForward.setDisabled(True)
            return
        self.ui.actionBack.setDisabled(w.previous_display is None)
        self.ui.actionForward.setDisabled(w.next_display is None)

    def current_file(self):
        return self.display_widget().loaded_file()

    def update_window_title(self):
        if self.showing_file_path_in_title_bar:
            title = self.current_file()
        else:
            title = self.display_widget().windowTitle()
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
        except Exception:
            folder = os.getcwd()

        filename = QFileDialog.getOpenFileName(self, 'Open File...', folder, 'PyDM Display Files (*.ui *.py)')
        filename = filename[0] if isinstance(filename, (list, tuple)) else filename

        if filename:
            filename = str(filename)
            try:
                if modifiers == Qt.ShiftModifier:
                    target = ScreenTarget.NEW_PROCESS
                else:
                    target = None
                self.open(filename, target=target)

            except (IOError, OSError, ValueError, ImportError) as e:
                self.handle_open_file_error(filename, e)

    def open(self, filename, macros=None, args=None, target=None):
        if not os.path.isabs(filename):
            base_path = None
            curr_display = self.display_widget()
            if curr_display:
                base_path = os.path.dirname(curr_display.loaded_file())
            filename = find_file(filename, base_path=base_path)
        new_widget = load_file(filename,
                               macros=macros,
                               args=args,
                               target=target)
        if new_widget:
            if self.home_widget is None:
                self.home_widget = new_widget
            display_widget = self.display_widget()
            if display_widget:
                new_widget.previous_display = display_widget
            self.set_display_widget(new_widget)
            ui_file, py_file = self.get_files_in_display()
            editors = []
            if ui_file:
                editors.append("Designer")
            if py_file:
                editors.append("Text Editor")
            edit_in_text = "Open in {}".format(' and '.join(editors))
            self.ui.actionEdit_in_Designer.setText(edit_in_text)
            if (self.designer_path and ui_file) or (py_file and not ui_file):
                self.ui.actionEdit_in_Designer.setEnabled(True)
        return new_widget

    def load_tool(self, checked):
        try:
            curr_dir = os.path.dirname(self.current_file())
        except Exception:
            curr_dir = os.getcwd()
            logger.error("The display manager does not have a display loaded. Suggesting current work directory.")
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
        curr_display = self.display_widget()
        if not curr_display:
            logger.error("The display manager does not have a display loaded.")
            return

        prev_display = curr_display.previous_display
        next_display = curr_display.next_display

        macros = curr_display.macros()
        args = curr_display.args()
        loaded_file = curr_display.loaded_file()

        self.statusBar().showMessage(
            "Reloading '{0}'...".format(self.current_file()), 5000)
        new_widget = self.open(loaded_file, macros=macros, args=args)
        new_widget.previous_display = prev_display
        new_widget.next_display = next_display

    @Slot(bool)
    def increase_font_size(self, checked):
        old_factor = self.font_factor
        self.font_factor += 0.1
        self.set_font_size(old_factor, self.font_factor)

    @Slot(bool)
    def decrease_font_size(self, checked):
        old_factor = self.font_factor
        self.font_factor -= 0.1
        self.set_font_size(old_factor, self.font_factor)

    @Slot(bool)
    def reset_font_size(self, checked):
        old_factor = self.font_factor
        self.font_factor = 1
        self.set_font_size(old_factor, self.font_factor)

    def set_font_size(self, old, new):
        current_font = self.app.font()
        current_font.setPointSizeF(current_font.pointSizeF()/old*new)
        QApplication.instance().setFont(current_font)

        for w in self.app.allWidgets():
            w_c_f = w.font()
            w_c_f.setPointSizeF(w_c_f.pointSizeF()/old*new)
            w.setFont(w_c_f)

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
        event.ignore()

        def do_close():
            self.clear_display_widget()
            event.accept()

        main_windows = [w for w in self.app.topLevelWidgets() if isinstance(w, QMainWindow)]
        if len(main_windows) == 1 and main_windows[0] == self:
            self._confirm_quit(callback=do_close)
        else:
            do_close()

    @Slot(bool)
    def quit_main_window(self, checked):
        self._confirm_quit(callback=self.app.quit)

    def _confirm_quit(self, callback):
        if not config.CONFIRM_QUIT:
            callback()
        else:
            quit_message = QMessageBox.question(
                self, 'Quitting Application', 'Exit Application?',
                QMessageBox.Yes | QMessageBox.No)
            if quit_message == QMessageBox.Yes:
                callback()
