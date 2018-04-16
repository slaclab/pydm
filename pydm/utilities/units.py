from scipy import constants

UNITS = {'length':   {'m': 1,
                      'cm': constants.centi,
                      'mm': constants.milli,
                      'um': constants.micro,
                      'nm': constants.nano,
                      'pm': constants.pico,
                      'in': constants.inch,
                      'ft': constants.foot,
                      'yds': constants.yard,
                      },
         'time':    {'s': 1,
                     'ms': constants.milli,
                     'us': constants.micro,
                     'ns': constants.nano,
                     'ps': constants.pico,
                     'min': constants.minute,
                     'hr': constants.hour,
                     'weeks': constants.week,
                     'days': constants.day,
                     },
         'frequency': {'Hz': 1,
                       'kHz': constants.kilo,
                       'MHz': constants.mega,
                       'GHz': constants.giga,
                       'THz': constants.tera,
                       'mHz': constants.milli,
                       },
         'angle':   {'rad': 1,
                     'mrad': constants.milli,
                     'urad': constants.micro,
                     'nrad': constants.nano,
                     'degree': constants.degree,
                     'turn': 2*constants.pi,
                     },
         'voltage': {'V': 1,
                     'MV': constants.mega,
                     'kV': constants.kilo,
                     'mV': constants.milli,
                     'uV': constants.micro,
                     },
         'current': {'A': 1,
                     'MA': constants.mega,
                     'kA': constants.kilo,
                     'mA': constants.milli,
                     'uA': constants.micro,
                     'nA': constants.nano,
                     }
         }


def find_unittype(unit):
    """
    Find the type of a unit string.

    Parameters
    ----------
    unit : str
        The unit string

    Returns
    -------
    tp : str
        The unit type name or None if not found.
    """
    for tp in UNITS.keys():
        if unit in UNITS[tp].keys():
            return tp
    return None


def find_unit(unit):
    """
    Find the conversion of a unit string.

    Parameters
    ----------
    unit : str
        The unit string

    Returns
    -------
    float or None
        The unit value relative to the standard or None if not found.
    """
    tp = find_unittype(unit)
    if tp:
        return UNITS[tp][unit]
    else:
        return None


def convert(unit, desired):
    """
    Find the conversion rate of two different unit strings.

    Parameters
    ----------
    unit : str
        The current unit string
    desired : str
        The desired unit string

    Returns
    -------
    float or None
        The relation between unit and desired or None if not found.
    """
    current = find_unit(unit)
    final = find_unit(desired)

    if find_unittype(unit) != find_unittype(desired):
        return None

    if current and final:
        return current/final


def find_unit_options(unit):
    """
    Find the options for a given unit.

    Parameters
    ----------
    unit : str
        The unit string

    Returns
    -------
    list or None
        The list of similar units in crescent order or None if not found.
    """
    tp = find_unittype(unit)
    if tp:
        units = [choice for choice, _ in
                 sorted(UNITS[tp].items(), key=lambda x: 1/x[1])]
        return units
    else:
        return None
