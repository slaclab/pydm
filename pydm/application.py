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
import json
import inspect
import warnings
from .display_module import Display
from .PyQt.QtCore import Qt, QEvent, QTimer, pyqtSlot
from .PyQt.QtGui import QApplication, QColor, QWidget, QToolTip, QClipboard
from .PyQt import uic
from .main_window import PyDMMainWindow
from .utilities import macro, which
from . import data_plugins

DEFAULT_PROTOCOL = os.getenv("PYDM_DEFAULT_PROTOCOL")
if DEFAULT_PROTOCOL is not None:
    # Get rid of the "://" part if it exists
    DEFAULT_PROTOCOL = DEFAULT_PROTOCOL.split("://")[0]

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
    macros : dict, optional
        A dictionary of macro variables to be forwarded to the display class
        being loaded.
    """
    # Instantiate our plugins.
    plugins = {plugin.protocol: plugin() for plugin in data_plugins.plugin_modules}

    # HACK. To be replaced with some stylesheet stuff eventually.
    alarm_severity_color_map = {
        0: QColor(0, 0, 0),  # NO_ALARM
        1: QColor(220, 220, 20),  # MINOR_ALARM
        2: QColor(240, 0, 0),  # MAJOR_ALARM
        3: QColor(240, 0, 240)  # INVALID_ALARM
    }

    # HACK. To be replaced with some stylesheet stuff eventually.
    connection_status_color_map = {
        False: QColor(255, 255, 255),
        True: QColor(0, 0, 0)
    }

    def __init__(self, ui_file=None, command_line_args=[], display_args=[], perfmon=False, hide_nav_bar=False, macros=None):
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
        self.directory_stack = ['']
        self.macro_stack = [{}]
        self.windows = {}
        self.display_args = display_args
        self.hide_nav_bar = hide_nav_bar
        # Open a window if one was provided.
        if ui_file is not None:
            self.make_window(ui_file, macros, command_line_args)
            self.had_file = True
        else:
            self.had_file = False
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

    def exec_(self):
        """
        Execute the QApplication.
        """
        # Connect to top-level widgets that were not loaded from file
        # These are usually testing/debug widgets
        if not self.had_file:
            self.make_connections()
        return super(PyDMApplication, self).exec_()


    @pyqtSlot()
    def get_CPU_usage(self):
        """
        Prints total CPU usage (in percent), as well as per-thread usage, to the terminal.
        """
        with self.perf.oneshot():
            total_percent = self.perf.cpu_percent(interval=None)
            total_time = sum(self.perf.cpu_times())
            usage = [total_percent * ((t.system_time + t.user_time) / total_time) for t in self.perf.threads()]
        print("Total: {tot}, Per Thread: {percpu}".format(tot=total_percent, percpu=usage))

    def make_connections(self):
        """
        Establish initial connections to all PyDM channels found while traversing
        the widget tree.
        """
        for widget in self.topLevelWidgets():
            self.establish_widget_connections(widget)

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
        path_and_args = shlex.split(str(ui_file))
        filepath = path_and_args[0]
        filepath_args = path_and_args[1:]
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
        if macros is not None:
            args.extend(["-m", json.dumps(macros)])
        args.append(filepath)
        args.extend(self.display_args)
        args.extend(filepath_args)
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

    def make_window(self, ui_file, macros=None, command_line_args=None):
        """
        Instantiate a new PyDMMainWindow, add it to the application's
        list of windows, and open the ui_file in the window.  Typically,
        this function is only called as part of starting up a new process,
        because PyDMApplications only have one window per process.
        
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
        main_window = PyDMMainWindow(hide_nav_bar=self.hide_nav_bar)
        main_window.open_file(ui_file, macros, command_line_args)
        main_window.show()
        self.windows[main_window] = os.path.dirname(ui_file)
        # If we are launching a new window, we don't want it to sit right on top of an existing window.
        if len(self.windows) > 1:
            main_window.move(main_window.x() + 10, main_window.y() + 10)

    def close_window(self, window):
        del self.windows[window]

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
        if macros is not None:
            f = macro.substitute_in_file(uifile, macros)
        else:
            f = uifile
        return uic.loadUi(f)

    def __sanity_check_pyqt(self, cls):
        for itm in dir(cls):
            i = getattr(cls, itm)
            if hasattr(i, "__file__"):
                if any([True if v in i.__file__ else False for v in ["PyQt4", "PyQt5"]]):
                    warnings.warn("Direct PyQt5/PyQt4 import detected. To ensure compatibility with PyQt4 and PyQt5 consider using: pydm.PyQt for your imports.", RuntimeWarning, stacklevel=0)
                    return

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

        # Now load the intelligence module.
        module = imp.load_source('intelclass', pyfile)
        self.__sanity_check_pyqt(module)
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

    def open_file(self, ui_file, macros=None, command_line_args=None):
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
        # First split the ui_file string into a filepath and arguments
        args = command_line_args if command_line_args is not None else []
        split = shlex.split(ui_file)
        filepath = split[0]
        args.extend(split[1:])
        self.directory_stack.append(os.path.dirname(filepath))
        (filename, extension) = os.path.splitext(filepath)
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
            raise ValueError("invalid file type: {}".format(extension))
        self.establish_widget_connections(widget)
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

    def open_relative(self, ui_file, widget, macros=None, command_line_args=[]):
        """
        open_relative opens a ui file with a relative path.  This is
        really only used by embedded displays.
        """
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
        """
        Given a PyDMChannel object, determine the appropriate plugin to use.
        
        Parameters
        ----------
        channel : PyDMChannel
        
        Returns
        -------
        PyDMPlugin
        """
        if channel.address is None or channel.address == "":
            return None
        match = re.match('.*://', channel.address)
        if match:
            protocol = match.group(0)[:-3]
        elif DEFAULT_PROTOCOL is not None:
            # If no protocol was specified, and the default protocol environment variable is specified, try to use that instead.
            protocol = DEFAULT_PROTOCOL
        try:
            plugin_to_use = self.plugins[str(protocol)]
            return plugin_to_use
        except KeyError:
            print("Couldn't find plugin for protocol: {0}".format(match.group(0)[:-3]))
        warnings.warn("Channel {addr} did not specify a valid protocol and no default protocol is defined.  This channel will receive no data.  To specify a default protocol, set the PYDM_DEFAULT_PROTOCOL environment variable.", RuntimeWarning, stacklevel=2)
        return None

    def add_connection(self, channel):
        """
        Add a new connection to a channel.
        
        Parameters
        ----------
        channel : PyDMChannel
        """
        plugin = self.plugin_for_channel(channel)
        if plugin:
            plugin.add_connection(channel)

    def remove_connection(self, channel):
        """
        Remove a connection to a channel.
        
        Parameters
        ----------
        channel : PyDMChannel
        """
        plugin = self.plugin_for_channel(channel)
        if plugin:
            plugin.remove_connection(channel)


    def eventFilter(self, obj, event):
        #Override the eventFilter to capture all middle mouse button events,
        #and show a tooltip if needed.
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.MiddleButton:
                self.show_address_tooltip(obj, event)
                return True
        return False

    # Not sure if showing the tooltip should be the job of the app,
    # may want to revisit this.
    def show_address_tooltip(self, obj, event):
        addr = obj.channels()[0].address
        QToolTip.showText(event.globalPos(), addr)
        # If the address has a protocol, and it is the default protocol, strip it out before putting it on the clipboard.
        m = re.match('(.+?):/{2,3}(.+?)$', addr)
        if m is not None and DEFAULT_PROTOCOL is not None and m.group(1) == DEFAULT_PROTOCOL:
            QApplication.clipboard().setText(m.group(2), mode=QClipboard.Selection)
        else:
            QApplication.clipboard().setText(addr, mode=QClipboard.Selection)

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
        """
        Given a widget to start from, traverse the tree of child widgets,
        and try to close connections to any widgets with channels.
        
        Parameters
        ----------
        widget : QWidget
        """
        widgets = [widget]
        widgets.extend(widget.findChildren(QWidget))
        for child_widget in widgets:
            try:
                if hasattr(child_widget, 'channels'):
                    for channel in child_widget.channels():
                        self.remove_connection(channel)
            except NameError:
                pass
