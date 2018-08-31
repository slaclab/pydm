import os
import tempfile
import pytest

from ...utilities.macro import substitute_in_file


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
