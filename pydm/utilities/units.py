import math

tera = 1e12
giga = 1e9
mega = 1e6
kilo = 1e3
centi = 1e-2
milli = 1e-3
micro = 1e-6
nano = 1e-9
pico = 1e-12
inch = 0.0254
foot = 12 * inch
yard = 3 * foot
minute = 60.0
hour = 60 * minute
day = 24 * hour
week = 7 * day
degree = math.pi / 180

UNITS = {
    "length": {
        "m": 1,
        "cm": centi,
        "mm": milli,
        "um": micro,
        "nm": nano,
        "pm": pico,
        "in": inch,
        "ft": foot,
        "yds": yard,
    },
    "time": {
        "s": 1,
        "ms": milli,
        "us": micro,
        "ns": nano,
        "ps": pico,
        "min": minute,
        "hr": hour,
        "weeks": week,
        "days": day,
    },
    "frequency": {
        "Hz": 1,
        "kHz": kilo,
        "MHz": mega,
        "GHz": giga,
        "THz": tera,
        "mHz": milli,
    },
    "angle": {
        "rad": 1,
        "mrad": milli,
        "urad": micro,
        "nrad": nano,
        "degree": degree,
        "turn": 2 * math.pi,
    },
    "voltage": {
        "V": 1,
        "MV": mega,
        "kV": kilo,
        "mV": milli,
        "uV": micro,
    },
    "current": {
        "A": 1,
        "MA": mega,
        "kA": kilo,
        "mA": milli,
        "uA": micro,
        "nA": nano,
    },
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
        return current / final


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
        units = [choice for choice, _ in sorted(UNITS[tp].items(), key=lambda x: 1 / x[1])]
        return units
    else:
        return None
