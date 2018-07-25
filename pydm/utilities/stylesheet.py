# Utility to handle importing the global stylesheet for PyDM widgets

from ..PyQt.QtGui import QApplication
import os
from functools import partial

import logging

logger = logging.getLogger(__name__)
from . import is_pydm_app

# Fallback global stylesheet if there is no global stylesheet provided via env
# variable or command line parameter
GLOBAL_STYLESHEET = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        '..',
        'default_stylesheet.qss'
    )
)

def apply_stylesheet(stylesheet_file_path, timer=None):
    """
    Apply a stylesheet to the current Qt Designer form (a .ui file) or to a Designer form using the PyDM Launcher.

    Parameters
    ----------
    stylesheet_file_path : str
        The full path to a global CSS stylesheet file
    timer : QTimer
        A timer to launch the set stylesheet method for Qt Designer. For the PyDM Launcher, the timer is not needed,
        and can be set to None
    """
    if not stylesheet_file_path:
        # If there is no stylesheet path provided by a command parameter, check for the env variable
        stylesheet_file_path = os.getenv("PYDM_STYLESHEET", None)

    # Load style data from the stylesheet file. Otherwise, the fallback is already in place, i.e. PyDM will be
    # using the data from the global stylesheet
    style_data = _get_style_data(stylesheet_file_path)

    if timer:
        # For PyDM Launcher, the timer should be None. This code is to handle Qt
        # Designer only
        timer.timeout.connect(partial(_set_style_data, style_data, timer))
        timer.start()
    else:
        # For running PyDM Launcher
        _set_style_data(style_data, None)

    return style_data


def _get_style_data(stylesheet_file_path):
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
    style_data = None
    load_default = True
    if stylesheet_file_path is not None:
        try:
            with open(stylesheet_file_path, 'r') as stylesheet_file:
                logger.info(
                    "Opening style file '{0}'...".format(stylesheet_file_path))
                style_data = stylesheet_file.read()
                load_default = False
        except Exception as ex:
            style_data = None
            logger.error(
                "Error reading the stylesheet file '{0}'. Exception: {1}".format(
                    stylesheet_file_path,
                    str(ex)))

    if load_default:
        try:
            with open(GLOBAL_STYLESHEET) as default_stylesheet:
                logger.info("Opening the default stylesheet '{0}'...".format(
                    GLOBAL_STYLESHEET))
                style_data = default_stylesheet.read()
        except Exception as ex:
            style_data = None
            logger.error(
                "Cannot find the default stylesheet file '{0}'. Exception: {1}".format(
                    GLOBAL_STYLESHEET,
                    str(ex)))
    return style_data


def _set_style_data(style_data, timer):
    """
    Apply the global stylesheet data to a .ui form.

    If the PyDM Launcher opens this .ui form, apply the stylesheet directly to the app. Otherwise, in Qt Designer, apply
    the stylesheet to the root object ("formContainer").

    Parameters
    ----------
    style_data : str
        The style data obtained from a stylesheet file
    timer : QTimer
        The timer to launch the style data applying method (for the Qt Designer environment only)
    """
    app = QApplication.instance()
    if is_pydm_app():
        _set_stylesheet_for_app(app, style_data)
    else:
        for w in app.allWidgets():
            try:
                name = w.objectName()
            except:
                name = ''
            # Set the stylesheet to the root form object
            if name == "formContainer":
                # This will be loaded from the file set by users to define the global stylesheet for the facility in
                # use
                w.setStyleSheet(style_data)
                # A timer is fully expected here. If a timer cannot be provided for whatever reason, we must re-evaluate
                # the current Qt Designer stylesheet application methodology
                timer.stop()


def _set_stylesheet_for_app(app, style_data):
    """
    Apply the global stylesheet for an app.

    This method is needed due to unit testing requirements.

    Parameters
    ----------
    app : PyDMApplication
        The PyDMApplication instance
    style_data : str
        The stylesheet data, either from a file or from the GLOBAL_STYLESHEET

    """
    app.setStyleSheet(style_data)
