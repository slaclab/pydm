import os
import platform
import tempfile

from ...utilities import is_pydm_app, path_info, which, find_display_in_path
from ...PyQt import QtGui


def test_is_pydm_app(qapp):
    assert is_pydm_app(qapp)


def test_negative_is_pydm_app():
    assert not is_pydm_app(QtGui.QLabel())


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
    print("temp.name: ", file_path)
    direc, fname, _ = path_info(file_path)

    # Try to find the file as is... is should not find it.
    assert(find_display_in_path(fname) is None)

    # Try to find the file passing the path
    assert(find_display_in_path(fname, mode=None, path=direc) == file_path)

    # Try to find the file passing the path but relative name
    rel_name = ".{}{}".format(os.sep, fname)
    expected = "{}{}{}".format(direc, os.sep, rel_name)
    assert (find_display_in_path(rel_name, mode=None, path=direc) == expected)

def test_which():
    if platform.system() == 'Windows':
        out = which('ping')
        assert (out.lower() == 'c:\windows\system32\ping.exe')

        out = which('C:\Windows\System32\PING.EXE')
        assert (out.lower() == 'c:\windows\system32\ping.exe')
    else:
        out = which('ls')
        assert (out == '/bin/ls')

        out = which('/bin/ls')
        assert (out == '/bin/ls')

    out = which('non_existant_binary')
    assert (out is None)

    out = which('/bin/non_existant_binary')
    assert (out is None)

    out = which('ls', path='')
    assert (out is None)
