# Unit Tests for the PyDMRelatedDisplayButton Widget

import pytest

import json
import logging
logger = logging.getLogger(__name__)

from ...PyQt.QtGui import QMouseEvent, QMenu, QCursor
from ...PyQt.QtCore import pyqtProperty, Qt, QSize
from ...widgets.related_display_button import PyDMRelatedDisplayButton
from ...tests.widgets.test_lineedit import find_action_from_menu
from ...utilities import IconFont


# --------------------
# POSITIVE TEST CASES
# --------------------

@pytest.mark.parametrize("filename", [
    "abc",
    "",
    None
])
def test_construct(qtbot, filename):
    """
    Test the construction of the widget.

    Expectations:
    The default values are assigned correctly to the corresponding attributes.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    filename : str
        The name of the file to open
    """
    pydm_related_display_button = PyDMRelatedDisplayButton(filename=filename)
    qtbot.addWidget(pydm_related_display_button)

    assert pydm_related_display_button.mouseReleaseEvent == pydm_related_display_button.push_button_release_event
    assert pydm_related_display_button.contextMenuPolicy() == Qt.ContextMenuPolicy(Qt.CustomContextMenu)

    assert type(pydm_related_display_button.iconFont) == IconFont
    icon = IconFont().icon("file")
    size = QSize(30, 30)
    icon_pixmap = icon.pixmap(size)
    button_icon_pixmap = pydm_related_display_button.icon().pixmap(size)
    assert icon_pixmap.toImage() == button_icon_pixmap.toImage()

    assert pydm_related_display_button.cursor().pixmap().toImage() == \
           pydm_related_display_button.icon().pixmap(16, 16).toImage()
    assert pydm_related_display_button._display_filename == filename
    assert pydm_related_display_button._macro_string is None
    assert pydm_related_display_button._open_in_new_window == False
    assert pydm_related_display_button.open_in_new_window_action.text() == "Open in New Window"
    assert pydm_related_display_button._show_icon is True
    assert pydm_related_display_button._target is None


def test_properties_and_setters(qtbot):
    """
    Test the properties and setters of the widget.

    Expectations:
    The setters will update the new value to the properties, which will return the latest values when needed.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_related_display_button = PyDMRelatedDisplayButton()
    qtbot.addWidget(pydm_related_display_button)

    # showIcon
    pydm_related_display_button.showIcon = False
    assert pydm_related_display_button.showIcon is False
    assert pydm_related_display_button.icon().isNull()

    pydm_related_display_button.showIcon = True
    assert pydm_related_display_button.showIcon is True
    icon = IconFont().icon("file")
    size = QSize(30, 30)
    icon_pixmap = icon.pixmap(size)
    button_icon_pixmap = pydm_related_display_button.icon().pixmap(size)
    assert icon_pixmap.toImage() == button_icon_pixmap.toImage()

    # displayFilename
    assert pydm_related_display_button.displayFilename is None
    pydm_related_display_button.displayFilename = ""
    assert not pydm_related_display_button.isEnabled()

    pydm_related_display_button.displayFilename = "test filename"
    assert pydm_related_display_button.displayFilename == "test filename"
    assert pydm_related_display_button.isEnabled()

    # macros
    assert pydm_related_display_button.macros  == ""
    pydm_related_display_button.macros = ""
    assert pydm_related_display_button.macros == ""

    pydm_related_display_button.macros = "a"
    assert pydm_related_display_button.macros == "a"
    pydm_related_display_button.macros = "abc"
    assert pydm_related_display_button.macros == "abc"

    # openInNewWindow
    assert pydm_related_display_button.openInNewWindow is False
    pydm_related_display_button.openInNewWindow = True
    assert pydm_related_display_button.openInNewWindow is True


def test_check_enable_state(qtbot):
    """
    Test the widget's always-enabled status.

    Expectations:
    Set the widget as disabled, and then run the check_enable_state() method. The widget must be enabled then.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_related_display_button = PyDMRelatedDisplayButton()
    qtbot.addWidget(pydm_related_display_button)

    pydm_related_display_button.setEnabled(False)
    assert not pydm_related_display_button.isEnabled()

    pydm_related_display_button.check_enable_state()
    assert pydm_related_display_button.isEnabled()


macros = {
    "key_1": "value_1",
    "key_2": "value_2",
}


@pytest.mark.parametrize("key_pressed, key_mod, open_in_new_window, display_filename, macros", [
    (Qt.LeftButton, Qt.ShiftModifier, False, "test_filename", macros),
    (Qt.LeftButton, Qt.ShiftModifier, False, "", macros),
    (Qt.LeftButton, Qt.ShiftModifier, False, "", None),
    (Qt.LeftButton, Qt.ShiftModifier, False, None, macros),
    (Qt.LeftButton, Qt.ShiftModifier, False, None, ""),
    (Qt.LeftButton, Qt.ShiftModifier, False, None, None),

    (Qt.LeftButton, Qt.ShiftModifier, True, "test_filename", macros),
    (Qt.LeftButton, Qt.ShiftModifier, True, "", macros),
    (Qt.LeftButton, Qt.ShiftModifier, True, "", None),
    (Qt.LeftButton, Qt.ShiftModifier, True, None, macros),
    (Qt.LeftButton, Qt.ShiftModifier, True, None, ""),
    (Qt.LeftButton, Qt.ShiftModifier, True, None, None),

    (Qt.RightButton, Qt.ShiftModifier, False, "test_filename", macros),
    (Qt.RightButton, Qt.ShiftModifier, False, "", macros),
    (Qt.RightButton, Qt.ShiftModifier, False, "", None),
    (Qt.RightButton, Qt.ShiftModifier, False, None, macros),
    (Qt.RightButton, Qt.ShiftModifier, False, None, ""),
    (Qt.RightButton, Qt.ShiftModifier, False, None, None),

    (Qt.MiddleButton, Qt.ShiftModifier, False, "test_filename", macros),
    (Qt.MiddleButton, Qt.ShiftModifier, False, "", macros),
    (Qt.MiddleButton, Qt.ShiftModifier, False, "", None),
    (Qt.MiddleButton, Qt.ShiftModifier, False, None, macros),
    (Qt.MiddleButton, Qt.ShiftModifier, False, None, ""),
    (Qt.MiddleButton, Qt.ShiftModifier, False, None, None),

    (Qt.LeftButton, Qt.NoModifier, False, "test_filename", macros),
    (Qt.LeftButton, Qt.NoModifier, False, "", macros),
    (Qt.LeftButton, Qt.NoModifier, False, "", None),
    (Qt.LeftButton, Qt.NoModifier, True, None, macros),
    (Qt.LeftButton, Qt.NoModifier, True, None, ""),
    (Qt.LeftButton, Qt.NoModifier, True, None, None),

    (Qt.RightButton, Qt.NoModifier, False, "test_filename", macros),
    (Qt.RightButton, Qt.NoModifier, False, "", macros),
    (Qt.RightButton, Qt.NoModifier, False, "", None),
    (Qt.RightButton, Qt.NoModifier, True, None, macros),
    (Qt.RightButton, Qt.NoModifier, True, None, ""),
    (Qt.RightButton, Qt.NoModifier, True, None, None),

    (Qt.MiddleButton, Qt.NoModifier, False, "test_filename", macros),
    (Qt.MiddleButton, Qt.NoModifier, False, "", macros),
    (Qt.MiddleButton, Qt.NoModifier, False, "", None),
    (Qt.MiddleButton, Qt.NoModifier, True, None, macros),
    (Qt.MiddleButton, Qt.NoModifier, True, None, ""),
    (Qt.MiddleButton, Qt.NoModifier, True, None, None),
])
def test_push_button_release_event(qtbot, key_pressed, key_mod, open_in_new_window, display_filename, macros):
    """
    Generate the mouse release event, with and without the Shift key modifier to test the widget's display opening.

    Expectations:
    1. The widget will the file in a new window if a mouse button is released with the Shift key is being pressed.

    2. The widget will open the file in the same window if the mouse button is released if the Shift key is not being
       pressed.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    key_pressed : Qt.Key
        The mouse key being pressed prior to release
    key_mod : Qt.Key
        The key modifier (Shift in this test)
    open_in_new_window : bool
        True if a new window is expected to be opened; False if the same window is being used
    display_filename : str
        The name of the file to be opened
    macros : dict
        A dictionary representing the macros. This dict will be converted to a JSON string during the test.
    """
    pydm_related_display_button = PyDMRelatedDisplayButton()
    qtbot.addWidget(pydm_related_display_button)

    # Set the optional property to whether a new window will be opened. This has an OR relationship to the Shift + mouse
    # key pressed action to indicate whether to open a new window
    pydm_related_display_button.openInNewWindow = open_in_new_window

    # These are required for the window opening action
    pydm_related_display_button.displayFilename = display_filename
    pydm_related_display_button.macros = json.dumps(macros, separators=(',', ':'), sort_keys=True, indent=4)

    # Dispatch the Mouse Release event
    pydm_related_display_button.mouseReleaseEvent(QMouseEvent(
        QMouseEvent.MouseButtonRelease, pydm_related_display_button.rect().center(), key_pressed, key_pressed, key_mod))

    if not display_filename:
        assert pydm_related_display_button._target is None
    else:
        # If the Shift key is pressed or the openInNewWindow property is set, make sure the _target attribute is set to
        # NEW_WINDOW
        if key_mod == Qt.ShiftModifier or pydm_related_display_button.openInNewWindow:
            assert pydm_related_display_button._target == PyDMRelatedDisplayButton.NEW_WINDOW
        else:
            # Otherwise, the _target property should be set to EXISTING_WINDOW
            assert pydm_related_display_button._target == PyDMRelatedDisplayButton.EXISTING_WINDOW


def test_context_menu(qtbot):
    """
    Test to make sure the widget's context menu contains the specific action for the widget.

    Expectations:
    All specific actions for the widget's context menu are present in that menu.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_related_display_button = PyDMRelatedDisplayButton()
    qtbot.addWidget(pydm_related_display_button)

    menu = pydm_related_display_button.context_menu()
    action_menu = menu.menuAction().menu()

    # Make sure the context menu contains the "Open in New Window" command
    assert find_action_from_menu(action_menu,
                                 pydm_related_display_button.open_in_new_window_action.text())


def test_show_context_menu(qtbot, monkeypatch, caplog):
    """
    Test to ensure the context menu can be displayed when the customContextMenuRequested signal emit to the
    show_context_menu slot.

    Expectations:
    Instead of displaying the context menu, monkeypatch exec()_ to just log the execution, and check to ensure the log
    event is there.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To override dialog behaviors
    caplog : fixture
        The fixture to capture log outputs
    """
    pydm_related_display_button = PyDMRelatedDisplayButton()
    qtbot.addWidget(pydm_related_display_button)

    caplog.set_level(logging.INFO)

    def mock_exec_(*args):
        logger.info("Context Menu displayed.")
    monkeypatch.setattr(QMenu, "exec_", mock_exec_)

    pydm_related_display_button.customContextMenuRequested.emit(pydm_related_display_button.rect().center())

    assert "Context Menu displayed." in caplog.text


# --------------------
# NEGATIVE TEST CASES
# --------------------

@pytest.mark.parametrize("target, exception",[
    (PyDMRelatedDisplayButton.NEW_WINDOW, IOError),
    (PyDMRelatedDisplayButton.NEW_WINDOW, OSError),
    (PyDMRelatedDisplayButton.NEW_WINDOW, ValueError),
    (PyDMRelatedDisplayButton.NEW_WINDOW, ImportError),

    (PyDMRelatedDisplayButton.EXISTING_WINDOW, IOError),
    (PyDMRelatedDisplayButton.EXISTING_WINDOW, OSError),
    (PyDMRelatedDisplayButton.EXISTING_WINDOW, ValueError),
    (PyDMRelatedDisplayButton.EXISTING_WINDOW, ImportError),
])
def test_open_display_neg(qtbot, monkeypatch, target, exception):
    """
    Test to ensure the widget's status bar displays the error message when a window opening action raises an exception.

    Expectations:
    Since this open_display is associated with the PyDMMainWindow, which is not instantiated here, the best this test
    can try is to monkeypatch the window() method so that an exception is raised, simulating the exception raised in
    the main code

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To override dialog behaviors
    target : int
        A value indicating whether the file is to be opened in a new window, or the existing window
    exception : Exception
        An exception to be thrown by the widget's window during opening.
    """
    pydm_related_display_button = PyDMRelatedDisplayButton()
    qtbot.addWidget(pydm_related_display_button)

    pydm_related_display_button.displayFilename = "abc"
    pydm_related_display_button.macros = json.dumps(macros, separators=(',', ':'), sort_keys=True, indent=4)

    def mock_window(*args):
        raise exception

    monkeypatch.setattr(PyDMRelatedDisplayButton, "window", mock_window)

    with pytest.raises(exception):
        pydm_related_display_button.open_display()
