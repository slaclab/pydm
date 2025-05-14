from __future__ import annotations
import functools
import inspect
import logging
import os
import sys
import warnings
import subprocess
from functools import lru_cache
from io import StringIO
from os import path
from string import Template
from typing import Dict, Optional, Tuple

import re
import six
from qtpy.QtWidgets import QApplication, QWidget

from .help_files import HelpWindow
from .utilities import import_module_by_filename, is_pydm_app, macro, ACTIVE_QT_WRAPPER, QtWrapperTypes


if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYQT5:
    from qtpy import uic


class ScreenTarget:
    NEW_PROCESS = 0
    DIALOG = 1
    HOME = 2


logger = logging.getLogger(__file__)


def load_file(file, macros=None, args=None, target=ScreenTarget.NEW_PROCESS):
    """
    Load .ui, .py, or .adl screen file, perform macro substitution, then return
    the resulting QWidget.
    If target is specified, it will properly display the display file.

    Parameters
    ----------
    file : str
        The path to a screen file (.ui, .py, or .adl) to load.
    macros : dict, optional
        A dictionary of macro variables to supply to the
        loaded display subclass.
    args : list, optional
        A list of command-line arguments to pass to the
        loaded display subclass.
    target : int
        One of the ScreenTarget targets. PROCESS is only available when used
        with PyDM Application for now.

    Returns
    -------
    pydm.Display
    """
    if not is_pydm_app() and target == ScreenTarget.NEW_PROCESS:
        logger.warning("New Process is only valid with PyDM Application. " + "Falling back to ScreenTarget.DIALOG.")
        target = ScreenTarget.DIALOG

    if target == ScreenTarget.NEW_PROCESS:
        # Invoke PyDM to open a new process here.
        app = QApplication.instance()
        app.new_pydm_process(file, macros=macros, command_line_args=args)
        return None

    base, extension = os.path.splitext(file)
    loader = _extension_to_loader.get(extension, load_py_file)
    logger.debug("Loading %s file by way of %s...", file, loader.__name__)
    loaded_display = loader(file, args=args, macros=macros)

    if os.path.exists(base + ".txt"):
        loaded_display.load_help_file(base + ".txt")
    elif os.path.exists(base + ".html"):
        loaded_display.load_help_file(base + ".html")

    if target == ScreenTarget.DIALOG:
        loaded_display.show()

    return loaded_display


@lru_cache()
def _compile_ui_file(uifile: str) -> Tuple[str, str]:
    """
    Compile the ui file using uic and return the result as a string along with the associated class name.
    Caches the result to improve performance when the same ui file is reused many times within a display.

    Parameters
    ----------
    uifile : str
        The path to a .ui file to compile

    Returns
    -------
    Tuple[str, str] - The first element is the compiled ui file, the second is the name of the class (e.g. Ui_Form)
    """
    if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYQT5:
        code_string = StringIO()
        uic.compileUi(uifile, code_string)
        code_string = code_string.getvalue()
    elif ACTIVE_QT_WRAPPER == QtWrapperTypes.PYSIDE6:
        # seems like pyside6 only offers .ui compilation with pyside6-uic cmdline tool
        try:
            result = subprocess.run(
                ["pyside6-uic", uifile],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            code_string = result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error compiling {uifile} with pyside6-uic: {e.stderr.strip()}") from e

    # Grabs non-whitespace characters between class and the opening parenthesis
    class_name_match = re.search(r"^class\s*(\S*)\(", code_string, re.MULTILINE)
    if not class_name_match:
        raise ValueError("Unable to determine the class name from the compiled .ui file.")
    class_name = class_name_match.group(1)

    return code_string, class_name


def _load_ui_into_display(uifile, display):
    if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYQT5:
        klass, _ = uic.loadUiType(uifile)
    else:  # pyside6
        from PySide6.QtUiTools import loadUiType

        klass, _ = loadUiType(uifile)

    # Python 2.7 compatibility. More info at the following links:
    # https://github.com/universe-proton/universe-topology/issues/3
    # https://stackoverflow.com/questions/3296993/python-how-to-call-unbound-method-with-other-type-parameter
    retranslateUi = six.get_unbound_function(klass.retranslateUi)
    setupUi = six.get_unbound_function(klass.setupUi)
    # Add retranslateUi to Display class
    display.retranslateUi = functools.partial(retranslateUi, display)
    setupUi(display, display)

    display.ui = display


def clear_compiled_ui_file_cache() -> None:
    """
    Clears the cache of compiled ui files. Needed if changes to the underlying ui files have been made on disk and
    need to be picked up, such as the user choosing to reload the display.
    """
    _compile_ui_file.cache_clear()


def _load_compiled_ui_into_display(
    code_string: str, class_name: str, display: Display, macros: Optional[Dict[str, str]] = None
) -> None:
    """
    Takes a ui file which has already been compiled by uic and loads it into the input display.
    Performs macro substitution within the input code_string if any macros supplied are
    found within the code string.

    Parameters
    ----------
    code_string : str
        The pre-compiled ui file to load
    class_name : str
        The name of the class that methods will be executed on
    display : Display
        The display which the ui file is being loaded into
    macros : Optional[Dict[str, str]]
        Macros to be substituted
    """
    if macros:
        code_string = macro.replace_macros_in_template(Template(code_string), macros).getvalue()
    # Create and grab the class described by the compiled ui file
    ui_globals = {}
    exec(code_string, ui_globals)
    klass = ui_globals[class_name]

    # Add retranslateUi to Display class
    display.retranslateUi = functools.partial(klass.retranslateUi, display)
    klass.setupUi(display, display)

    display.ui = display


def load_ui_file(uifile, macros=None, args=None):
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
    args : list, optional
        This is ignored for UI files.

    Returns
    -------
    QWidget
    """

    display = Display(macros=macros)
    display.load_ui_from_file(uifile, macros)
    return display


def load_adl_file(filename, macros=None, args=None):
    """
    Load an MEDM ADL display with adl2pydm.

    Parameters
    ----------
    filename : str
        The ADL file path.

    macros : dict, optional
        A dictionary of macro variables to supply to the loaded display
        subclass.

    args : any, optional
        Ignored for load_adl_file.
    """
    try:
        import adl2pydm  # noqa: F401
        from adl2pydm import adl_parser, output_handler
    except ImportError:
        raise RuntimeError("Sorry, adl2pydm is not installed.")

    screen = adl_parser.MedmMainWidget(filename)
    buf = screen.getAdlLines(filename)
    screen.parseAdlBuffer(buf)

    writer = output_handler.Widget2Pydm()
    writer.write_ui(screen, None)
    ui_contents = writer.writer.generate_ui_contents()

    d = Display(macros=macros)
    d._loaded_file = filename

    fp = macro.replace_macros_in_template(Template(ui_contents), macros or {})
    _load_ui_into_display(fp, d)
    fp.close()
    return d


def load_py_file(pyfile, args=None, macros=None):
    """
    Load a .py file, performs some sanity checks to try and determine
    if the file actually contains a valid PyDM Display subclass, and if
    the checks pass, create and return an instance.

    This is an internal method, users will usually want to use `open_file` instead.

    Parameters
    ----------
    pyfile : str
        The path to a .py file to load.
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
    # Add the intelligence module directory to the python path, so that
    # submodules can be loaded.
    # Eventually, this should go away, and intelligence modules should behave
    # as real python modules.
    module = import_module_by_filename(os.path.abspath(pyfile))

    if hasattr(module, "intelclass"):
        cls = module.intelclass
        if not issubclass(cls, Display):
            raise ValueError(
                "Invalid class definition at file {}. {} does not inherit from Display. "
                "Nothing to open at this time.".format(pyfile, cls.__name__)
            )
    else:
        classes = [
            obj
            for name, obj in inspect.getmembers(module)
            if inspect.isclass(obj) and issubclass(obj, Display) and obj != Display
        ]
        if len(classes) == 0:
            raise ValueError(
                "Invalid File Format. {} has no class inheriting from Display. Nothing to open at this time.".format(
                    pyfile
                )
            )
        if len(classes) > 1:
            warnings.warn(
                "More than one Display class in file {}. "
                "The first occurrence (in alphabetical order) will be opened: {}".format(pyfile, classes[0].__name__),
                RuntimeWarning,
                stacklevel=2,
            )
        cls = classes[0]

    module_params = inspect.signature(cls).parameters

    # Because older versions of Display may not have the args parameter or the macros parameter, we check
    # to see if it does before trying to use them.
    kwargs = {}
    if "args" in module_params:
        kwargs["args"] = args
    if "macros" in module_params:
        kwargs["macros"] = macros
    instance = cls(**kwargs)
    instance._loaded_file = pyfile
    return instance


_extension_to_loader = {
    ".ui": load_ui_file,
    ".py": load_py_file,
    ".adl": load_adl_file,
}


class Display(QWidget):
    def __init__(self, parent=None, args=None, macros=None, ui_filename=None):
        super().__init__(parent)
        self.ui = None
        self.help_window = None
        self._ui_filename = ui_filename
        self._loaded_file = None
        self._args = args
        self._macros = macros
        self._previous_display = None
        self._next_display = None
        self._local_style = ""
        if ui_filename or self.ui_filename():
            self.load_ui(macros=macros)

    def loaded_file(self):
        return self._loaded_file

    @property
    def previous_display(self):
        return self._previous_display

    @previous_display.setter
    def previous_display(self, display):
        self._previous_display = display

    @property
    def next_display(self):
        return self._next_display

    @next_display.setter
    def next_display(self, display):
        self._next_display = display

    def menu_items(self):
        """Returns a dictionary where the keys are the names of the menu entries,
        and the values are callables, where the callable is the action performed
        when the menu item is selected.

        Submenus are supported by using a similarly structured dictionary as the value.

        Shortcuts are supported by using a tuple of type (callable, shortcut_string) as the value.

        Users will want to overload this function in their Display subclass to return
        their custom menu.

        Example:

        return {"Action 1": self.action1, "Submenu": {"Action 2" self.action2},
        "Action 3": (self.action3, "Ctrl+A")}

        """
        return {}

    def file_menu_items(self):
        """Returns a dictionary accepting a protected set of keys corresponding to one or more
        possible default actions in the "File" menu, with the values as callables, where the callable
        is the action performed when the menu item is selected.

        Allowed keys are: ("save", "save_as", "load")

        Shortcuts are supported by using a tuple of type (callable, shortcut_string) as the value.

        Users will want to overload this function in their Display subclass to return
        custom file menu actions.

        Example:

        return {"save": self.save_function, "save_as": self.save_as_function,
        "load": (self.load_function, "Ctrl+L")}

        """
        return {}

    def show_help(self) -> None:
        """Show the associated help file for this display"""
        if self.help_window is not None:
            self.help_window.show()

    def navigate_back(self):
        pass

    def navigate_forward(self):
        pass

    def macros(self):
        if self._macros is None:
            return {}
        return self._macros

    def args(self):
        return self._args

    def ui_filepath(self):
        """Returns the path to the ui file relative to the file of the class
        calling this function."""
        if not self.ui_filename():
            return None
        path_to_class = sys.modules[self.__module__].__file__
        return path.join(path.dirname(path.realpath(path_to_class)), self.ui_filename())

    def ui_filename(self):
        """Returns the name of the ui file.  In modern PyDM, it is preferable
        specify this via the ui_filename argument in Display's constructor,
        rather than reimplementing this in Display subclasses."""
        if self._ui_filename is None:
            return None
        else:
            return self._ui_filename

    def load_ui(self, macros=None):
        """Load and parse the ui file, and make the file's widgets available
        in self.ui.  Called by the initializer."""
        if self.ui:
            return self.ui
        if self.ui_filepath() is not None and self.ui_filepath() != "":
            self.load_ui_from_file(self.ui_filepath(), macros)

    def load_ui_from_file(self, ui_file_path: str, macros: Optional[Dict[str, str]] = None):
        """Load the ui file from the input path, and make the file's widgets available in self.ui"""
        self._loaded_file = ui_file_path
        code_string, class_name = _compile_ui_file(ui_file_path)
        _load_compiled_ui_into_display(code_string, class_name, self, macros)

    def load_help_file(self, file_path: str) -> None:
        """Loads the input help file into a window for display"""
        self.help_window = HelpWindow(file_path)

    def setStyleSheet(self, new_stylesheet):
        # Handle the case where the widget's styleSheet property contains a filename, rather than a stylesheet.
        possible_stylesheet_filename = os.path.expanduser(os.path.expandvars(new_stylesheet))
        logger.debug("Calling Display.setStyleSheet, new_stylesheet is %s", possible_stylesheet_filename)
        stylesheet_filename = None
        try:
            # First, check if the file is already an absolute path.
            if os.path.isfile(possible_stylesheet_filename):
                stylesheet_filename = possible_stylesheet_filename
            # Second, check if the css file is specified relative to the display file.
            else:
                rel_path = os.path.join(
                    os.path.dirname(os.path.abspath(self._loaded_file)), possible_stylesheet_filename
                )
                if os.path.isfile(rel_path):
                    stylesheet_filename = rel_path
        except Exception as e:
            logger.debug("Exception while checking if stylesheet is a filename: %s", e)
            pass
        self._local_style = new_stylesheet
        if stylesheet_filename is not None:
            logger.debug("styleSheet property contains a filename, loading %s", stylesheet_filename)
            with open(stylesheet_filename) as f:
                self._local_style = f.read()
        logger.debug("Setting stylesheet to: %s", self._local_style)
        super().setStyleSheet(self._local_style)
