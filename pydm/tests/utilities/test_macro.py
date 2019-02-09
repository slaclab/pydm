import os
import tempfile
import pytest
import json

from ...utilities.macro import substitute_in_file, parse_macro_string


@pytest.mark.parametrize("text, macros, expected", [
    (
            'This is a ${what} to ensure that macros work. ${A} ${B} ${C}',
            {'what': 'test', 'A': 'X', 'B': 'Y', 'C': 'Z'},
            'This is a test to ensure that macros work. X Y Z'
    ),
    (
            'This is a ${what} to ensure that macros work. ${A} ${B} ${C}',
            {'what': 'test', 'A': 'X', 'B': 'Y', 'C': 'Z', 'D': 'W'},
            'This is a test to ensure that macros work. X Y Z'
    ),
    (
            'This is a ${what} to ensure that macros work. ${A} ${B} ${C}',
            {'what': 'test', 'A': 'X', 'B': 'Y'},
            'This is a test to ensure that macros work. X Y ${C}'
    )
])
def test_substitute_in_file(text, macros, expected):
    fd, name = tempfile.mkstemp(text=True)
    # use a context manager to open the file at that path and close it again
    with open(name, 'w') as f:
        f.write(text)
    # close the file descriptor
    os.close(fd)

    nf = substitute_in_file(name, macros)
    nt = nf.read()
    assert (nt == expected)

@pytest.mark.parametrize("macro_string, expected_dict", [
    ('{"A": "1", "B": "2"}', {"A": "1", "B": "2"}),
    ("A=1,B=2", {"A": "1", "B": "2"}),
    ("A=$(other_macro),B=2,C=3", {"A": "$(other_macro)", "B": "2", "C": "3"}),
    ("A=$(other_macro=3)", {"A": "$(other_macro=3)"}),
    ("TITLE='1,2', B=2, C=3", {"TITLE": "1,2", "B": "2", "C": "3"}),
    ("TITLE=1\,2,B=2,C=3", {"TITLE": "1,2", "B": "2", "C": "3"}),
    ('TITLE="e=mc^2",B=2,C=3', {"TITLE": "e=mc^2", "B": "2", "C": "3"}),
    ('', {}),
    (None, {})
])
def test_macro_parser(macro_string, expected_dict):
    """
    Test the parser, using a couple of normal cases, and a bunch of perverse
    macro strings that only some insane macro genius (or huge macro idiot) 
    would ever attempt.
    """
    assert parse_macro_string(macro_string) == expected_dict
