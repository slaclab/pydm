import tempfile
import os
from string import Template

def substitute_in_file(file_path, macros):
    temporary_fd, temp_filename = tempfile.mkstemp()
    with open(file_path) as orig_file:
        with os.fdopen(temporary_fd, 'w') as temporary_file:
            t = Template(orig_file.read())
            temporary_file.write(t.safe_substitute(macros))
    return temp_filename
