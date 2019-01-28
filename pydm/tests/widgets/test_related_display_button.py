import os
import pytest
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QVBoxLayout
from ...widgets.related_display_button import PyDMRelatedDisplayButton

test_ui_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "../test_data", "test.ui")

def test_press_with_filename(qtbot):
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    button.displayFilename = test_ui_path
    qtbot.addWidget(button)
    qtbot.mouseRelease(button, Qt.LeftButton)
    def check_title():
        assert "Form" in QApplication.instance().main_window.windowTitle()
    qtbot.waitUntil(check_title)

def test_press_without_filename(qtbot):
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    qtbot.addWidget(button)
    qtbot.mouseRelease(button, Qt.LeftButton)
    qtbot.wait(250)
    assert "Form" not in QApplication.instance().main_window.windowTitle()

def test_no_menu_without_additional_files(qtbot):
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    button.displayFilename = test_ui_path
    qtbot.addWidget(button)
    assert button.menu() is None

def test_menu_with_additional_files(qtbot):
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    main_window.set_display_widget(button)
    button.displayFilename = test_ui_path
    button.additionalFiles = [test_ui_path, test_ui_path]
    button.additionalTitles = ["One", "Two"]
    qtbot.addWidget(button)
    assert button.menu() is not None
    qtbot.mouseRelease(button, Qt.LeftButton)
    qtbot.waitExposed(button.menu())
    qtbot.mouseRelease(button.menu(), Qt.LeftButton)
    button.menu().actions()[0].trigger()
    def check_title():
        assert "Form" in QApplication.instance().main_window.windowTitle()
    qtbot.waitUntil(check_title)

def test_menu_goes_away_when_files_removed(qtbot):
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    main_window.set_display_widget(button)
    button.displayFilename = test_ui_path
    button.additionalFiles = ["one.ui", "two.ui"]
    button.additionalTitles = ["One", "Two"]
    qtbot.addWidget(button)
    assert button.menu() is not None
    button.additionalFiles = []
    button.additionalTitles = []
    assert button.menu() is None

def test_menu_goes_away_when_files_all_blank(qtbot):
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    button.displayFilename = test_ui_path
    button.additionalFiles = ["", ""]
    button.additionalTitles = ["", ""]
    qtbot.addWidget(button)
    assert button.menu() is None