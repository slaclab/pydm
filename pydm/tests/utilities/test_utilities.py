from ...utilities import is_pydm_app, path_info, which
from ...PyQt import QtGui
from ...application import PyDMApplication


def test_is_pydm_app():
    app = PyDMApplication()
    assert is_pydm_app(app)
    app.deleteLater()


def test_negative_is_pydm_app():
    app = QtGui.QApplication([])
    assert not is_pydm_app(app)
    app.deleteLater()


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
