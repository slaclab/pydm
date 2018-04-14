import pytest
from scipy import constants
from ...utilities import units


@pytest.mark.parametrize("typ, expected", [
    ('cm', 'length'),
    ('non_existent', None)
])
def test_find_unittype(typ, expected):
    tp = units.find_unittype(typ)
    assert (tp == expected)


@pytest.mark.parametrize("unit, expected", [
    ('cm', constants.centi),
    ('non_existent', None)
])
def test_find_unit(unit, expected):
    r = units.find_unit(unit)
    assert (r == expected)


@pytest.mark.parametrize("unit, desired, expected", [
    ('m', 'cm', 1/constants.centi),
    ('m', 'rad', None),
    ('non_existent', 'rad', None)
])
def test_convert(unit, desired, expected):
    r = units.convert(unit, desired)
    assert (r == expected)


@pytest.mark.parametrize("unit, expected", [
    ('V', ['MV', 'kV', 'V', 'mV', 'uV']),
    ('foo', None)
])
def test_find_unit_options(unit, expected):
    opts = units.find_unit_options(unit)
    assert (opts == expected)
