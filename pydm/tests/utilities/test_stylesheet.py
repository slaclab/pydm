# Unit Tests for External Stylesheet Importing

import pytest

import os
import tempfile
import difflib

import logging
logger = logging.getLogger(__name__)

from ...PyQt.QtCore import QTimer
from ...PyQt.QtGui import QWidget

from ...application import PyDMApplication
import pydm.utilities as utilities
from ...utilities.stylesheet import apply_stylesheet, _get_style_data, _set_style_data, GLOBAL_STYLESHEET


# The path to the stylesheet used in these unit tests
test_stylesheet_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "test_data",
                                    "global_stylesheet.css")

# --------------------
# POSITIVE TEST CASES
# --------------------

@pytest.mark.parametrize("file_path, env_path, timer", [
    (test_stylesheet_path, None, None),
    (test_stylesheet_path, None, QTimer()),
    (None, test_stylesheet_path, None),
    (None, test_stylesheet_path, QTimer()),
    (test_stylesheet_path, test_stylesheet_path, None),
    (test_stylesheet_path, test_stylesheet_path, QTimer()),
    (None, None, None),
    (None, None, QTimer())
])
def test_apply_stylesheet(monkeypatch, caplog, file_path, env_path, timer):
    """
    Test applying an external stylesheet to either an app or a widget.

    Expectations:
    1. The path to the stylesheet will be in the following order:
        a. The external path from the PyDM app command line parameter
        b. If it's not available, PyDM will use the path set by the PYDM_STYLESHEET env variable
        c. If the env variable is not set, use the built-in GLOBAL_STYLESHEET

    2. Here, we're only testing whether the path search order is correct, and whether the timer is started. The
       correctness of the subsequent function calls will be tested separately.

    Parameters
    ----------
    monkeypatch : fixture
        To override functions that do not need to be tested currently
    caplog : fixture
        To capture log output to ensure workflow correctness
    file_path : str
        The file path to the test stylesheet file, which represents the value coming from a PyDM command line parameter
    env_path : str
        The file path to the test stylesheet file supposedly coming from the env variable
    timer : QTimer
        The timer set by the caller
    """
    if env_path:
        os.environ["PYDM_STYLESHEET"] = env_path

    caplog.set_level(logging.INFO)

    def mock_get_style_data(*args):
        logger.info(args)
        return GLOBAL_STYLESHEET
    monkeypatch.setattr(utilities.stylesheet, "_get_style_data", mock_get_style_data)

    def mock_timer_start(*args):
        logger.info("Starting timer...")
    monkeypatch.setattr(QTimer, "start", mock_timer_start)

    def mock_set_style_data(style_data, timer=None):
        logger.info(style_data)
    monkeypatch.setattr(utilities.stylesheet, "_set_style_data", mock_set_style_data)

    style_data = apply_stylesheet(file_path, timer)

    if file_path:
        assert file_path in caplog.text
    else:
        if env_path:
            assert env_path in caplog.text
        else:
            assert style_data == GLOBAL_STYLESHEET
    if timer:
        assert "Starting timer..." in caplog.text


@pytest.mark.parametrize("file_path", [
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "test_data", "global_stylesheet.css"),
    None,
])
def test_get_style_data(file_path):
    """
    Test the reading of the stylesheet file.

    Expectations:
    This method should be able to locate the stylesheet file, given the correct path, and read its contents.

    If the path is None, the GLOBAL_STYLESHEET data should be read.

    Parameters
    ----------
    file_path : str
        The file path to the test stylesheet file, which could come from a PyDM command line parameter, or from the
        env variable "PYDM_STYLESHEET'
    """
    style_data = _get_style_data(file_path)
    if file_path:
        tmp_file_path = tempfile.mkstemp(prefix="pydm_test_styletest")[1]

        # Open the file for writing.
        with open(tmp_file_path, 'w') as f:
            f.write(style_data)

        with open(file_path) as source:
            with open(tmp_file_path) as dest:
                diffs = difflib.unified_diff(
                    source.readlines(),
                    dest.readlines(),
                    fromfile='source',
                    tofile='dest',
                )
                diff_lines = []
                for line in diffs:
                    diff_lines.append(line)
                assert len(diff_lines) == 0
                dest.close()
            source.close()
        os.remove(tmp_file_path)
    else:
        assert style_data == GLOBAL_STYLESHEET


@pytest.mark.parametrize("is_pydm_app", [
    True,
    False
])
def test_set_style_data(qtbot, monkeypatch, caplog, is_pydm_app):
    """
    Test the application of the stylesheet data to either the PyDM app or the root widget.

    Expectations:
    If this is a PyDM app, the stylesheet data will be applied to the app. If not, i.e. in Qt Designer, the stylesheet
    data will be applied to the widget whose name is "formContainer".

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To override functions that do not need to be tested currently
    caplog : fixture
        To capture log output to ensure workflow correctness
    is_pydm_app : bool
        True if we want to simulate an PyDM app; False if not, i.e. simulating the Qt Designer environment
    """
    monkeypatch.setattr(utilities.stylesheet, "is_pydm_app", lambda *args: is_pydm_app)

    caplog.set_level(logging.INFO)

    style_data = GLOBAL_STYLESHEET
    timer = None

    if is_pydm_app:
        def mock_set_stylesheet_for_app(*args, **kwargs):
            logger.info("Setting stylesheet for the app...")
        monkeypatch.setattr(utilities.stylesheet, "_set_stylesheet_for_app", mock_set_stylesheet_for_app)
    else:
        timer = QTimer()
        timer.setInterval(500)

        root_widget = QWidget()
        qtbot.addWidget(root_widget)

        empty_widget = QWidget()
        qtbot.addWidget(empty_widget)

        root_widget.setObjectName("formContainer")
        monkeypatch.setattr(PyDMApplication, "allWidgets", lambda *args: [empty_widget, root_widget])

        def mock_widget_setStyleSheet(*args, **kwargs):
            logger.info("Setting stylesheet for the widget...")
        monkeypatch.setattr(QWidget, "setStyleSheet", mock_widget_setStyleSheet)

        def mock_timer_stop(*args):
            logger.info("Stopping timer...")
        monkeypatch.setattr(QTimer, "stop", mock_timer_stop)

    _set_style_data(style_data, timer)

    if is_pydm_app:
        assert "Setting stylesheet for the app..." in caplog.text
    else:
        assert "Setting stylesheet for the widget..." in caplog.text
        assert "Stopping timer..." in caplog.text


# --------------------
# NEGATIVE TEST CASES
# --------------------

def test_apply_stylesheet_neg(caplog):
    _get_style_data("foo")

    for record in caplog.records:
        assert record.levelno == logging.ERROR
    assert "Error reading the stylesheet file 'foo'" in caplog.text
