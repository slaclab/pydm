import io
import six
from string import Template
import json

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
    file : io.StringIO
        File-like object with the proper substitutions.
    """
    with open(file_path) as orig_file:
        text = Template(orig_file.read())
    expanded_text = text.safe_substitute(macros)
    return io.StringIO(six.text_type(expanded_text))


def find_base_macros(widget):
    '''
    Find and return the first set of defined base_macros from this widget or
    its ancestors.
    '''
    while widget is not None:
        if hasattr(widget, 'base_macros'):
            return widget.base_macros
        widget = widget.parent()
    return {}

def parse_macro_string(macro_string):
    macro_string = str(macro_string)
    try:
        macros = json.loads(macro_string)
        return macros
    except ValueError:
        if macro_string.find("=") < 0:
            raise ValueError("Could not parse macro argument as JSON.")
        macros = {}
        for pair in macro_string.split(","):
            key, value = pair.strip().split("=")
            macros[key.strip()] = value.strip()
        return macros
    