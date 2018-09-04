import io
import six
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
