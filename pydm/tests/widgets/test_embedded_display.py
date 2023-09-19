import os
import pytest
import sys
from qtpy.QtWidgets import QApplication

test_ui_path_with_relative_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "../test_data", "test_relative_filename_parent.ui"
)


def test_show_with_relative_filename(qtbot):
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.open(test_ui_path_with_relative_path)
    main_window.setWindowTitle("Embedded Display Test")
    qtbot.addWidget(main_window)
    display = main_window.home_widget.embeddedDisplay

    # Default behavior should be to not follow symlinks (for backwards compat.).
    # Same effect as: display.followSymlinks = False
    def check_embed():
        assert display.embedded_widget is not None

    qtbot.waitUntil(check_embed)


@pytest.mark.skipif(
    sys.platform == "win32" and sys.version_info < (3, 8),
    reason="os.path.realpath on Python 3.7 and prior does not resolve symlinks on Windows",
)
def test_show_with_relative_filename_and_symlink(qtbot, tmp_path):
    symlinked_ui_file = tmp_path / "test_ui_with_relative_path.ui"
    try:
        os.symlink(test_ui_path_with_relative_path, symlinked_ui_file)
    except Exception:
        pytest.skip("Unable to create a symlink for testing purposes.")

    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.open(symlinked_ui_file)
    main_window.setWindowTitle("Embedded Display Test")
    qtbot.addWidget(main_window)
    display = main_window.home_widget.embeddedDisplay
    display.followSymlinks = True

    def check_embed():
        assert display.embedded_widget is not None

    qtbot.waitUntil(check_embed)
