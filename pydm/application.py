"""
Main Application Module

Contains our PyDMApplication class with core connection and loading logic and
our PyDMMainWindow class with navigation logic.
"""
import os
import imp
import sys
import uuid
import signal
import subprocess
import json
import inspect
import logging
import warnings
from .display_module import Display
from qtpy.QtCore import Qt, QTimer, Slot
from qtpy.QtWidgets import QApplication, QWidget
from qtpy.QtGui import QColor
from qtpy import uic
from .main_window import PyDMMainWindow

from .utilities import macro, which, path_info, find_display_in_path
from .utilities.stylesheet import apply_stylesheet
from .utilities import connection
from . import data_plugins
from .widgets.rules import RulesDispatcher

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
        # The macro and directory stacks are needed for nested displays (usually PyDMEmbeddedDisplays).
        # During the process of loading a display (whether from a .ui file, or a .py file), the application's
        # 'open_file' method will be called recursively.    Inside open_file, the last item on the stack represents
        # the parent widget's file path and macro variables.    Any file paths are joined to the end of the parent's
        # file path, and any macros are merged with the parent's macros.    This system depends on open_file always
        # being called hierarchially (i.e., parent calls it first, then on down the ancestor tree, with no unrelated
        # calls in between).    If something crazy happens and PyDM somehow gains the ability to open files in a
        # multi-threaded way, for example, this system will fail.
        data_plugins.set_read_only(read_only)
        self.main_window = None
        self.directory_stack = ['']
        self.macro_stack = [{}]
        self.windows = {}
        self.display_args = display_args
        self.hide_nav_bar = hide_nav_bar
        self.hide_menu_bar = hide_menu_bar
        self.hide_status_bar = hide_status_bar
        self.fullscreen = fullscreen

        # Open a window if required.
        if ui_file is not None:
            self.make_main_window(stylesheet_path=stylesheet_path)
            self.make_window(ui_file, macros, command_line_args)
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
                pydm_display_app_path = os.path.join(os.path.split(os.path.realpath(__file__))[0], "..", "scripts", "pydm")

        args = [pydm_display_app_path]
        if self.hide_nav_bar:
            args.extend(["--hide-nav-bar"])
        if self.hide_menu_bar:
            args.extend(["--hide-menu-bar"])
        if self.hide_status_bar:
            args.extend(["--hide-status-bar"])
        if self.fullscreen:
            args.extend(["--fullscreen"])
        if macros is not None:
            args.extend(["-m", json.dumps(macros)])
        args.append(filepath)
        args.extend(self.display_args)
        args.extend(filepath_args)
        if command_line_args is not None:
            args.extend(command_line_args)
        subprocess.Popen(args, shell=False)

    def new_window(self, ui_file, macros=None, command_line_args=None):
        """
        Make a new window and open the supplied file.
        Currently, this method just calls `new_pydm_process`.

        This is an internal method that typically will not be needed by users.

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
        # All new windows are spawned as new processes.
        self.new_pydm_process(ui_file, macros, command_line_args)

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

        # If we are launching a new window, we don't want it to sit right on top of an existing window.
        if len(self.windows) > 1:
            main_window.move(main_window.x() + 10, main_window.y() + 10)

    def make_window(self, ui_file, macros=None, command_line_args=None):
        """
        Open the ui_file in the window.

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
        if ui_file is not None:
            self.main_window.open_file(ui_file, macros, command_line_args)
            self.windows[self.main_window] = path_info(ui_file)[0]

    def close_window(self, window):
        try:
            del self.windows[window]
        except KeyError:
            # If window is no longer at self.windows
            # it means that we already closed it.
            pass

    def load_ui_file(self, uifile, macros=None):
        """
        Load a .ui file, perform macro substitution, then return the resulting QWidget.

        This is an internal method, users will usually want to use `open_file` instead.

        Parameters
        ----------
        uifile : str
            The path to a .ui file to load.
        macros : dict, optional
            A dictionary of macro variables to supply to the file
            to be opened.

        Returns
        -------
        QWidget
        """
        if macros is not None and len(macros) > 0:
            f = macro.substitute_in_file(uifile, macros)
        else:
            f = uifile
        return uic.loadUi(f)

    def load_py_file(self, pyfile, args=None, macros=None):
        """
        Load a .py file, performs some sanity checks to try and determine
        if the file actually contains a valid PyDM Display subclass, and if
        the checks pass, create and return an instance.

        This is an internal method, users will usually want to use `open_file` instead.

        Parameters
        ----------
        pyfile : str
            The path to a .ui file to load.
        args : list, optional
            A list of command-line arguments to pass to the
            loaded display subclass.
        macros : dict, optional
            A dictionary of macro variables to supply to the
            loaded display subclass.

        Returns
        -------
        pydm.Display
        """
        # Add the intelligence module directory to the python path, so that submodules can be loaded.    Eventually, this should go away, and intelligence modules should behave as real python modules.
        module_dir = os.path.dirname(os.path.abspath(pyfile))
        sys.path.append(module_dir)
        temp_name = str(uuid.uuid4())

        # Now load the intelligence module.
        module = imp.load_source(temp_name, pyfile)
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
            # This only works in python 3 and up.
            module_params = inspect.signature(cls).parameters
        except AttributeError:
            # Works in python 2, deprecated in 3.0 and up.
            module_params = inspect.getargspec(cls.__init__).args

        # Because older versions of Display may not have the args parameter or the macros parameter, we check
        # to see if it does before trying to use them.
        kwargs = {}
        if 'args' in module_params:
            kwargs['args'] = args
        if 'macros' in module_params:
            kwargs['macros'] = macros
        return cls(**kwargs)

    def open_file(self, ui_file, macros=None, command_line_args=None, **kwargs):
        """
        Open a .ui or .py file, and return a widget from the loaded file.
        This method is the entry point for all opening of new displays,
        and manages handling macros and relative file paths when opening
        nested displays.

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

        Returns
        -------
        QWidget
        """
        if 'establish_connection' in kwargs:
            logger.warning("Ignoring 'establish_connection' parameter at "
                           "open_relative. The connection is now handled by the"
                           " widgets.")

        # First split the ui_file string into a filepath and arguments
        args = command_line_args if command_line_args is not None else []
        dir_name, file_name, extra_args = path_info(ui_file)
        args.extend(extra_args)
        filepath = os.path.join(dir_name, file_name)
        self.directory_stack.append(dir_name)
        (filename, extension) = os.path.splitext(file_name)
        if macros is None:
            macros = {}
        merged_macros = self.macro_stack[-1].copy()
        merged_macros.update(macros)
        self.macro_stack.append(merged_macros)
        if extension == '.ui':
            widget = self.load_ui_file(filepath, merged_macros)
        elif extension == '.py':
            widget = self.load_py_file(filepath, args, merged_macros)
        else:
            self.directory_stack.pop()
            self.macro_stack.pop()
            raise ValueError("Invalid file type: {}".format(extension))
        # Add on the macros to the widget after initialization. This is
        # done for both ui files and python files.
        widget.base_macros = merged_macros
        self.directory_stack.pop()
        self.macro_stack.pop()
        return widget

    # get_path gives you the path to ui_file relative to where you are running pydm from.
    # Many widgets handle file paths (related display, embedded display, and drawing image come to mind)
    # and the standard is that they expect paths to be given relative to the .ui or .py file in which the
    # widget lives.  But, python and Qt want the file path relative to the directory you are running
    # pydm from.  This function does that translation.
    def get_path(self, ui_file):
        """
        Gives you the path to ui_file relative to where you are running pydm from.

        Many widgets handle file paths (related display, embedded display,
        and drawing image come to mind) and the standard is that they expect
        paths to be given relative to the .ui or .py file in which the widget
        lives.  But, python and Qt want the file path relative to the directory
        you are running pydm from.  This function does that translation.

        Parameters
        ----------
        ui_file : str

        Returns
        -------
        str
        """
        dirname = self.directory_stack[-1]
        full_path = os.path.join(dirname, str(ui_file))
        return full_path

    def open_relative(self, ui_file, widget, macros=None, command_line_args=[],
                      **kwargs):
        """
        open_relative opens a ui file with a relative path.  This is
        really only used by embedded displays.
        """
        if 'establish_connection' in kwargs:
            logger.warning("Ignoring 'establish_connection' parameter at "
                           "open_relative. The connection is now handled by the"
                           " widgets.")
        full_path = self.get_path(ui_file)

        if not os.path.exists(full_path):
            new_fname = find_display_in_path(ui_file)
            if new_fname is not None and new_fname != "":
                full_path = new_fname
        return self.open_file(full_path, macros=macros,
                              command_line_args=command_line_args)

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
