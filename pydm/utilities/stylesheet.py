# Utility to handle importing the global stylesheet for PyDM widgets
import os
import logging

from qtpy.QtWidgets import QApplication

from ..config import STYLESHEET, STYLESHEET_INCLUDE_DEFAULT

logger = logging.getLogger(__name__)


# Fallback global stylesheet if there is no global stylesheet provided via env
# variable or command line parameter
GLOBAL_STYLESHEET = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        '..',
        'default_stylesheet.qss'
    )
)

__style_data = None


def clear_cache():
    """Clear the cache for stylesheet data"""
    global __style_data
    __style_data = None


def merge_widget_stylesheet(widget, stylesheet_file_path=None):
    curr_style = widget.styleSheet() or ""
    env_style = _get_style_data(stylesheet_file_path) or ""
    widget.setStyleSheet(env_style + curr_style)


def apply_stylesheet(stylesheet_file_path=None, widget=None):
    """
    Apply a stylesheet to the current Qt Designer form (a .ui file) or to a
    Designer form using the PyDM Launcher.

    Parameters
    ----------
    stylesheet_file_path : str
        The full path to a global CSS stylesheet file
    widget : QWidget
        The widget in which we want to apply the stylesheet.
    """
    # Load style data from the stylesheet file. Otherwise, the fallback is
    # already in place, i.e. PyDM will be using the data from the global
    # stylesheet
    style = _get_style_data(stylesheet_file_path)

    if not style:
        return

    if not widget:
        widget = QApplication.instance()

    widget.setStyleSheet(style)


def _get_style_data(stylesheet_file_path=None):
    """
    Read the global stylesheet file and provide the style data as a str.

    Parameters
    ----------
    stylesheet_file_path : str
        The path to the global stylesheet.

    Returns
    -------
    The style data read from the stylesheet file : str
    """
    global __style_data

    if __style_data:
        return __style_data

    if not stylesheet_file_path:
        stylesheet_file_path = STYLESHEET

    if not stylesheet_file_path:
        stylesheet_file_path = None

    __style_data = ""
    load_default = True

    if stylesheet_file_path is not None:
        files = stylesheet_file_path.split(os.pathsep)
        for f in files[::-1]:
            if not f:
                continue
            try:
                with open(f, 'r') as stylesheet_file:
                    logger.debug(
                        "Opening style file '{0}'...".format(stylesheet_file_path))
                    __style_data += stylesheet_file.read()
                    load_default = False
            except Exception as ex:
                logger.error(
                    "Error reading the stylesheet file '{0}'. Exception: {1}".format(
                        f, str(ex)))

    if load_default or STYLESHEET_INCLUDE_DEFAULT:
        try:
            with open(GLOBAL_STYLESHEET, 'r') as default_stylesheet:
                logger.debug("Opening the default stylesheet '{0}'...".format(
                    GLOBAL_STYLESHEET))
                __style_data = default_stylesheet.read() + __style_data
        except Exception as ex:
            __style_data = None
            logger.error(
                "Cannot find the default stylesheet file '{0}'. Exception: {1}".format(
                    GLOBAL_STYLESHEET,
                    str(ex)))
    return __style_data
