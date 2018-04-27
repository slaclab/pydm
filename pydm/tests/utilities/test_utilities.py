import platform

from ...utilities import is_pydm_app, path_info, which
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
