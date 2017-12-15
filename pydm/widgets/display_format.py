import math
import numpy as np

try:
    # unichr is not available on Py3+
    unichr(1)
except NameError:
    unichr = chr


class DisplayFormat(object):
    Default = 0
    String = 1
    Decimal = 2
    Exponential = 3
    Hex = 4
    Binary = 5


def parse_value_for_display(new_value, display_format_type, precision, widget):
    if display_format_type == DisplayFormat.Default:
        return new_value
    elif display_format_type == DisplayFormat.String:
        if isinstance(new_value, np.ndarray):
            new_value = new_value[new_value > 0]
            fmt_string = "{}"*len(new_value)
            r = fmt_string.format(*[unichr(x) for x in new_value])
            return r
        else:
            return new_value
    elif display_format_type == DisplayFormat.Decimal:
        # This case is taken care by the current string formatting
        # routine
        return new_value
    elif display_format_type == DisplayFormat.Exponential:
        fmt_string = "{" + ":.{}e".format(precision) + "}"
        try:
            r = fmt_string.format(new_value)
        except (ValueError, TypeError):
            print("Could not display value {} using displayFormat 'Exponential' at widget named '{}'.".format(new_value, widget.objectName()))
            r = new_value
        return r
    elif display_format_type == DisplayFormat.Hex:
        try:
            r = hex(math.floor(new_value))
        except (ValueError, TypeError):
            print("Could not display value {} using displayFormat 'Hex' at widget named '{}'.".format(new_value, widget.objectName()))
            r = new_value
        return r
    elif display_format_type == DisplayFormat.Binary:
        try:
            r = bin(math.floor(new_value))
        except (ValueError, TypeError):
            print("Could not display value {} using displayFormat 'Binary' at widget named '{}'.".format(new_value, widget.objectName()))
            r = new_value
        return r
