"""
Main Application Module

Contains our PyDMApplication class with core connection and loading logic and
our PyDMMainWindow class with navigation logic.
"""
import os
import signal
import subprocess
import json
import logging
import warnings

from qtpy.QtCore import Qt, QTimer, Slot
from qtpy.QtWidgets import QApplication, QWidget
from .main_window import PyDMMainWindow

from .display import load_file
from .utilities import macro, which, path_info, find_display_in_path
from .utilities.stylesheet import apply_stylesheet
from .utilities import connection
from . import data_plugins

logger = logging.getLogger(__name__)


class PyDMApplication(QApplication):
    """
    PyDMApplication handles loading PyDM display files, opening
    new windows, and most importantly, establishing and managing
    connections to channels via data plugins.

    Parameters
    ----------
    ui_file : str, optional
        The file path to a PyDM display file (.ui or .py).
    command_line_args : list, optional
        A list of strings representing arguments supplied at the command
        line.  All arguments in this list are handled by QApplication,
        in addition to PyDMApplication.
    display_args : list, optional
        A list of command line arguments that should be forwarded to the
        Display class.  This is only useful if a Related Display Button
        is opening up a .py file with extra arguments specified, and
        probably isn't something you will ever need to use when writing
        code that instantiates PyDMApplication.
    perfmon : bool, optional
        Whether or not to enable performance monitoring using 'psutil'.
        When enabled, CPU load information on a per-thread basis is
        periodically printed to the terminal.
    hide_nav_bar : bool, optional
        Whether or not to display the navigation bar (forward/back/home buttons)
        when the main window is first displayed.
    hide_menu_bar: bool, optional
        Whether or not to display the menu bar (File, View)
        when the main window is first displayed.
    hide_status_bar: bool, optional
        Whether or not to display the status bar (general messages and errors)
        when the main window is first displayed.
    read_only: bool, optional
        Whether or not to launch PyDM in a read-only state.
    macros : dict, optional
        A dictionary of macro variables to be forwarded to the display class
        being loaded.
    use_main_window : bool, optional
        If ui_file is note given, this parameter controls whether or not to
        create a PyDMMainWindow in the initialization (Default is True).
    fullscreen : bool, optional
        Whether or not to launch PyDM in a full screen mode.
    """
    # Instantiate our plugins.
    plugins = data_plugins.plugin_modules

    def __init__(self, ui_file=None, command_line_args=[], display_args=[],
                 perfmon=False, hide_nav_bar=False, hide_menu_bar=False,
                 hide_status_bar=False, read_only=False, macros=None,
                 use_main_window=True, stylesheet_path=None, fullscreen=False):
        super(PyDMApplication, self).__init__(command_line_args)
        # Enable High DPI display, if available.
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            self.setAttribute(Qt.AA_UseHighDpiPixmaps)

        data_plugins.set_read_only(read_only)
        self.main_window = None
        self.display_args = display_args
        self.hide_nav_bar = hide_nav_bar
        self.hide_menu_bar = hide_menu_bar
        self.hide_status_bar = hide_status_bar
        self.fullscreen = fullscreen
        self.stylesheet_path = stylesheet_path
        self.perfmon = perfmon

        # Open a window if required.
        if ui_file is not None:
            self.make_main_window(stylesheet_path=stylesheet_path)
            self.main_window.open(ui_file, macros, command_line_args)
        elif use_main_window:
            self.make_main_window(stylesheet_path=stylesheet_path)

        self.had_file = ui_file is not None
        # Re-enable sigint (usually blocked by pyqt)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Performance monitoring
        if perfmon:
            import psutil
            self.perf = psutil.Process()
            self.perf_timer = QTimer()
            self.perf_timer.setInterval(2000)
            self.perf_timer.timeout.connect(self.get_CPU_usage)
            self.perf_timer.start()

    def get_string_encoding(self):
        return os.getenv("PYDM_STRING_ENCODING", "utf_8")

    def exec_(self):
        """
        Execute the QApplication.
        """
        return super(PyDMApplication, self).exec_()

    def is_read_only(self):
        warnings.warn("'PyDMApplication.is_read_only' is deprecated, "
                      "use 'pydm.data_plugins.is_read_only' instead.")
        return data_plugins.is_read_only()

    @Slot()
    def get_CPU_usage(self):
        """
        Prints total CPU usage (in percent), as well as per-thread usage, to the terminal.
        """
        with self.perf.oneshot():
            total_percent = self.perf.cpu_percent(interval=None)
            total_time = sum(self.perf.cpu_times())
            usage = [total_percent * ((t.system_time + t.user_time) / total_time) for t in self.perf.threads()]
        print("Total: {tot}, Per Thread: {percpu}".format(tot=total_percent, percpu=usage))

    def new_pydm_process(self, ui_file, macros=None, command_line_args=None):
        """
        Spawn a new PyDM process and open the supplied file.  Commands to open
        new windows in PyDM typically actually spawn an entirely new PyDM process.
        This keeps each window isolated, so that one window cannot slow
        down or crash another.

        Parameters
        ----------
        ui_file : str
            The path to a .ui or .py file to open in the new process.
        macros : dict, optional
            A dictionary of macro variables to supply to the display file
            to be opened.
        command_line_args : list, optional
            A list of command line arguments to pass to the new process.
            Typically, this argument is used by related display buttons
            to pass in extra arguments.  It is probably rare that code you
            write needs to use this argument.
        """
        # Expand user (~ or ~user) and environment variables.
        ui_file = os.path.expanduser(os.path.expandvars(ui_file))
        base_dir, fname, args = path_info(str(ui_file))
        filepath = os.path.join(base_dir, fname)
        filepath_args = args
        pydm_display_app_path = which("pydm")

        if pydm_display_app_path is None:
            if os.environ.get("PYDM_PATH") is not None:
                pydm_display_app_path = os.path.join(os.environ["PYDM_PATH"], "pydm")
            else:
                # Not in the PATH and no ENV VAR pointing to it...
                # Let's try the script folder...
                pydm_display_app_path = os.path.join(os.path.split(os.path.realpath(__file__))[0], "..", "pydm_launcher", "main.py")

        args = [pydm_display_app_path]
        if self.hide_nav_bar:
            args.extend(["--hide-nav-bar"])
        if self.hide_menu_bar:
            args.extend(["--hide-menu-bar"])
        if self.hide_status_bar:
            args.extend(["--hide-status-bar"])
        if self.fullscreen:
            args.extend(["--fullscreen"])
        if self.perfmon:
            args.extend(["--perfmon"])
        if data_plugins.is_read_only():
            args.append("--read-only")
        if self.stylesheet_path:
            args.extend(["--stylesheet", self.stylesheet_path])
        if macros is not None:
            args.extend(["-m", json.dumps(macros)])
        args.extend(["--log_level", logging.getLevelName(logging.getLogger("").getEffectiveLevel())])
        args.append(filepath)
        args.extend(self.display_args)
        args.extend(filepath_args)
        if command_line_args is not None:
            args.extend(command_line_args)
        subprocess.Popen(args, shell=False)

    def make_main_window(self, stylesheet_path=None):
        """
        Instantiate a new PyDMMainWindow, add it to the application's
        list of windows. Typically, this function is only called as part
        of starting up a new process, because PyDMApplications only have
        one window per process.
        """
        main_window = PyDMMainWindow(hide_nav_bar=self.hide_nav_bar,
                                     hide_menu_bar=self.hide_menu_bar,
                                     hide_status_bar=self.hide_status_bar)

        self.main_window = main_window
        apply_stylesheet(stylesheet_path, widget=self.main_window)
        self.main_window.update_tools_menu()

        if self.fullscreen:
            main_window.enter_fullscreen()
        else:
            main_window.show()

    def plugin_for_channel(self, channel):
        """
        Given a PyDMChannel object, determine the appropriate plugin to use.

        Parameters
        ----------
        channel : PyDMChannel

        Returns
        -------
        PyDMPlugin
        """
        warnings.warn("'PyDMApplication.plugin_for_channel' is deprecated, "
                      "use 'pydm.data_plugins.plugin_for_address' instead.")
        if channel.address is None or channel.address == "":
            return None
        return data_plugins.plugin_for_address(channel.address)

    def add_connection(self, channel):
        """
        Add a new connection to a channel.

        Parameters
        ----------
        channel : PyDMChannel
        """
        warnings.warn("'PyDMApplication.add_connection' is deprecated, "
                      "use PyDMConnection.connect()")
        channel.connect()

    def remove_connection(self, channel):
        """
        Remove a connection to a channel.

        Parameters
        ----------
        channel : PyDMChannel
        """
        warnings.warn("'PyDMApplication.remove_connection' is deprecated, "
                      "use PyDMConnection.disconnect()")
        channel.disconnect()

    def eventFilter(self, obj, event):
        warnings.warn("'PyDMApplication.eventFilter' is deprecated, "
                      " this function is now found on PyDMWidget")
        obj.eventFilter(obj, event)

    def show_address_tooltip(self, obj, event):
        warnings.warn("'PyDMApplication.show_address_tooltip' is deprecated, "
                      " this function is now found on PyDMWidget")
        obj.show_address_tooltip(event)

    def establish_widget_connections(self, widget):
        """
        Given a widget to start from, traverse the tree of child widgets,
        and try to establish connections to any widgets with channels.

        Display subclasses which dynamically create widgets may need to
        use this method.

        Parameters
        ----------
        widget : QWidget
        """
        warnings.warn("'PyDMApplication.establish_widget_connections' is deprecated, "
                      "this function is now found on `utilities.establish_widget_connections`.")
        connection.establish_widget_connections(widget)

    def close_widget_connections(self, widget):
        """
        Given a widget to start from, traverse the tree of child widgets,
        and try to close connections to any widgets with channels.

        Parameters
        ----------
        widget : QWidget
        """
        warnings.warn(
            "'PyDMApplication.close_widget_connections' is deprecated, "
            "this function is now found on `utilities.close_widget_connections`.")
        connection.close_widget_connections(widget)
