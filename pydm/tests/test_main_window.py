import os

from pydm import PyDMApplication
from pydm.display import Display, clear_compiled_ui_file_cache
from qtpy import uic
from unittest.mock import MagicMock, patch

# The path to the .ui file for creating a main window
test_ui_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data", "test.ui")


@patch("qtpy.uic.compileUi", wraps=uic.compileUi)
def test_reload_display(wrapped_compile_ui: MagicMock, qapp: PyDMApplication) -> None:
    """Verify that when a user reloads a PyDM window the underling display's ui file is actually reloaded"""
    clear_compiled_ui_file_cache()  # Ensure other tests have not already compiled our test file before we start

    try:
        display = Display(parent=None, ui_filename=test_ui_path)

        qapp.make_main_window()
        qapp.main_window.set_display_widget(display)

        # When the display is first created and loaded the underlying ui file gets compiled
        wrapped_compile_ui.assert_called_once()

        # Reloading should force a re-compile of the ui file to ensure any changes are picked up
        qapp.main_window.reload_display(True)
        assert wrapped_compile_ui.call_count == 2
    finally:
        clear_compiled_ui_file_cache()


def test_menubar_text(qapp: PyDMApplication) -> None:
    """Verify main-window displays expected text in its menubar dropdown items"""
    # only testing text update of "Enter/Exit Fullscreen" menu-item for now, this can be expanded later
    display = Display(parent=None)

    qapp.make_main_window()
    qapp.main_window.set_display_widget(display)

    action = qapp.main_window.ui.actionEnter_Fullscreen
    # make sure we start in not fullscreen view
    qapp.main_window.showNormal()
    assert action.text() == "Enter Fullscreen"
    # click the menu-item to go into fullscreen view
    action.trigger()
    assert action.text() == "Exit Fullscreen"
