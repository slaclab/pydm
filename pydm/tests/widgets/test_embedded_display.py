# Unit Tests for the PyDmEmbeddedDisplay Widget

import pytest

from ...PyQt.QtGui import QWidget, QFrame, QApplication, QLabel, QVBoxLayout
from ...PyQt.QtCore import Qt, QMargins

import json
import os.path

import logging
logger = logging.getLogger(__name__)

from ...application import PyDMApplication
from ...widgets.image import PyDMImageView
from ...widgets.embedded_display import PyDMEmbeddedDisplay


# --------------------
# POSITIVE TEST CASES
# --------------------

@pytest.mark.parametrize("is_pydm_app", [
    True,
    False
])
def test_construct(qtbot, monkeypatch, is_pydm_app):
    """
    Test the construction of the widget.

    Expectations:
    Default values are assigned to the widget's properties appropriately.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To simulate whether the widget is in a PyDM app or within Qt Designer.
    is_pydm_app : bool
        True if the widget is being tested for being a part of a PyDM app; False if the widget is within the Qt
        Designer's design process
    """
    monkeypatch.setattr(PyDMEmbeddedDisplay, "_is_pydm_app", lambda *args: is_pydm_app)

    pydm_embedded_display = PyDMEmbeddedDisplay()
    qtbot.addWidget(pydm_embedded_display)

    assert pydm_embedded_display.app == QApplication.instance()
    assert pydm_embedded_display._filename is None
    assert pydm_embedded_display._macros is None
    assert pydm_embedded_display._embedded_widget is None
    assert pydm_embedded_display._disconnect_when_hidden is True
    assert pydm_embedded_display._is_connected is False

    assert type(pydm_embedded_display.layout) == QVBoxLayout
    assert type(pydm_embedded_display.err_label) == QLabel
    assert pydm_embedded_display.err_label.isHidden()

    assert pydm_embedded_display.err_label.alignment() == Qt.AlignHCenter
    assert pydm_embedded_display.layout.count() == 1
    assert pydm_embedded_display.layout.contentsMargins() == QMargins(0, 0, 0, 0)

    if is_pydm_app:
        assert pydm_embedded_display.frameShape() == QFrame.NoFrame
    else:
        assert pydm_embedded_display.frameShape() == QFrame.Box


def test_minimum_size_hint(qtbot):
    """
    Test the widget's minimum size.

    Expectations:
    The minimum size must have its width and height both larger than 0.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    """
    pydm_embedded_display = PyDMEmbeddedDisplay()
    qtbot.addWidget(pydm_embedded_display)

    minimum_size = pydm_embedded_display.minimumSizeHint()
    assert minimum_size.width() > 0 and minimum_size.height() > 0


macros = {
    "key_1": "value_1",
    "key_2": "value_2",
}

@pytest.mark.parametrize("macro_content", [
    "",
    None,
    "None",
    json.dumps(macros, separators=(',', ':'), sort_keys=True, indent=4)
])
def test_macros(qtbot, macro_content):
    """
    Test the widget's macro property and setter.

    Expectations:
    1. If the macro is None or an empty string, the property will return an empty string
    2. Otherwise, the property returns the macro contents as str

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    macro_content : str
        The macro contents, which must be abel to be converted to a string
    """
    pydm_embedded_display = PyDMEmbeddedDisplay()
    qtbot.addWidget(pydm_embedded_display)

    pydm_embedded_display.macros = macro_content

    if macro_content:
        assert pydm_embedded_display.macros == macro_content
    else:
        assert pydm_embedded_display.macros == ""


@pytest.mark.parametrize("filename, is_pydm_app", [
    ("", True),
    ("", False),

    (None, True),
    (None, False),

    ("abc", True),
    ("abc", False),
])
def test_filename(qtbot, monkeypatch, filename, is_pydm_app):
    """
    Test the widet's filename property and setter.

    Expectations:
    1. If the filename is not empty, and the widget is a part of a PyDM app, the open_file() function will be executed.
    2. If the filename is not empty, but the widget is not a part of a PyDM app, the error label will display the file
       name

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    monkeypatch : fixture
        To simulate whether the widget is a part of a PyDM app or of Qt Designer, and whether the open_file() function
        will be executed.
    filename : str
        The name of the file to be opened
    is_pydm_app : bool
        True if the widget is being tested for being a part of a PyDM app; False if the widget is within the Qt
        Designer's design process
    """
    monkeypatch.setattr(PyDMEmbeddedDisplay, "_is_pydm_app", lambda *args: is_pydm_app)
    monkeypatch.setattr(PyDMEmbeddedDisplay, "open_file", lambda *args: QWidget())

    pydm_embedded_display = PyDMEmbeddedDisplay()
    qtbot.addWidget(pydm_embedded_display)

    pydm_embedded_display.filename = filename

    if pydm_embedded_display.filename:
        if is_pydm_app:
            assert isinstance(pydm_embedded_display.embedded_widget, QWidget)
        else:
            assert pydm_embedded_display.err_label.text() == pydm_embedded_display.filename


@pytest.mark.parametrize("macro", [
    '{ "key_1": "value_1", "key_2": "value_2" }',
    None,
    ''
])
def test_parsed_macros(qtbot, macro):
    """
    Test the widget's macro parsing.

    Expectations:
    1. If the macro isn't empty or None, the parsed contents will be a JSON-formatted string. This requires the macro
       contents to be JSON-compliant.
    2. Otherwise, the parsed contents will be an empty dict.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    macro : str, dict
        The contents of the macro to be parsed a JSON string.
    """
    pydm_embedded_display = PyDMEmbeddedDisplay()
    qtbot.addWidget(pydm_embedded_display)

    pydm_embedded_display.macros = macro
    parsed_contents = pydm_embedded_display.parsed_macros()
    assert isinstance(parsed_contents, dict)

    if macro:
        assert parsed_contents == json.loads(macro)
    else:
        assert parsed_contents == {}


@pytest.mark.parametrize("is_abs_path", [
    True,
    False
])
def test_open_file(qtbot, monkeypatch, caplog, is_abs_path):
    """
    Test the widget's file openng capability given an absolute or a relative file path.

    Expectations:
    1. If the file path is absolute, the open_file() function will be executed.
    2. If the file path is relative, the open_relative() function will be executed.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    monkeypatch : fixture
        To simulate the executions of the open_file() and open_relative() functions
    caplog : fixture
        To capture the log output during the monkeypatching function executions
    is_abs_path : bool
        True if the file path is absolute; False if relative
    """
    pydm_embedded_display = PyDMEmbeddedDisplay()
    qtbot.addWidget(pydm_embedded_display)

    pydm_embedded_display.filename = "test_filename"
    monkeypatch.setattr(os.path, 'isabs', lambda *args: is_abs_path)

    def mock_pydmapplication_open_file(*args, **kwargs):
        logging.info("Executing PyDMApplication.open_file()")

    def mock_pydmapplication_open_relative(*args, **kwargs):
        logging.info("Executing PyDMApplication.open_relative()")

    caplog.set_level(logging.INFO)
    monkeypatch.setattr(PyDMApplication, "open_file", mock_pydmapplication_open_file)
    monkeypatch.setattr(PyDMApplication, "open_relative", mock_pydmapplication_open_relative)

    pydm_embedded_display.open_file()

    if is_abs_path:
        assert "Executing PyDMApplication.open_file()" in caplog.text
    else:
        assert "Executing PyDMApplication.open_relative()" in caplog.text


@pytest.mark.parametrize("is_current_emb_widget_empty", [
    False,
    True
])
def test_embedded_widget(qtbot, monkeypatch, caplog, is_current_emb_widget_empty):
    """
    Test the widget's embedded widget property and setter.

    Expectations:
    1. The property must return the up-to-date embedded widget, or None as the default value
    2. The setter must replace the old embedded widget with the new one after closing the old widget's connections, then
       establishing the new widget's connections, and then set the internal _is_connected flag to True
    3. The error label must be hidden after an embedded widget is set

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    monkeypatch : fixture
        To simulate the closing of the old embedded widget's connections, and the establishing of the new embedded
        widget's new ones.
    caplog : fixture
        To capture the log output of the connection closing and establishing simulations
    is_current_emb_widget_empty : bool
        True if the current embedded widget is None; False otherwise
    """
    pydm_embedded_display = PyDMEmbeddedDisplay()
    qtbot.addWidget(pydm_embedded_display)

    caplog.set_level(logging.INFO)
    def mock_pydmapplication_establish_widget_connections(*args):
        logging.info("Executing PyDMApplication.establish_widget_connections()")

    monkeypatch.setattr(PyDMApplication, "establish_widget_connections",
                        mock_pydmapplication_establish_widget_connections)

    pydm_image_view_1 = PyDMImageView()

    if is_current_emb_widget_empty:
        pydm_embedded_display.embedded_widget = None
        assert pydm_embedded_display.embedded_widget is None
    else:
        pydm_embedded_display.embedded_widget = pydm_image_view_1
        assert pydm_embedded_display.embedded_widget == pydm_image_view_1

        assert pydm_embedded_display.err_label.isHidden()
        assert pydm_embedded_display._is_connected
        assert "Executing PyDMApplication.establish_widget_connections()" in caplog.text

    pydm_image_view_2 = PyDMImageView()

    def mock_pydmapplication_close_widget_connections(*args):
        logging.info("Executing PyDMApplication.close_widget_connections()")

    monkeypatch.setattr(PyDMApplication, "close_widget_connections",
                        mock_pydmapplication_close_widget_connections)

    pydm_embedded_display.embedded_widget = pydm_image_view_2
    assert pydm_embedded_display.embedded_widget == pydm_image_view_2

    assert pydm_embedded_display.err_label.isHidden()
    assert pydm_embedded_display._is_connected

    if not is_current_emb_widget_empty:
        assert "Executing PyDMApplication.close_widget_connections()" in caplog.text
    assert "Executing PyDMApplication.establish_widget_connections()" in caplog.text


@pytest.mark.parametrize("is_connected, is_embedded_widget_empty", [
    (True, False),
    (False, True),
    (True, True),
    (False, False)
])
def test_connect(qtbot, monkeypatch, caplog, is_connected, is_embedded_widget_empty):
    """
    Test the widget's ability to establish connections for the embedded widget.

    Expectations:
    1. If the widget is already connected, or its embedded widget is None, do not establish connections.
    2. Otherwise, establish the connections for the embedded widget's child widgets.

    Parameters
    ----------
   qtbot : fixture
        pytest-qt window for widget testing
    monkeypatch : fixture
        To simulate the establishing of the new embedded widget's new connections
    caplog : fixture
        To capture the log output of the connection establishing simulation
    is_connected : bool
        True if the widget is currently connected; False otherwise
    is_embedded_widget_empty : bool
        True if the embedded widget is None; False otherwise
    """
    pydm_embedded_display = PyDMEmbeddedDisplay()
    qtbot.addWidget(pydm_embedded_display)

    caplog.set_level(logging.INFO)
    def mock_pydmapplication_establish_widget_connections(*args, **kwargs):
        logging.info("Executing PyDMApplication.establish_widget_connections()")
    monkeypatch.setattr(PyDMApplication, "establish_widget_connections",
                        mock_pydmapplication_establish_widget_connections)

    pydm_embedded_display._is_connected = is_connected
    if not is_embedded_widget_empty:
        pydm_embedded_display.embedded_widget = PyDMImageView()

        # Set the connected status again to simulate a change in the connection status
        pydm_embedded_display._is_connected = is_connected

    caplog.clear()
    pydm_embedded_display.connect()

    if is_connected or is_embedded_widget_empty:
        assert len(caplog.text) == 0
    else:
        assert "Executing PyDMApplication.establish_widget_connections()" in caplog.text

@pytest.mark.parametrize("is_connected, is_embedded_widget_empty", [
    (True, False),
    (False, True),
    (True, True),
    (False, False)
])
def test_disconnect(qtbot, monkeypatch, caplog, is_connected, is_embedded_widget_empty):
    """
    Test the widget's ability to disconnect connections for the embedded widget.

    Expectations:
    1. If the widget is already disconnected, or its embedded widget is None, do not establish connections.
    2. Otherwise, close the connections for the embedded widget's child widgets.

    Parameters
    ----------
    qtbot : fixture
       pytest-qt window for widget testing
    monkeypatch : fixture
       To simulate the disconnecting of the new embedded widget's new connections
    caplog : fixture
       To capture the log output of the connection closing simulation
    is_connected : bool
       True if the widget is currently connected; False otherwise
    is_embedded_widget_empty : bool
       True if the embedded widget is None; False otherwise
    """
    pydm_embedded_display = PyDMEmbeddedDisplay()
    qtbot.addWidget(pydm_embedded_display)

    caplog.set_level(logging.INFO)
    def mock_pydmapplication_close_widget_connections(*args, **kwargs):
        logging.info("Executing PyDMApplication.close_widget_connections()")
    monkeypatch.setattr(PyDMApplication, "close_widget_connections",
                        mock_pydmapplication_close_widget_connections)

    pydm_embedded_display._is_connected = is_connected
    if not is_embedded_widget_empty:
        pydm_embedded_display.embedded_widget = PyDMImageView()

        # Set the connected status again to simulate a change in the connection status
        pydm_embedded_display._is_connected = is_connected

    caplog.clear()
    pydm_embedded_display.disconnect()

    if not is_connected or is_embedded_widget_empty:
        assert len(caplog.text) == 0
    else:
        assert "Executing PyDMApplication.close_widget_connections()" in caplog.text


def test_disconnect_when_hidden_property_and_setter(qtbot):
    """
    Test the widget's disconnectwhenHidden property and setter.

    Expectations:
    The property will retain the previously set value to return while the setter will update the property's value
    appropriately.

    Parameters
    ----------
    qtbot : fixture
       pytest-qt window for widget testing
    """
    pydm_embedded_display = PyDMEmbeddedDisplay()
    qtbot.addWidget(pydm_embedded_display)

    assert pydm_embedded_display.disconnectWhenHidden is True
    pydm_embedded_display.disconnectWhenHidden = False
    assert pydm_embedded_display.disconnectWhenHidden is False


@pytest.mark.parametrize("disconnect_when_hidden", [
    True,
    False
])
def test_show_event(qtbot, monkeypatch, caplog, disconnect_when_hidden):
    """
    Test the widget's connecting and disconnecting actions associated with its visibility.

    Expectations:
    1. If the widget's disconnectWhenHidden property is False, do not change any connection state, i.e. neither
       connect() nor disconnect() will be executed.
    2. Otherwise, the connect() function will be executed when the widget handles its showEvent, and the disconnect()
       function will be executed when the hideEvent takes place

    Parameters
    ----------
    qtbot : fixture
       pytest-qt window for widget testing
    monkeypatch : fixture
       To simulate the widget's connecting and disconnecting actions
    caplog : fixture
       To capture the log output of the connection closing simulation
    disconnect_when_hidden : bool
        True if the widget will connect at the showEvent, and disconnect and the hideEvent; False if the widget will
        perform neither actions
    """
    pydm_embedded_display = PyDMEmbeddedDisplay()
    qtbot.addWidget(pydm_embedded_display)

    pydm_embedded_display.disconnectWhenHidden = disconnect_when_hidden

    caplog.set_level(logging.INFO)

    def mock_connect(*args):
        logger.info("Executing PyDMEmbeddedDisplay.connect()")
    monkeypatch.setattr(PyDMEmbeddedDisplay, "connect", mock_connect)

    def mock_disconnect(*args):
        logger.info("Executing PyDMEmbeddedDisplay.disconnect()")
    monkeypatch.setattr(PyDMEmbeddedDisplay, "disconnect", mock_disconnect)

    pydm_embedded_display.setVisible(True)
    pydm_embedded_display.setVisible(False)

    def wait_hidden():
        return not pydm_embedded_display.isVisible()
    qtbot.waitUntil(wait_hidden, timeout=5000)

    if disconnect_when_hidden:
        assert "Executing PyDMEmbeddedDisplay.connect()" in caplog.text
        assert "Executing PyDMEmbeddedDisplay.disconnect()" in caplog.text
    else:
        assert len(caplog.text) == 0


# --------------------
# NEGATIVE TEST CASES
# --------------------

@pytest.mark.parametrize("exception, is_pydm_app", [
    (ValueError, True),
    (ValueError, False),

    (IOError, True),
    (IOError, False)
])
def test_filename_neg(qtbot, monkeypatch, exception, is_pydm_app):
    """
    Test the widget's ability to handle exceptions raised by open_file() within the filename setter.

    Expectations:
    1. If open_file() raises a ValueError exception, the widget's error label will display the "Could not parse macro
       string" text
    2. If open_file raises an IOError exception, the widget's error label will display the "Could not open 'filename'"
       text.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    monkeypatch : fixture
        To simulate whether the widget is a part of a PyDM app or of Qt Designer, and whether the open_file() function
        will be executed.
    exception : Exception
        The exception type the open_file() function  raises
    is_pydm_app : bool
        True if the widget is being tested for being a part of a PyDM app; False if the widget is within the Qt
        Designer's design process
    """
    monkeypatch.setattr(PyDMEmbeddedDisplay, "_is_pydm_app", lambda *args: is_pydm_app)

    def mock_open_file(*args):
        raise exception
    monkeypatch.setattr(PyDMEmbeddedDisplay, "open_file", mock_open_file)

    pydm_embedded_display = PyDMEmbeddedDisplay()
    qtbot.addWidget(pydm_embedded_display)

    test_filename = "test_filename"
    pydm_embedded_display.filename = test_filename
    err_label_text = pydm_embedded_display.err_label.text()

    if is_pydm_app:
        if exception == ValueError:
            assert "Could not parse macro string" in err_label_text
        elif exception == IOError:
            assert "Could not open '{0}'".format(test_filename) in err_label_text
    else:
        assert err_label_text == test_filename










