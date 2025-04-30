import collections
import functools
import importlib
import importlib.util
import logging
import ntpath
import os
import platform
import shlex
import sys
import time
import types
import uuid
import errno

from typing import List, Optional
from enum import IntEnum

from qtpy import QtCore, QtGui, QtWidgets

from . import colors, macro, shortcuts
from .connection import close_widget_connections, establish_widget_connections
from .iconfont import IconFont
from .remove_protocol import protocol_and_address, remove_protocol, parsed_address
from .units import convert, find_unit_options, find_unittype

__all__ = [
    "colors",
    "macro",
    "shortcuts",
    "close_widget_connections",
    "establish_widget_connections",
    "IconFont",
    "protocol_and_address",
    "remove_protocol",
    "BasicURI",
    "parsed_address",
    "convert",
    "find_unit_options",
    "find_unittype",
]

logger = logging.getLogger(__name__)


# The qtpy abstraction layer decides which qt python wrapper to use by the QT_API environment variable.
# Currently, we only intend for PyDM to support PyQt5 (legacy) and PySide6.
# ACTIVE_QT_WRAPPER is implemented for easier access to the QT_API env variable,
# since we need to know which wrapper is currently being used to support both pyqt5 and pyside6.
class QtWrapperTypes(IntEnum):
    UNSUPPORTED = 0
    PYSIDE6 = 1
    PYQT5 = 2


ACTIVE_QT_WRAPPER = QtWrapperTypes.UNSUPPORTED

# QT_API should be set according to the qtpy docs: https://github.com/spyder-ide/qtpy?tab=readme-ov-file#requirements
qt_api = os.getenv("QT_API", "").lower()
if qt_api == "pyside6":
    ACTIVE_QT_WRAPPER = QtWrapperTypes.PYSIDE6
elif qt_api == "pyqt5":
    ACTIVE_QT_WRAPPER = QtWrapperTypes.PYQT5

if ACTIVE_QT_WRAPPER == QtWrapperTypes.UNSUPPORTED:
    error_message = (
        "The QT_API variable is not set to a supported Qt Python wrapper "
        "(PySide6 or PyQt5). Please set QT_API to 'pyside6' or 'pyqt5'."
    )
    logger.error(error_message)
    raise RuntimeError(error_message)


def is_ssh_session():
    """
    Whether or not this is a SSH session.

    Returns
    -------
    bool
        True if it is a ssh session, False otherwise.
    """
    return os.getenv("SSH_CONNECTION") is not None


def setup_renderer():
    """
    This utility function reverts the renderer to Software rendering if it is
    running in a SSH session.
    """
    if is_ssh_session():
        logger.info("Using PyDM via SSH. Reverting to Software Rendering.")
        from qtpy.QtCore import QCoreApplication, Qt
        from qtpy.QtQuick import QQuickWindow, QSGRendererInterface

        QCoreApplication.setAttribute(Qt.AA_UseSoftwareOpenGL)
        QQuickWindow.setSceneGraphBackend(QSGRendererInterface.Software)


def is_pydm_app(app=None):
    """
    Check whether or not `QApplication.instance()` is a PyDMApplication.

    Parameters
    ----------
    app : QApplication, Optional
        The app to inspect. If no application is provided the current running `QApplication` will be queried.

    Returns
    -------
    bool
        True if it is a PyDMApplication, False otherwise.
    """
    from qtpy.QtWidgets import QApplication

    from pydm.application import PyDMApplication

    if app is None:
        app = QApplication.instance()
    if isinstance(app, PyDMApplication):
        return True
    else:
        return False


def is_qt_designer():
    """
    Check whether or not running inside Qt Designer.

    Returns
    -------
    bool
        True if inside Designer, False otherwise.
    """
    from pydm.qtdesigner import DesignerHooks

    return DesignerHooks().form_editor is not None


def get_designer_current_path():
    """
    Fetch the absolute path for the current active form at Qt Designer.

    Returns
    -------
    path : str, None
        The absolute path for the current active form or None in case not
        available
    """
    if not is_qt_designer():
        return None

    from pydm.qtdesigner import DesignerHooks

    form_editor = DesignerHooks().form_editor
    win_manager = form_editor.formWindowManager()
    form_window = win_manager.activeFormWindow()
    if form_window is None and win_manager.formWindowCount() > 0:
        form_window = win_manager.formWindow(0)
    if form_window is not None:
        abs_dir = form_window.absoluteDir()
        if abs_dir:
            return abs_dir.absolutePath()

    return None


def path_info(path_str):
    """
    Retrieve basic information about the given path.

    Parameters
    ----------
    path_str : str
        The path from which to extract information.

    Returns
    -------
    tuple
        base dir, file name, list of args
    """
    if platform.system() == "Windows":
        os_path_mod = ntpath
    else:
        os_path_mod = os.path

    dir_name, other_parts = os_path_mod.split(path_str)
    split = shlex.split(other_parts)
    file_name = split.pop(0)
    args = split

    return dir_name, file_name, args


def _extensions(fname):
    name = os.path.basename(fname)
    MAX_ITER = 10
    exts = []
    for i in range(MAX_ITER):
        new_name, ext = os.path.splitext(name)
        if ext:
            exts.insert(0, ext)
        if name == new_name:
            break
        name = new_name
    return exts


def _screen_file_extensions(preferred_extension):
    """
    Return a prioritized list of screen file extensions.

    Include .ui & .py files (also .adl files if adl2pydm installed).
    Prefer extension as described by fname.
    """
    extensions = [".py", ".ui"]  # search for screens with these extensions
    try:
        import adl2pydm  # proceed only if package is importable  # noqa: F401

        extensions.append(".adl")
    except ImportError:
        pass

    # don't search twice for preferred extension
    if preferred_extension in extensions:
        extensions.remove(preferred_extension)

    # search first for preferred extension
    extensions.insert(0, preferred_extension)
    return extensions


def find_file(
    fname,
    base_path=None,
    mode=None,
    raise_if_not_found=False,
    subdir_scan_enabled=False,
    subdir_scan_base_path_only=True,
):
    """
    Look for files at the search paths common to PyDM.

    The search order is as follows:

    * The ``base_path`` argument
    * Qt Designer Path - the path for the current form as reported by the
      designer
    * The current working directory
    * Directories listed in the environment variable ``PYDM_DISPLAYS_PATH``

    Parameters
    ----------
    fname : str
        The file name. Environment variables, ~ and ~user constructs before
        search.
    base_path : str
        The directory name of a file pathname from a display, if any
    mode : int
        The mode required for the file, defaults to os.F_OK | os.R_OK.
        Which ensure that the file exists and we can read it.
    raise_if_not_found : bool
        Flag which if False will add a check that raises a FileNotFoundError
        instead of returning None when the file is not found.
    subdir_scan_enabled : bool
        If the file cannot be found in the given directories, check
        subdirectories. Defaults to False.
    subdir_scan_base_path_only : bool
        If it is necessary to scan subdirectories for the requested file,
        only scan subdirectories of the base_path. Defaults to True.

    Returns
    -------
    file_path : str
        Returns the file path or None in case the file was not found
    """
    fname = os.path.expanduser(os.path.expandvars(fname))

    if mode is None:
        mode = os.F_OK | os.R_OK

    x_path = collections.deque()

    if base_path:
        base_path = os.path.abspath(base_path)
        x_path.append(base_path)

    if is_qt_designer():
        designer_path = get_designer_current_path()
        if designer_path:
            x_path.append(designer_path)

    # Current working directory
    x_path.append(os.getcwd())

    pydm_search_path = os.getenv("PYDM_DISPLAYS_PATH", None)
    if pydm_search_path:
        x_path.extend(pydm_search_path.split(os.pathsep))

    for idx, path in enumerate(x_path):
        x_path[idx] = os.path.expanduser(os.path.expandvars(path))

    root, ext = os.path.splitext(fname)

    # 3 seconds should be more than generous enough
    SUBDIR_SCAN_TIME_LIMIT = 3
    start_time = time.perf_counter()

    file_path = None
    while file_path is None and len(x_path) > 0:
        # Loop through the possible screen file extensions
        for e in _screen_file_extensions(ext):
            file_path = which(str(root) + str(e), mode=mode, pathext=e, extra_path=x_path)
            if file_path is not None:
                break  # pick the first screen file found

        if not subdir_scan_enabled or time.perf_counter() - start_time >= SUBDIR_SCAN_TIME_LIMIT:
            if not file_path and raise_if_not_found:
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), fname)
            break

        # Only search recursively under base path
        if subdir_scan_base_path_only:
            if base_path is None or len(base_path) == 0:
                break
            x_path.clear()
            x_path.append(os.path.expanduser(os.path.expandvars(base_path)))
            # Prevent entering this block again
            subdir_scan_base_path_only = False

        # This might get large in some situations, but it's the easiest way to do BFS without
        # changing too much of the existing logic, and ideally recursion isn't needed
        path_count = len(x_path)
        for _ in range(path_count):
            for subdir in os.listdir(x_path[0]):
                if subdir.startswith(".") or subdir.startswith("__pycache__"):
                    continue
                new_path = os.path.join(x_path[0], subdir)
                if os.path.isdir(new_path):
                    x_path.append(new_path)
            x_path.popleft()

    return file_path


def find_display_in_path(file, mode=None, path=None, pathext=None):
    """
    Look for a display file in a given path.
    This is basically a wrapper on top of the ``which``
    command defined below so we don't need to keep redefining
    the ``PYDM_DISPLAYS_PATH`` variable.

    Parameters
    ----------
    file : str
        The file name.
    mode : int
        The mode required for the file, defaults to os.F_OK | os.R_OK.
        Which ensure that the file exists and we can read it.
    path : str
        The PATH string.

    Returns
    -------
    str
        Returns the full path to the file or None in case it was not found.
    """
    if pathext is None and sys.platform == "win32":
        pathext = ".ui"
    if path is None:
        path = os.getenv("PYDM_DISPLAYS_PATH", None)
    if mode is None:
        mode = os.F_OK | os.R_OK

    return which(file, mode, path, pathext=pathext)


def which(cmd, mode=os.F_OK | os.X_OK, path=None, pathext=None, extra_path=None):
    """Given a command, mode, and a PATH string, return the path which
    conforms to the given mode on the PATH, or None if there is no such
    file.
    `mode` defaults to os.F_OK | os.X_OK. `path` defaults to the result
    of os.environ.get("PATH"), or can be overridden with a custom search
    path.
    Note: This function was backported from the Python 3 source code and modified
    to deal with the case in which we WANT to look at the path even with a relative
    path.
    """

    # Check that a given file can be accessed with the correct mode.
    # Additionally check that `file` is not a directory, as on Windows
    # directories pass the os.access check.
    def _access_check(fn, mode):
        return os.path.exists(fn) and os.access(fn, mode) and not os.path.isdir(fn)

    # If we're given a path with a directory part, look it up directly
    # rather than referring to PATH directories. This includes checking
    # relative to the current directory, e.g. ./script
    # if os.path.dirname(cmd):
    #     if _access_check(cmd, mode):
    #         return cmd
    #     return None

    if path is None:
        path = os.environ.get("PATH", os.defpath)
    if not path:
        return None
    path = path.split(os.pathsep)

    if sys.platform == "win32":
        # The current directory takes precedence on Windows.
        if os.curdir not in path:
            path.insert(0, os.curdir)

        # PATHEXT is necessary to check on Windows.
        if pathext is None:
            pathext = os.environ.get("PATHEXT", "")
        pathext = pathext.split(os.pathsep)
        # See if the given file matches any of the expected path
        # extensions. This will allow us to short circuit when given
        # "python.exe". If it does match, only test that one, otherwise we
        # have to try others.
        if any(cmd.lower().endswith(ext.lower()) for ext in pathext):
            files = [cmd]
        else:
            files = [cmd + ext for ext in pathext]
    else:
        # On other platforms you don't have things like PATHEXT to tell you
        # what file suffixes are executable, so just pass on cmd as-is.
        files = [cmd]

    seen = set()
    for paths in extra_path, path:
        if paths is None:
            continue
        for dir_ in paths:
            normdir = os.path.normcase(dir_)
            if normdir not in seen:
                seen.add(normdir)
                for thefile in files:
                    name = os.path.join(dir_, thefile)
                    if _access_check(name, mode):
                        return name
    return None


def only_main_thread(func):
    """
    Decorator that wraps a function which should only be executed at the Qt
    main thread.

    The decorator will log an error message and raise a RuntimeError if the
    decorated function is invoked from a thread other than the Qt main one.

    Parameters
    ----------
    func : callable
        The function to wrap

    Returns
    -------
    wrapper
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        main_t = QtWidgets.QApplication.instance().thread()
        curr_t = QtCore.QThread.currentThread()
        if curr_t != main_t:
            msg = "{}.{} can only be invoked from the main Qt thread.".format(func.__module__, func.__name__)
            logger.error(msg)
            raise RuntimeError(msg)
        return func(*args, **kwargs)

    if not callable(func):
        raise ValueError("Parameter must be a callable.")

    return wrapper


def log_failures(
    logger: logging.Logger,
    explanation: str = "Failed to run {func.__name__}",
    include_traceback: bool = False,
    level: int = logging.WARNING,
):
    """
    Decorator that wraps a function to be run.

    Exceptions raised while executing that function will be logged.
    In case of an exception, the wrapper will return ``None``.

    Parameters
    ----------
    logger : logging.Logger
        The logger instance to log messages to.
    explanation : str, optional
        The explanation message to include.  Format arguments include:
            ``func``, ``args``, ``kwargs``, and the exception ``ex``.
    include_traceback : bool, optional
        Include traceback information in the log message.
    level : int, optional
        Logging level to use.
    """

    def wrapper(func: callable):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                msg = explanation.format(func=func, args=args, kwargs=kwargs, ex=ex)
                if include_traceback:
                    logger.log(level, msg, exc_info=ex)
                else:
                    logger.log(level, msg)
                return None

        return wrapped

    return wrapper


def import_module_by_filename(source_filename: str, *, add_to_modules: bool = True) -> types.ModuleType:
    """
    For a given source filename, import it and search for objects.

    Parameters
    ----------
    source_filename : str
        The source code filename.

    add_to_modules : bool, optional, keyword-only
        Add the imported module to ``sys.modules``.  Defaults to ``True``.

    Returns
    -------
    module : types.ModuleType
        The imported module.
    """
    module_dir = os.path.dirname(os.path.abspath(source_filename))
    if module_dir not in sys.path:
        sys.path.append(module_dir)

    module_name = str(uuid.uuid4())
    spec = importlib.util.spec_from_file_location(module_name, source_filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if add_to_modules:
        sys.modules[module_name] = module
    return module


def get_clipboard() -> Optional[QtGui.QClipboard]:
    """Get the clipboard instance. Requires a QApplication."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        return None

    return QtWidgets.QApplication.clipboard()


def get_clipboard_modes() -> List[int]:
    """
    Get the clipboard modes for the current platform.

    Returns
    -------
    list of int
        Qt-specific modes to try for interacting with the clipboard.
    """
    clipboard = get_clipboard()
    if clipboard is None:
        return []

    if platform.system() == "Linux":
        # Mode selection is only valid for X11.
        return [QtGui.QClipboard.Selection, QtGui.QClipboard.Clipboard]

    return [QtGui.QClipboard.Clipboard]


def copy_to_clipboard(text: str, *, quiet: bool = False):
    """
    Copy ``text`` to the clipboard.

    Parameters
    ----------
    text : str
        The text to copy to the clipboard.

    quiet : bool, optional, keyword-only
        If quiet is set, do not log the copied text.  Defaults to False.
    """
    clipboard = get_clipboard()
    if clipboard is None:
        return None

    for mode in get_clipboard_modes():
        clipboard.setText(text, mode=mode)
        event = QtCore.QEvent(QtCore.QEvent.Clipboard)
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.sendEvent(clipboard, event)

    if not quiet:
        logger.warning(("Copied text to clipboard:\n-------------------------\n%s\n-------------------------\n"), text)


def get_clipboard_text() -> str:
    """
    Get ``text`` from the clipboard. If unavailable or unset, empty string.

    Returns
    -------
    str
        The clipboard text, if available.
    """
    clipboard = get_clipboard()
    if clipboard is None:
        return ""
    for mode in get_clipboard_modes():
        text = clipboard.text(mode=mode)
        if text:
            return text
    return ""


def checkObjectProperties(class_object, extra_properties):
    """
    Check that an object has the expected RULE_PROPERTIES map.
    This function should only be used on objects derived from PyDMWidget and
    therefore PyDMPrimitiveWidget (which defines the RULE_PROPERTIES).
    The expected properties are the base properties of PyDMWidget and any extra ones applied to the subclass.

    Parameters
    ----------
    class_object : Type[PyDMWidget]
        The object to check the properties of.

    extra_properties : dict
        Map of the additional properties we expect applied to the class_object.
        These should be only the extra props applied to the derived class itself,
        not including the props applied to PyDMWidget and PyDMPrimitiveWidget.
    """

    # Properties that all PyDMWidget derived objects should all have, since they are applied
    # at the definition of PyDMWidget and PyDMPrimitiveWidget classes.
    pydm_widget_props = {
        "Enable": ["setEnabled", bool],
        "Visible": ["setVisible", bool],
        "Opacity": ["set_opacity", float],
        "Position - X": ["setX", int],
        "Position - Y": ["setY", int],
    }

    # Combine the properties into one map
    pydm_widget_props.update(extra_properties)

    # Check if object's properties are as expected
    for key, value in pydm_widget_props.items():
        if key not in class_object.RULE_PROPERTIES:
            print("Missing property: ", key)
            return False
        if class_object.RULE_PROPERTIES[key] != value:
            print(f"Mismatch for property '{key}': expected {value}, got {class_object.RULE_PROPERTIES[key]}")
            return False
    return True
