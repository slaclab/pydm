import os
import pytest
import logging

from pydm import config
from pydm.utilities import stylesheet
from qtpy.QtWidgets import QApplication

# The path to the stylesheet used in these unit tests
test_stylesheet_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "test_data", "global_stylesheet.css"
)


@pytest.fixture(scope="function")
def save_and_restore_pydm_stylesheet():
    """
    A fixture for ensuring that modifications to the PYDM_STYLESHEET environment variable are restored
    even if the test fails. This will prevent any impact to the user's environment, as well as future tests in the run.
    """
    # Back up the stylesheet related variables so they can be restored after the test
    env_backup = os.getenv("PYDM_STYLESHEET", None)
    backup_global_style_path = stylesheet.GLOBAL_STYLESHEET
    os.environ["PYDM_STYLESHEET"] = ""

    yield

    # Restore the user's original stylesheet
    if env_backup:
        os.environ["PYDM_STYLESHEET"] = env_backup
    stylesheet.GLOBAL_STYLESHEET = backup_global_style_path


def test_stylesheet_apply(qtbot, save_and_restore_pydm_stylesheet):
    assert os.getenv("PYDM_STYLESHEET", None) == ""

    # Retrieve instance of the application so we can test with it
    app = QApplication.instance()
    # Ensure that the app stylesheet is clean
    assert not app.styleSheet()

    stylesheet.clear_cache()

    # Exercise apply stylesheet to app
    stylesheet.apply_stylesheet()

    assert app.styleSheet() is not None

    stylesheet.clear_cache()
    # Exercise when there is no stylesheet available
    stylesheet.GLOBAL_STYLESHEET = "invalid_file.none"
    app.setStyleSheet("")
    assert not app.styleSheet()

    # Test apply stylesheet to app
    stylesheet.apply_stylesheet()

    assert not app.styleSheet()


def test_stylesheet_get_style_data(caplog, save_and_restore_pydm_stylesheet):
    assert os.getenv("PYDM_STYLESHEET", None) == ""

    with caplog.at_level(logging.DEBUG):
        # Cleanup the cache
        stylesheet.clear_cache()

        # Check to ensure that the cache is empty
        assert stylesheet.__style_data is None

        # First test the case in which we don't specify the file
        ret = stylesheet._get_style_data()

        assert ret
        assert stylesheet.__style_data == ret

        # Make sure logging capture the error, and have the correct error
        # message
        assert "Opening the default stylesheet" in caplog.text

        caplog.clear()

        # Exercise the cache
        ret = stylesheet._get_style_data()

        assert ret
        assert stylesheet.__style_data == ret

        assert len(caplog.records) == 0

        caplog.clear()

        # Exercise the cache
        ret = stylesheet._get_style_data()

        assert ret
        assert stylesheet.__style_data == ret

        assert len(caplog.records) == 0

        # Clear the cache
        stylesheet.clear_cache()

        # Exercise the invalid file with fallback
        ret = stylesheet._get_style_data("foo.bar.none")

        # Make sure logging capture the error, and have the correct error message
        assert len(caplog.records) == 2
        assert "Error reading the stylesheet file" in caplog.text
        assert "Opening the default stylesheet" in caplog.text

        caplog.clear()
        stylesheet.clear_cache()

        # Exercise the proper loading
        ret = stylesheet._get_style_data(test_stylesheet_path)
        # Make sure logging capture the error, and have the correct error message
        assert "Opening style file" in caplog.text

        caplog.clear()
        stylesheet.clear_cache()

        # Exercise invalid default file
        stylesheet.GLOBAL_STYLESHEET = "invalid_file.none"
        ret = stylesheet._get_style_data()

        # Make sure logging capture the error, and have the correct error message
        if not config.STYLESHEET:
            assert len(caplog.records) == 1
        else:
            assert len(caplog.records) == 2  # Extra message about existing stylesheet
        assert "Cannot find the default stylesheet" in caplog.text
