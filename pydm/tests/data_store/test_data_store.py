import pytest

from pydm.data_store import _DataStore, DataKeys


def test_construct():
    ds = _DataStore()
    assert ds._data == {}
    assert ds._introspection == {}


def test_crud():
    ds = _DataStore()

    data = None
    intro = None
    ds.update(address='addr', data=data, introspection=intro)
    assert ds.fetch_with_introspection('addr') == (None, None)

    data = {'foo': 'bar', 'test': 12.123}
    intro = {'VALUE': 'foo', 'CONNECTION': 'test'}
    ds.update(address='addr', data=data, introspection=intro)
    assert ds.fetch_with_introspection('addr') == (data, intro)
    assert ds['addr'] == data

    new_data = {'int': 1, 'float': 1.23, 'bool': True}
    new_intro = {'VALUE': 'int'}
    ds['addr'] = (new_data, new_intro)
    assert ds.fetch_with_introspection('addr') == (new_data, new_intro)

    ds['addr'] = data
    assert ds.fetch_with_introspection('addr') == (data, new_intro)

    with pytest.raises(ValueError):
        ds['addr'] = 1

    ds.remove('addr')
    assert ds.fetch_with_introspection('addr') == (None, None)


def test_data_keys():
    intro = {'CONNECTION': 'conn',
             'VALUE': 'val',
             'SEVERITY': 'sev',
             'WRITE_ACCESS': 'write.access',
             'ENUM_STRINGS': 'enum.strings[0]',
             'UNIT': 'not.an.engineering.unit',
             'PRECISION': 'prec',
             'UPPER_LIMIT': 'tiger_uppercut',
             'LOWER_LIMIT': 'tiger_lowercut?',
             }

    gen_intro = DataKeys.generate_introspection_for(
        connection_key='conn', value_key='val',
        severity_key='sev', write_access_key='write.access',
        enum_strings_key='enum.strings[0]', unit_key='not.an.engineering.unit',
        precision_key='prec', upper_limit_key='tiger_uppercut',
        lower_limit_key='tiger_lowercut?'
    )

    assert intro == gen_intro
