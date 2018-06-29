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
    tmp = tempfile.NamedTemporaryFile()
    stylesheet_location = tmp.name

    produce_alarm_stylesheet(stylesheet_location,
                             ["PyDMWidget", "PyDMWritableWidget", "PyDMLabel", "PyDMLineEdit", "PyDMSlider",
                              "PyDMCheckbox"])

    source_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "test_data",
                                    "alarm_stylesheet.css")
    with open(source_file_path) as source:
        with open(tmp.name) as dest:
            diffs = difflib.unified_diff(
                source.readlines(),
                dest.readlines(),
                fromfile='source',
                tofile='dest',
            )
            diff_lines = []
            for line in diffs:
                diff_lines.append(line)
            assert len(diff_lines) == 0
