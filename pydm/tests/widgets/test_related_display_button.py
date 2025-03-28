import os
import pytest
import sys
import warnings
from qtpy.QtCore import Qt, QSize
from qtpy.QtWidgets import QApplication
from pydm.utilities.stylesheet import global_style
from pydm.widgets.related_display_button import PyDMRelatedDisplayButton
from pydm.utilities import IconFont, checkObjectProperties

test_ui_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../test_data", "test.ui")
test_ui_path_with_stylesheet = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "../test_data", "test_emb_style.ui"
)
test_ui_path_with_relative_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "../test_data", "test_relative_filename_parent.ui"
)


# additional props we expect to get added to PyDMRelatedDisplayButton class RULE_PROPERTIES
expected_related_display_button_properties = {"Text": ["setText", str], "Filenames": ["filenames", list]}


def test_old_display_filename_property(qtbot):
    # This test is mostly only checking that the related display button
    # doesn't totally explode when the old 'displayFilename' property is used.
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    assert checkObjectProperties(button, expected_related_display_button_properties) is True
    with warnings.catch_warnings(record=True) as record:
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

    # verify default icon is set as expected
    DEFAULT_ICON_NAME = "file"
    DEFAULT_ICON_SIZE = QSize(16, 16)

    default_icon = IconFont().icon(DEFAULT_ICON_NAME)

    default_icon_pixmap = default_icon.pixmap(DEFAULT_ICON_SIZE)
    related_display_button_icon_pixmap = button.icon().pixmap(DEFAULT_ICON_SIZE)

    assert related_display_button_icon_pixmap.toImage() == default_icon_pixmap.toImage()
    assert button.cursor().pixmap().toImage() == default_icon_pixmap.toImage()

    # verify that qt standard icons can be set through our custom property
    style = button.style()
    test_icon = style.standardIcon(style.StandardPixmap.SP_DesktopIcon)
    test_icon_image = test_icon.pixmap(DEFAULT_ICON_SIZE).toImage()

    button.PyDMIcon = "SP_DesktopIcon"
    shell_cmd_icon = button.icon()
    shell_cmd_icon_image = shell_cmd_icon.pixmap(DEFAULT_ICON_SIZE).toImage()

    assert test_icon_image == shell_cmd_icon_image

    # verify that "Font Awesome" icons can be set through our custom property
    icon_f = IconFont()
    test_icon = icon_f.icon("eye-slash", color=None)
    test_icon_image = test_icon.pixmap(DEFAULT_ICON_SIZE).toImage()

    button.PyDMIcon = "eye-slash"
    button_icon = button.icon()
    push_btn_icon_image = button_icon.pixmap(DEFAULT_ICON_SIZE).toImage()

    assert test_icon_image == push_btn_icon_image

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


def test_press_with_relative_filename(qtbot):
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.open(test_ui_path_with_relative_path)
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = main_window.home_widget.relatedDisplayButton
    # Default behavior should be to not follow symlinks (for backwards compat.).
    # Same effect as: button.followSymlinks = False
    qtbot.mouseRelease(button, Qt.LeftButton)

    def check_title():
        assert "Child" in QApplication.instance().main_window.windowTitle()

    qtbot.waitUntil(check_title)


@pytest.mark.skipif(
    sys.platform == "win32" and sys.version_info < (3, 8),
    reason="os.path.realpath on Python 3.7 and prior does not resolve symlinks on Windows",
)
def test_press_with_relative_filename_and_symlink(qtbot, tmp_path):
    symlinked_ui_file = tmp_path / "test_ui_with_relative_path.ui"
    try:
        os.symlink(test_ui_path_with_relative_path, symlinked_ui_file)
    except Exception:
        pytest.skip("Unable to create a symlink for testing purposes.")

    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.open(symlinked_ui_file)
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = main_window.home_widget.relatedDisplayButton
    button.followSymlinks = True
    qtbot.mouseRelease(button, Qt.LeftButton)

    def check_title():
        assert "Child" in QApplication.instance().main_window.windowTitle()

    qtbot.waitUntil(check_title)


def test_no_pydm_app_stylesheet(monkeypatch, qtbot):
    local_is_pydm_app = True

    def is_pydm_app():
        return local_is_pydm_app

    monkeypatch.setattr(
        "pydm.widgets.related_display_button.is_pydm_app",
        is_pydm_app,
    )

    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    qtbot.addWidget(button)

    # In a pydm application, the stylesheet is set on PyDMApplication
    local_is_pydm_app = True
    display1 = button.open_display(test_ui_path)
    assert not display1.styleSheet()

    # In non-pydm applications, we add a stylesheet to the display
    local_is_pydm_app = False
    display2 = button.open_display(test_ui_path)
    assert global_style() in display2.styleSheet()

    # If there was already a stylesheet we need to maintain the original text
    local_is_pydm_app = True
    display3 = button.open_display(test_ui_path_with_stylesheet)
    original_style = display3.styleSheet()
    local_is_pydm_app = False
    display4 = button.open_display(test_ui_path_with_stylesheet)
    assert original_style in display4.styleSheet()
    # And we need to add the global stylesheet too
    assert global_style() in display4.styleSheet()
