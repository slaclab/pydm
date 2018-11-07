import os
import pytest
from pydm import Display

# The path to the .ui file used in these tests
test_ui_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "test_data", "test.ui")

def test_display_raises_without_filename():
    """If you don't specify a ui_filename argument, or don't reimplement
    ui_filename(), make sure you get a NotImplementedError."""
    with pytest.raises(NotImplementedError):
        my_display = Display(parent=None)

def test_ui_filename_arg():
    """If you supply a valid filename argument, you shouldn't get any exceptions."""
    my_display = Display(parent=None, ui_filename=test_ui_path)

def test_reimplemented_ui_filename():
    """If you reimplement ui_filename and return a valid filename, you
    shouldn't get any exceptions."""
    class TestDisplay(Display):
        def ui_filename(self):
            return test_ui_path
    my_display = TestDisplay(parent=None)

def test_nonexistant_ui_file_raises():
    with pytest.raises(IOError):
        my_display = Display(parent=None, ui_filename="this_doesnt_exist.ui")
    class TestDisplay(Display):
        def ui_filename(self):
            return "this_doesnt_exist.ui"
    with pytest.raises(IOError):
        my_display = TestDisplay(parent=None)