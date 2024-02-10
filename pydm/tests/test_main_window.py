import os

from pydm import Display, PyDMApplication
from qtpy import uic
from unittest.mock import MagicMock, patch

# The path to the .ui file for creating a main window
test_ui_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data", "test.ui")


@patch("qtpy.uic.compileUi", wraps=uic.compileUi)
def test_reload_display(wrapped_compile_ui: MagicMock, qapp: PyDMApplication) -> None:
    """Verify that when a user reloads a PyDM window the underling display's ui file is actually reloaded"""
    display = Display(parent=None, ui_filename=test_ui_path)

    qapp.make_main_window()
    qapp.main_window.set_display_widget(display)

    # When the display is first created and loaded the underlying ui file gets compiled
    wrapped_compile_ui.assert_called_once()

    # Reloading should force a re-compile of the ui file to ensure any changes are picked up
    qapp.main_window.reload_display(True)
    assert wrapped_compile_ui.call_count == 2
