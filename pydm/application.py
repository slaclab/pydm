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
import re
import shlex
import json
import inspect
import logging
import warnings
import platform
import collections
from functools import partial
from .display_module import Display
from qtpy.QtCore import Qt, QEvent, QTimer, Slot
from qtpy.QtWidgets import QApplication, QWidget, QToolTip, QAction, QMenu
from qtpy.QtGui import QClipboard, QColor
from qtpy import uic
from .main_window import PyDMMainWindow
from .tools import ExternalTool

from .utilities import macro, which, path_info, find_display_in_path
from .utilities.stylesheet import apply_stylesheet
from . import data_plugins
from .widgets.rules import RulesDispatcher

logger = logging.getLogger(__name__)
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
    tools = dict()

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
        self.main_window = None
        self.directory_stack = ['']
        self.macro_stack = [{}]
        self.windows = {}
        self.display_args = display_args
        self.hide_nav_bar = hide_nav_bar
        self.hide_menu_bar = hide_menu_bar
        self.hide_status_bar = hide_status_bar
        self.fullscreen = fullscreen
        self.__read_only = read_only

        # Open a window if required.
        if ui_file is not None:
            apply_stylesheet(stylesheet_path)
            self.make_main_window()
            self.make_window(ui_file, macros, command_line_args)
        elif use_main_window:
            self.make_main_window()

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
        return self.__read_only

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

    def make_main_window(self):
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
        if self.fullscreen:
            main_window.enter_fullscreen()
        else:
            main_window.show()

        self.load_external_tools()
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

    def open_file(self, ui_file, macros=None, command_line_args=None,
                  establish_connection=True):
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
        establish_connection : bool, optional
            Whether or not we should call `establish_widget_connections` for this
            new widget. Default is True.

        Returns
        -------
        QWidget
        """
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
        if establish_connection:
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

    def open_relative(self, ui_file, widget, macros=None, command_line_args=[],
                      establish_connection=True):
        """
        open_relative opens a ui file with a relative path.  This is
        really only used by embedded displays.
        """
        full_path = self.get_path(ui_file)

        if not os.path.exists(full_path):
            new_fname = find_display_in_path(ui_file)
            if new_fname is not None and new_fname != "":
                full_path = new_fname
        return self.open_file(full_path, macros=macros,
                              command_line_args=command_line_args,
                              establish_connection=establish_connection)

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
        protocol = None
        match = re.match('.*://', channel.address)
        if match:
            protocol = match.group(0)[:-3]
        elif DEFAULT_PROTOCOL is not None:
            # If no protocol was specified, and the default protocol environment variable is specified, try to use that instead.
            protocol = DEFAULT_PROTOCOL
        if protocol:
            try:
                plugin_to_use = self.plugins[str(protocol)]
                return plugin_to_use
            except KeyError:
                print("Couldn't find plugin for protocol: {0}".format(match.group(0)[:-3]))
        #If you get this far, we didn't successfuly figure out what plugin to use for this channel.
        logger.warning(
            "Channel {addr} did not specify a valid protocol and no default "
            "protocol is defined.  This channel will receive no data. To "
            "specify a default protocol, set the PYDM_DEFAULT_PROTOCOL "
            "environment variable.".format(addr=channel.address)
        )
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
        # Override the eventFilter to capture all middle mouse button events,
        # and show a tooltip if needed.
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.MiddleButton:
                self.show_address_tooltip(obj, event)
                return True
        return False

    # Not sure if showing the tooltip should be the job of the app,
    # may want to revisit this.
    def show_address_tooltip(self, obj, event):
        if not len(obj.channels()):
            logger.warning("Object %r has no PyDM Channels", obj)
            return
        addr = obj.channels()[0].address
        QToolTip.showText(event.globalPos(), addr)
        # If the address has a protocol, and it is the default protocol, strip it out before putting it on the clipboard.
        m = re.match('(.+?):/{2,3}(.+?)$', addr)
        if m is not None and DEFAULT_PROTOCOL is not None and m.group(1) == DEFAULT_PROTOCOL:
            copy_text = m.group(2)
        else:
            copy_text = addr

        clipboard = QApplication.clipboard()
        clipboard.setText(copy_text)
        event = QEvent(QEvent.Clipboard)
        self.sendEvent(clipboard, event)

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

    def unregister_widget_rules(self, widget):
        """
        Given a widget to start from, traverse the tree of child widgets,
        and try to unregister rules to any widgets.

        Parameters
        ----------
        widget : QWidget
        """
        widgets = [widget]
        widgets.extend(widget.findChildren(QWidget))
        for child_widget in widgets:
            try:
                if hasattr(child_widget, 'rules'):
                    if child_widget.rules:
                        RulesDispatcher().unregister(child_widget)
            except:
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

    def list_all_connections(self):
        """
        List all the connections for all the data plugins.

        Returns
        -------
        list of connections
        """
        conns = []
        for p in self.plugins.values():
            for connection in p.connections.values():
                conns.append(connection)
        return conns

    def load_external_tools(self):
        """
        Loads all the external tools available at the given
        `PYDM_TOOLS_PATH` environment variable and subfolders that
        follows the `*_tool.py` and have classes that inherits from
        the `pydm.tools.ExternalTool` class.
        """
        EXT_TOOLS_TOKEN = "_tool.py"
        path = os.getenv("PYDM_TOOLS_PATH", None)

        logger.info("*"*80)
        logger.info("* Loading PyDM External Tools")
        logger.info("*"*80)

        if path is not None:
            logger.info("Looking for external tools at: {}".format(path))
            if platform.system() == "Windows":
                locations = path.split(";")
            else:
                locations = path.split(":")
            for loc in locations:
                for root, _, files in os.walk(loc):
                    for name in files:
                        if name.endswith(EXT_TOOLS_TOKEN):
                            self.install_external_tool(os.path.join(root, name))
        else:
            logger.warning("External Tools not loaded. No External Tools Path specified.")

    def install_external_tool(self, tool):
        """
        Install an External Tool at the PyDMApplication and add it to the
        main window Tools menu.

        Parameters
        ----------
        tool : str or pydm.tools.ExternalTool
            The full path to a file containing a ExternalTool definition
            or an Instance of an ExternalTool.
        """

        def reorder_tools_dict():
            self.tools = collections.OrderedDict(sorted(self.tools.items()))
            for k in self.tools.keys():
                if isinstance(self.tools[k], dict):
                    self.tools[k] = collections.OrderedDict(sorted(self.tools[k].items()))

        try:
            if isinstance(tool, str):
                base_dir, _, _ = path_info(tool)
                sys.path.append(base_dir)
                temp_name = str(uuid.uuid4())

                module = imp.load_source(temp_name, tool)
                classes = [obj for _, obj in inspect.getmembers(module)
                           if inspect.isclass(obj) and issubclass(obj, ExternalTool) and obj != ExternalTool]
                if len(classes) == 0:
                    raise ValueError("Invalid File Format. {} has no class inheriting from ExternalTool. Nothing to open at this time.".format(tool))
                obj = [c() for c in classes]
            elif isinstance(tool, ExternalTool):
                # The actual tool to be installed...
                obj = [tool]
            else:
                raise ValueError("Invalid argument for parameter 'tool'. String or ExternalTool expected.")

            for o in obj:
                if o.group is not None and o.group != "":
                    if o.group not in self.tools:
                        self.tools[o.group] = dict()
                    self.tools[o.group][o.name] = o
                else:
                    self.tools[o.name] = o

            reorder_tools_dict()
            kwargs = {'channels': None, 'sender': self.main_window}
            self.assemble_tools_menu(self.main_window.ui.menuTools, clear_menu=True, **kwargs)
        except Exception as e:
            print("Failed to load External Tool: ", tool, ". Exception was: ", str(e))

    def assemble_tools_menu(self, parent_menu, clear_menu=False, widget_only=False, **kwargs):
        """
        Assemble the Tools menu for a given parent menu.

        Parameters
        ----------
        parent_menu : QMenu
            The main menu item to hold the tools menu tree.
        clear_menu : bool
            Whether of not we should clear the menu before adding the tools.
        widget_only : bool
            Whether or not generate only the menu for widgets compatible
            tools. This should be True when creating the menu for the
            PyDMWidgets and False for most of the other cases.
        kwargs : dict
            Parameters sent directly to the `call` method of the ExternalTool
            instance. In general this dict is composed by `channels` which
            is a list and `sender` which is a QWidget.

        """
        def assemble_action(menu, tool_obj):
            if tool_obj.icon is not None:
                action = menu.addAction(tool_obj.name)
                action.setIcon(tool_obj.icon)
            else:
                action = menu.addAction(tool_obj.name)
            action.triggered.connect(partial(tool_obj.call, **kwargs))

        if clear_menu:
            parent_menu.clear()
        else:
            parent_menu.addSeparator()

        for k, v in self.tools.items():
            if isinstance(v, dict):
                m = QMenu(k, parent=parent_menu)
                should_create_menu = False
                for _, t in v.items():
                    if widget_only and not t.use_with_widgets:
                        continue
                    assemble_action(m, t)
                    should_create_menu = True
                if should_create_menu:
                    parent_menu.addMenu(m)
            else:
                if widget_only and not v.use_with_widgets:
                        continue
                assemble_action(parent_menu, v)

        if not widget_only:
            parent_menu.addSeparator()
            parent_menu.addAction(self.main_window.ui.actionLoadTool)
