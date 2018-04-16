import tempfile
import os
from string import Template


def substitute_in_file(file_path, macros):
    """
    Substitute the macros given by ${name} at the given file with the entries on the `macros` dictionary.

    Parameters
    ----------
    file_path : str
        The path to the file in which to substitute
    macros : dict
        Dictionary containing macro name as key and value as what will be substituted.
    Returns
    -------
    temp_filename : str
        The path to the new generated file with the proper substitutions.
    """
    temporary_fd, temp_filename = tempfile.mkstemp()
    with open(file_path) as orig_file:
        with os.fdopen(temporary_fd, 'w') as temporary_file:
            t = Template(orig_file.read())
            temporary_file.write(t.safe_substitute(macros))
    return temp_filename
