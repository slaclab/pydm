import math
import numpy as np


class DisplayFormat(object):
    Default = 0
    String = 1
    Decimal = 2
    Exponential = 3
    Hex = 4
    Binary = 5


def parse_value_for_display(value, precision, display_format_type=DisplayFormat.Default, string_encoding="utf_8", widget=None):
    if display_format_type == DisplayFormat.Default:
        return value
    elif display_format_type == DisplayFormat.String:
        if isinstance(value, np.ndarray):
            try:
                r = value.tobytes().decode(string_encoding)
                print("Could not decode {} using {} at widget named '{}'.".format(value, string_encoding, widget.objectName()))
            except:
                return value
            return r
        else:
            return value
    elif display_format_type == DisplayFormat.Decimal:
        # This case is taken care by the current string formatting
        # routine
        return value
    elif display_format_type == DisplayFormat.Exponential:
        fmt_string = "{" + ":.{}e".format(precision) + "}"
        try:
            r = fmt_string.format(value)
        except (ValueError, TypeError):
            print("Could not display value {} using displayFormat 'Exponential' at widget named '{}'.".format(value, widget.objectName()))
            r = value
        return r
    elif display_format_type == DisplayFormat.Hex:
        try:
            r = hex(math.floor(value))
        except (ValueError, TypeError):
            print("Could not display value {} using displayFormat 'Hex' at widget named '{}'.".format(value, widget.objectName()))
            r = value
        return r
    elif display_format_type == DisplayFormat.Binary:
        try:
            r = bin(math.floor(value))
        except (ValueError, TypeError):
            print("Could not display value {} using displayFormat 'Binary' at widget named '{}'.".format(value, widget.objectName()))
            r = value
        return r
