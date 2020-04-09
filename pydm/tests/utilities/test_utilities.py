import os
import platform
import tempfile
from qtpy import QtWidgets

from pydm.utilities import (is_pydm_app, path_info, which, find_display_in_path,
                          is_qt_designer, nested_dict_get, data_callback)
from pydm.application import PyDMApplication

def test_is_pydm_app(qapp):
    assert is_pydm_app(app=None) == isinstance(qapp, PyDMApplication)
    assert is_pydm_app(qapp) == isinstance(qapp, PyDMApplication)


def test_negative_is_pydm_app():
    assert not is_pydm_app(QtWidgets.QLabel())


def test_is_qt_designer():
    assert not is_qt_designer()


def test_path_info():
    dir_name, file_name, args = path_info('/bin/ls -l -a')
    assert (dir_name == '/bin')
    assert (file_name == 'ls')
    assert (args == ['-l', '-a'])

    dir_name, file_name, args = path_info('/bin/ls')
    assert (dir_name == '/bin')
    assert (file_name == 'ls')
    assert (args == [])


def test_find_display_in_path():
    temp, file_path = tempfile.mkstemp(suffix=".ui", prefix="display_")
    direc, fname, _ = path_info(file_path)
    # Try to find the file as is... is should not find it.
    assert(find_display_in_path(fname) is None)

    # Try to find the file passing the path
    disp_path = find_display_in_path(fname, mode=None, path=direc)
    assert(disp_path == file_path)

    # Try to find the file passing the path but relative name
    rel_name = ".{}{}".format(os.sep, fname)
    expected = "{}{}{}".format(direc, os.sep, rel_name)
    disp_path = find_display_in_path(rel_name, mode=None, path=direc)
    assert (disp_path == expected)


def test_which():
    if platform.system() == 'Windows':
        out = which('ping')
        assert (out.lower() == 'c:\\windows\\system32\\ping.exe')

        out = which('C:\\Windows\\System32\\PING.EXE')
        assert (out.lower() == 'c:\\windows\\system32\\ping.exe')
    else:
        out = which('ls')
        assert ('ls' in out)

        out = which('/bin/ls')
        assert ('ls' in out)

    out = which('non_existant_binary')
    assert (out is None)

    out = which('/bin/non_existant_binary')
    assert (out is None)

    out = which('ls', path='')
    assert (out is None)


def test_nested_dict_get():
    data = {
        'X': {
            'inner': {
                'foo': 1,
                'bar': True
            },
            'deep': [
                {'entry1': 'value'},
                {'entry2': 123.45},
            ],
            'value': [0, 1, 2, 3, 4]
        },
        'Y': {
            'value': [5, 6, 7, 8, 9]
        }
    }

    assert nested_dict_get(data, 'X.inner.foo'.split('.')) == 1
    assert nested_dict_get(data, 'X.inner.bar'.split('.')) == True
    assert nested_dict_get(data, 'X.deep[0].entry1'.split('.')) == 'value'
    assert nested_dict_get(data, 'Y.value'.split('.')) == [5, 6, 7, 8, 9]
    assert nested_dict_get(data, 'Y.value[-1]'.split('.')) == 9
    assert nested_dict_get(data, 'Y.value[:-2]'.split('.')) == [5, 6, 7]
    assert nested_dict_get(data, 'Invalid'.split('.')) is None
    assert nested_dict_get(data, 'Y.Invalid'.split('.')) is None
    assert nested_dict_get(data, 'Y.value[100]'.split('.')) is None


def test_data_callback():
    class MyWidget:
        def __init__(self):
            self.hit = {}

        def clear_hit_map(self):
            self.hit = {}

        def value_changed(self, new_val):
            self.hit['value_changed'] = new_val

        def connection_changed(self, new_val):
            self.hit['connection_changed'] = new_val

        def test_method(self, new_val):
            self.hit['test_method'] = new_val

    widget = MyWidget()
    introspection = {'CONNECTION': 'status.conn',
                     'VALUE': 'VaLuE',
                     'TEST': 'test',
                     'KEY': 'k',
                     'foo': False}

    mapping = {'CONNECTION': widget.connection_changed,
               'VALUE': 'value_changed',
               'KEY': False}

    data_callback(widget, None, introspection, mapping)
    assert widget.hit == {}

    widget.clear_hit_map()
    data = {'status': {'conn': False}, 'VaLuE': 123.456}
    data_callback(widget, data, introspection, mapping)
    assert 'value_changed' in widget.hit
    assert widget.hit['value_changed'] == 123.456
    assert 'connection_changed' in widget.hit
    assert widget.hit['connection_changed'] is False
