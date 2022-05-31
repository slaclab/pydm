import os
import pytest
from pydm import Display
from pydm.display import load_py_file

# The path to the .ui file used in these tests
test_ui_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "test_data", "test.ui")

# The path to the .py files used in these tests
no_display_test_py_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "test_data", "no_display_test_file.py")

valid_display_test_py_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "test_data", "valid_display_test_file.py")


def test_ui_filename_arg(qtbot):
    """If you supply a valid filename argument, you shouldn't get any exceptions."""
    my_display = Display(parent=None, ui_filename=test_ui_path)
    qtbot.addWidget(my_display)


def test_reimplemented_ui_filename(qtbot):
    """If you reimplement ui_filename and return a valid filename, you
    shouldn't get any exceptions."""
    class TestDisplay(Display):
        def ui_filename(self):
            return test_ui_path
    my_display = TestDisplay(parent=None)
    qtbot.addWidget(my_display)


def test_nonexistant_ui_file_raises(qtbot):
    with pytest.raises(IOError):
        my_display = Display(parent=None, ui_filename="this_doesnt_exist.ui")

    class TestDisplay(Display):
        def ui_filename(self):
            return "this_doesnt_exist.ui"

    with pytest.raises(IOError):
        my_display = TestDisplay(parent=None)


def test_nonexistent_py_file_raises():
    """ Load a python file that does not exist and confirm the error raised is as expected """
    with pytest.raises(FileNotFoundError):
        load_py_file('this_doesnt_exist.py')


def test_doesnt_inherit_display_raises():
    """ Load a python file that does not inherit from PyDM Display and confirm the error raised is as expected """
    with pytest.raises(ValueError) as error_info:
        load_py_file(no_display_test_py_path)
    assert 'no class inheriting from Display' in str(error_info.value)


def test_load_valid_python_display_file(qtbot):
    """ Verify that loading a valid python only file inheriting from Display works as expected """
    display = load_py_file(valid_display_test_py_path)
    qtbot.addWidget(display)

    # Confirm that the file loaded everything as expected
    assert display.loaded_file() == valid_display_test_py_path
    assert display.ui_filename() == 'test.ui'
    assert display.macros() == {}
    assert display.previous_display is None
    assert display.next_display is None


def test_load_python_file_with_macros(qtbot):
    """ Attempt to add macros to the display while loading the file """
    macros = {'MACRO_1': 7, 'MACRO_2': 'test_string'}
    display = load_py_file(valid_display_test_py_path, macros=macros)
    qtbot.addWidget(display)
    assert display.loaded_file() == valid_display_test_py_path
    assert display.ui_filename() == 'test.ui'
    assert display.macros() == {'MACRO_1': 7, 'MACRO_2': 'test_string'}
