import io
import six
from string import Template
import json
from typing import Tuple

from qtpy.QtWidgets import QWidget

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


def substitute_in_widget(
    widget: QWidget,
    macros: dict[str, str],
    source_file: str
) -> QWidget:
    """
    Performs substitution on a created widget with un-substituted strings.

    This mutates the widget in place and also returns it.

    In cases where all macros are in string properties and we are re-using
    the same template many times, this is a much faster way to apply macros.

    Parameters
    ----------
    widget : QWidget
        Any widget with macros in string properties.
    properties : list of str
        The exact properties to replace in.
    macros : dict from str to str
        Mapping from macro string to replacement value.

    Returns
    -------
    widget : QWidget
        The same widget back again, with templates filled.
    """
    for child_name, prop, template in _get_macro_targets(widget, source_file):
        child_widget = getattr(widget, child_name)
        child_widget.setProperty(
            prop,
            template.safe_substitute(macros)
        )
    print(f'did macro subs for {widget}')
    return widget


_macro_target_cache = {}


def _get_macro_targets(
    widget: QWidget,
    source_file: str,
) -> Tuple[Tuple[str, str, Template]]:
    try:
        return _macro_target_cache[source_file]
    except KeyError:
        ...
    targets = []
    for obj_name, obj in widget.__dict__.items():
        if not isinstance(obj, QWidget):
            continue
        meta_obj = obj.metaObject()
        for index in range(meta_obj.propertyCount()):
            meta_property = meta_obj.property(index)
            if meta_property.typeName() == 'QString':
                prop_name = meta_property.name()
                value = obj.property(prop_name)
                if "${" in obj.property(prop_name):
                    targets.append((obj_name, prop_name, Template(value)))
    targets = tuple(targets)
    _macro_target_cache[source_file] = targets
    return targets


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
    
