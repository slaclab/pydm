import os
import pytest

from pydm.display import Display, MainWindowDisplay, load_ui_file, _get_ui_root_widget_class
from qtpy.QtWidgets import QMainWindow, QWidget

TEST_DATA = os.path.join(os.path.dirname(__file__), "test_data")
MAINWINDOW_UI = os.path.join(TEST_DATA, "mainwindow_test.ui")


def test_get_ui_root_widget_class_mainwindow():
    """Detect QMainWindow as root widget class in a .ui file."""
    assert _get_ui_root_widget_class(MAINWINDOW_UI) == "QMainWindow"


def test_load_mainwindow_ui_returns_mainwindow_display(qtbot):
    """Loading a QMainWindow .ui file produces a MainWindowDisplay instance.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt fixture for widget management.
    """
    display = load_ui_file(MAINWINDOW_UI)
    qtbot.addWidget(display)
    assert isinstance(display, MainWindowDisplay)
    assert isinstance(display, QMainWindow)


def test_load_mainwindow_ui_does_not_crash(qtbot):
    """QMainWindow .ui files should load without AttributeError.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt fixture for widget management.
    """
    display = load_ui_file(MAINWINDOW_UI)
    qtbot.addWidget(display)
    assert hasattr(display, "setCentralWidget")
    assert display.centralWidget() is not None


def test_mainwindow_display_has_full_display_interface(qtbot):
    """MainWindowDisplay should have all Display methods so isinstance checks
    and navigation/menu/macro features work correctly.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt fixture for widget management.
    """
    display = load_ui_file(MAINWINDOW_UI)
    qtbot.addWidget(display)

    assert hasattr(display, "args")
    assert hasattr(display, "macros")
    assert hasattr(display, "loaded_file")
    assert hasattr(display, "menu_items")
    assert hasattr(display, "file_menu_items")
    assert hasattr(display, "show_help")
    assert hasattr(display, "navigate_back")
    assert hasattr(display, "navigate_forward")
    assert hasattr(display, "load_ui_from_file")
    assert hasattr(display, "load_help_file")
    assert hasattr(display, "previous_display")
    assert hasattr(display, "next_display")
