import os
import weakref
import gc

from pydm import PyDMApplication
from pydm.display import Display, clear_compiled_ui_file_cache
from qtpy import uic
from unittest.mock import MagicMock, patch
from pydm.utilities import ACTIVE_QT_WRAPPER, QtWrapperTypes

# The path to the .ui file for creating a main window
test_ui_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data", "test.ui")

if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYQT5:

    @patch("qtpy.uic.compileUi", wraps=uic.compileUi)
    def test_reload_display_pyqt5(wrapped_compile_ui: MagicMock, qapp: PyDMApplication) -> None:
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

else:  # pyside6
    # In pyside6 to compile ui files we need to run the 'pyside6-uic' tool as a subprocess,
    # but can't seem to mock "subprocess.run" here without things blowing up, so for now lets just test that
    # the 'reload_display' function can at least be called without throwing an error in pyside6.
    def test_reload_display_pyside6(qapp: PyDMApplication) -> None:
        """Verify that when a user reloads a PyDM window, the underlying display's UI file is actually
        recompiled with pyside6-uic"""
        clear_compiled_ui_file_cache()  # Ensure other tests have not already compiled our test file before we start

        try:
            display = Display(parent=None, ui_filename=test_ui_path)

            qapp.make_main_window()
            qapp.main_window.set_display_widget(display)

            # Try reloading things
            qapp.main_window.reload_display(True)

        finally:
            clear_compiled_ui_file_cache()


def test_reload_cleans_up_display(qapp: PyDMApplication):
    """When calling reload_display() on the main window, verify the original display is entirely replaced by the
    refreshed version. There should be no remaining references to the original one."""
    qapp.make_main_window()
    qapp.main_window.open(test_ui_path)
    display_widget_ref = weakref.ref(qapp.main_window.display_widget())

    # Reloading should replace the existing display_widget with a new refreshed version
    qapp.main_window.reload_display(True)

    # After the reload there should be no more references to the original display so this will garbage collect it
    gc.collect()

    # With no more references, the weakref should be cleaned up
    assert display_widget_ref() is None


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
