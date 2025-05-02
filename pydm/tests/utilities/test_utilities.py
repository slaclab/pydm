import logging
import os
import platform
import tempfile

from qtpy import QtWidgets

from pydm.utilities import find_display_in_path, find_file, is_pydm_app, is_qt_designer, log_failures, path_info, which

logger = logging.getLogger(__name__)


def test_is_pydm_app(qapp):
    assert is_pydm_app(qapp)


def test_negative_is_pydm_app():
    assert not is_pydm_app(QtWidgets.QLabel())


def test_is_qt_designer():
    assert not is_qt_designer()


def test_path_info():
    dir_name, file_name, args = path_info("/bin/ls -l -a")
    assert dir_name == "/bin"
    assert file_name == "ls"
    assert args == ["-l", "-a"]

    dir_name, file_name, args = path_info("/bin/ls")
    assert dir_name == "/bin"
    assert file_name == "ls"
    assert args == []


def test_find_display_in_path():
    temp, file_path = tempfile.mkstemp(suffix=".ui", prefix="display_")
    direc, fname, _ = path_info(file_path)
    # Try to find the file as is... it should not find it.
    assert find_display_in_path(fname) is None

    # Try to find the file passing the path
    disp_path = find_display_in_path(fname, mode=None, path=direc)
    assert disp_path == file_path

    # Try to find the file passing the path but relative name
    rel_name = ".{}{}".format(os.sep, fname)
    expected = "{}{}{}".format(direc, os.sep, rel_name)
    disp_path = find_display_in_path(rel_name, mode=None, path=direc)
    assert disp_path == expected


def test_find_file():
    parent_lvl1 = tempfile.mkdtemp()
    parent_lvl2 = tempfile.mkdtemp(dir=parent_lvl1)
    temp, file_path = tempfile.mkstemp(suffix=".ui", prefix="display_", dir=parent_lvl2)
    direc, fname, _ = path_info(file_path)
    # Try to find the file as is... it should not find it.
    assert find_file(fname) is None

    # Try to find the file under base_path
    disp_path = find_file(fname, base_path=direc)
    assert disp_path == file_path

    # Try to find the file under the parent folder without recursion (fail)
    disp_path = find_file(fname, base_path=parent_lvl1)
    assert disp_path == None

    # Try to find the file under the parent folder with recursion (succeed)
    disp_path = find_file(fname, base_path=parent_lvl1, subdir_scan_enabled=True)
    assert disp_path == file_path


def test_which():
    if platform.system() == "Windows":
        out = which("ping")
        assert out.lower() == r"c:\windows\system32\ping.exe"

        out = which(r"C:\Windows\System32\PING.EXE")
        assert out.lower() == r"c:\windows\system32\ping.exe"
    else:
        out = which("ls")
        assert "ls" in out

        out = which("/bin/ls")
        assert "ls" in out

    out = which("non_existant_binary")
    assert out is None

    out = which("/bin/non_existant_binary")
    assert out is None

    out = which("ls", path="")
    assert out is None


def test_log_failure_capture(caplog):
    @log_failures(logger)
    def inner():
        raise ValueError()

    with caplog.at_level(logging.WARNING):
        result = inner()

    assert result is None

    assert len(caplog.records) == 1
    assert "Failed to run inner" in str(caplog.records[0])


def test_log_failure_pass(caplog):
    @log_failures(logger)
    def inner():
        return 5

    with caplog.at_level(logging.WARNING):
        result = inner()

    assert result == 5
    assert not caplog.records
