# Unit Test for the alarm stylesheet generator

import pytest

import os
import tempfile
import difflib

from ...utilities.generate_stylesheet_file import produce_alarm_stylesheet


def test_produce_alarm_stylesheet():
    """
    Test the generation of a stylesheet with all the combinations of alarm settings for multiple widgets.

    Expectations:
    For each widget, all the style combinations for alarm sensitivities, i.e. border and content, will be generated
    into a file.
    """
    stylesheet_location = tempfile.mkstemp(prefix="pydm_test_generate_stylesheet_file")[1]

    produce_alarm_stylesheet(stylesheet_location,
                             ["PyDMWidget", "PyDMWritableWidget", "PyDMLabel", "PyDMLineEdit", "PyDMSlider",
                              "PyDMCheckbox"])

    source_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "test_data",
                                    "alarm_stylesheet.css")

    with open(source_file_path) as source:
        with open(stylesheet_location) as dest:
            diffs = set(source).difference(dest)
    assert len(diffs) == 0

    try:
        os.remove(stylesheet_location)
    except:
        # Ignore the "[Error 32] The process cannot access the file because it is being used by another process"
        # error on Windows, when the test is run as a non-Administrator in a Windows test session
        pass
