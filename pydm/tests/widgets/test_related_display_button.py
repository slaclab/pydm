import os
import pytest
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QVBoxLayout
from ...widgets.related_display_button import PyDMRelatedDisplayButton

test_ui_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "../test_data", "test.ui")

def test_old_display_filename_property(qtbot):
    # This test is mostly only checking that the related display button
    # doesn't totally explode when the old 'displayFilename' property is used.
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    with pytest.warns(None) as record:
        button.displayFilename = test_ui_path
    assert len(record) >= 1
    assert button.filenames[0] == test_ui_path
    qtbot.addWidget(button)
    button._rebuild_menu()
    qtbot.mouseRelease(button, Qt.LeftButton)
    def check_title():
        assert "Form" in QApplication.instance().main_window.windowTitle()
    qtbot.waitUntil(check_title)

def test_press_with_filename(qtbot):
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    button.filenames = [test_ui_path]
    qtbot.addWidget(button)
    button._rebuild_menu()
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
    button._rebuild_menu()
    qtbot.mouseRelease(button, Qt.LeftButton)
    qtbot.wait(250)
    assert "Form" not in QApplication.instance().main_window.windowTitle()

def test_no_menu_with_one_file(qtbot):
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    button.filenames = [test_ui_path]
    qtbot.addWidget(button)
    button._rebuild_menu()
    assert button.menu() is None

def test_menu_with_additional_files(qtbot):
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    main_window.set_display_widget(button)
    button.filenames = [test_ui_path, test_ui_path]
    button.titles = ["One", "Two"]
    qtbot.addWidget(button)
    button._rebuild_menu()
    assert button.menu() is not None
    qtbot.mouseRelease(button, Qt.LeftButton)
    qtbot.waitExposed(button.menu())
    qtbot.mouseClick(button.menu(), Qt.LeftButton)
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
    button.filenames = ["one.ui", "two.ui"]
    button.titles = ["One", "Two"]
    qtbot.addWidget(button)
    button._rebuild_menu()
    assert button.menu() is not None
    button.filenames = []
    button.titles = []
    button._rebuild_menu()
    assert button.menu() is None

def test_menu_goes_away_when_files_all_blank(qtbot):
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    button.filenames = ["", ""]
    button.titles = ["", ""]
    qtbot.addWidget(button)
    button._rebuild_menu()
    assert button.menu() is None