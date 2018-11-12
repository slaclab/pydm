import math
import numpy as np

import logging
import warnings

logger = logging.getLogger(__name__)


class DisplayFormat(object):
    Default = 0
    String = 1
    Decimal = 2
    Exponential = 3
    Hex = 4
    Binary = 5


def parse_value_for_display(value, precision, display_format_type=DisplayFormat.Default, string_encoding="utf_8", widget=None):
    try:
        widget_name = widget.objectName()
    except(AttributeError, TypeError):
        widget_name = ""

    if display_format_type == DisplayFormat.Default:
        return value
    elif display_format_type == DisplayFormat.String:
        if isinstance(value, np.ndarray):
            try:
                # Stop at the first zero (EPICS convention)
                # Assume the ndarray is one-dimensional
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    zeros = np.where(value == 0)[0]
                if zeros.size > 0:
                    value = value[:zeros[0]]
                r = value.tobytes().decode(string_encoding)
            except:
                logger.error("Could not decode {0} using {1} at widget named '{2}'.".format(
                    value, string_encoding, widget_name))
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
            logger.error("Could not display value '{0}' using displayFormat 'Exponential' at widget named "
                         "'{1}'.".format(value, widget_name))
            r = value
        return r
    elif display_format_type == DisplayFormat.Hex:
        try:
            r = hex(int(math.floor(value)))
        except (ValueError, TypeError):
            logger.error("Could not display value '{0}' using displayFormat 'Hex' at widget named "
                         "'{1}'.".format(value, widget_name))
            r = value
        return r
    elif display_format_type == DisplayFormat.Binary:
        try:
            r = bin(int(math.floor(value)))
        except (ValueError, TypeError):
            logger.error("Could not display value '{0}' using displayFormat 'Binary' at widget named "
                         "'{1}'.".format(value, widget_name))
            r = value
        return r
