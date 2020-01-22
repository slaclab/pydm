import io
import six
from string import Template
import json

# Macro parsing states
PRE_NAME = 0
IN_NAME = 1
PRE_VAL = 2
IN_VAL = 3


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
    template = template_for_file(file_path)
    return replace_macros_in_template(template, macros)


def replace_macros_in_template(template, macros):
    curr_template = template
    prev_template = Template("")
    expanded_text = ""
    for i in range(100):
        expanded_text = curr_template.safe_substitute(macros)
        if curr_template.template == prev_template.template:
            break
        prev_template = curr_template
        curr_template = Template(expanded_text)
    return io.StringIO(six.text_type(expanded_text))


def template_for_file(file_path):
    with open(file_path) as orig_file:
        text = Template(orig_file.read())
    return text


def parse_macro_string(macro_string):
    """Parses a macro string and returns a dictionary.
    First, this method attempts to parse the string as JSON.
    If that fails, it attempts to parse it as an EPICS-style
    macro string.  The parsing algorithm for that case is very
    closely based on macParseDefns in libCom/macUtil.c"""
    if not macro_string:
        return {}

    macro_string = str(macro_string)

    try:
        macros = json.loads(macro_string)
        return macros
    except ValueError:
        if "=" not in macro_string:
            raise ValueError("Could not parse macro argument as JSON.")
        macros = {}
        state = PRE_NAME
        quote = None
        name_start = None
        name_end = None
        val_start = None
        val_end = None
        for (i,c) in enumerate(macro_string):
            if quote:
                if c == quote:
                    quote = False
            elif c == "'" or c == '"':
                quote = c
                continue
            escape = macro_string[i-1] == "\\"
            if state == PRE_NAME:
                if (not quote) and (not escape) and (c.isspace() or c == ","):
                    continue
                name_start = i
                state = IN_NAME
            elif state == IN_NAME:
                if quote or escape:
                    continue
                if c == "=" or c == ",":
                    name_end = i
                    state = PRE_VAL
            elif state == PRE_VAL:
                if (not quote) and (not escape) and c.isspace():
                    continue
                val_start = i
                state = IN_VAL
                if i == len(macro_string)-1:
                    val_end = i+1
            elif state == IN_VAL:
                if quote or escape:
                    continue
                if c == ",":
                    val_end = i
                    state = PRE_NAME
                elif i == len(macro_string)-1:
                    val_end = i+1
                    state = PRE_NAME
                else:
                    continue
            if not (None in (name_start, name_end, val_start, val_end)):
                key = macro_string[name_start:name_end].strip().replace("\\", "")
                val = macro_string[val_start:val_end].strip('"\'').replace("\\", "")
                macros[key] = val
                name_start = None
                name_end = None
                val_start = None
                val_end = None
                state = PRE_NAME
        return macros
    