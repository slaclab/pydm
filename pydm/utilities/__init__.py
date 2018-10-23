from .units import find_unittype, convert, find_unit_options
from . import macro
from . import colors
from .remove_protocol import remove_protocol, protocol_and_address
from .connection import establish_widget_connections, close_widget_connections
from .iconfont import IconFont
from ..qtdesigner import DesignerHooks

import os
import sys
import platform
import ntpath
import shlex


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
    from ..application import PyDMApplication
    from qtpy.QtWidgets import QApplication
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
    return DesignerHooks().form_editor is not None


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


def which(cmd, mode=os.F_OK | os.X_OK, path=None, pathext=None):
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
        return (os.path.exists(fn) and os.access(fn, mode) and
                not os.path.isdir(fn))

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
    for dir_ in path:
        normdir = os.path.normcase(dir_)
        if normdir not in seen:
            seen.add(normdir)
            for thefile in files:
                name = os.path.join(dir_, thefile)
                if _access_check(name, mode):
                    return name
    return None
