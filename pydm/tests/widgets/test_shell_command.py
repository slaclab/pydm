# Unit Tests for the Shell Command widget class

import pytest

import platform
from logging import ERROR

from qtpy import QtCore
from qtpy.QtCore import QSize

from ...widgets.shell_command import PyDMShellCommand
from ...utilities import IconFont


# --------------------
# POSITIVE TEST CASES
# --------------------

@pytest.mark.parametrize("command", [
    "ping",
    "",
    None,
])
def test_construct(qtbot, command):
    """
    Test the construct of the widget.

    Expectations:
    The widget is initialized with all the expected default values for its properties, including its icon and mouse
    cursor.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    command : str
        The shell command to be executed when the widget is pressed

    """
    pydm_shell_command = PyDMShellCommand(command=command)
    qtbot.addWidget(pydm_shell_command)

    assert pydm_shell_command._command == command
    assert pydm_shell_command._allow_multiple is False
    assert pydm_shell_command.process is None
    assert pydm_shell_command._show_icon is True

    DEFAULT_ICON_NAME = "cog"
    DEFAULT_ICON_SIZE = QSize(16, 16)

    default_icon = IconFont().icon(DEFAULT_ICON_NAME)

    default_icon_pixmap = default_icon.pixmap(DEFAULT_ICON_SIZE)
    shell_cmd_icon_pixmap = pydm_shell_command.icon().pixmap(DEFAULT_ICON_SIZE)

    assert shell_cmd_icon_pixmap.toImage() == default_icon_pixmap.toImage()
    assert pydm_shell_command.cursor().pixmap().toImage() == default_icon_pixmap.toImage()


@pytest.mark.parametrize("currently_show_icon, to_show_icon", [
    (True, False),
    (False, True),
    (True, True),
    (False, False),
    (None, True),
    (None, False),
    (True, None),
    (False, None),
    (None, None),
])
def test_show_icon(qtbot, currently_show_icon, to_show_icon):
    """
    Test the widget's show icon setting.

    Expectations:
    The widget will retain the show icon setting as it is set.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    currently_show_icon : bool
        The current show icon setting (True is to show the icon; None otherwise)
    to_show_icon : bool
        The next show icon setting (True is to show the icon; None otherwise)
    """
    pydm_shell_command = PyDMShellCommand()
    qtbot.addWidget(pydm_shell_command)

    pydm_shell_command.showIcon = currently_show_icon
    assert pydm_shell_command.showIcon == currently_show_icon

    pydm_shell_command.showIcon = to_show_icon
    assert pydm_shell_command.showIcon == to_show_icon


@pytest.mark.parametrize("currently_allowed, to_allow", [
    (True, False),
    (False, True),
    (True, True),
    (False, False),
    (None, True),
    (None, False),
    (True, None),
    (False, None),
    (None, None),
])
def test_allow_multiple_execs(qtbot, currently_allowed, to_allow):
    """
    Test the widget's multiple command execution setting.

    Expectations:
    The widget will retain the multiple command execution setting as it is set.

    Parameters
    ----------
    qtbot : fixture
       Window for widget testing
    currently_allowed : bool
       The current  multiple command execution setting (True is to allow the multiple executions; None otherwise)
    to_show_icon : bool
       The next multiple command execution setting (True is to allow the multiple executions; None otherwise)
    """
    pydm_shell_command = PyDMShellCommand()
    qtbot.addWidget(pydm_shell_command)

    pydm_shell_command.allowMultipleExecutions = currently_allowed
    assert pydm_shell_command.allowMultipleExecutions == currently_allowed

    pydm_shell_command.allowMultipleExecutions = to_allow
    assert pydm_shell_command.allowMultipleExecutions == to_allow


@pytest.mark.parametrize("current_cmd, next_cmd", [
    ("ping", "pong"),
    ("ping", "ping"),
    ("ping", "ping"),
    ("ping", None),
    ("", "ping"),
    ("", ""),
    (None, "ping"),
    (None, ""),
    (None, None)
])
def test_get_set_command(qtbot, current_cmd, next_cmd):
    """
    Test the widget's capability to set the shell command to execute.

    Expectations:
    The widget will retain the shell command as set.

    Parameters
    ----------
    qtbot : fixture
       Window for widget testing
    current_cmd : str
        The current shell command being set for the widget to execute
    next_cmd : str
        The next shell command to set for the widget to execute
    """
    pydm_shell_command = PyDMShellCommand()
    qtbot.addWidget(pydm_shell_command)

    pydm_shell_command.command = current_cmd
    assert pydm_shell_command.command == current_cmd

    pydm_shell_command.command = next_cmd
    assert pydm_shell_command.command == next_cmd


@pytest.mark.parametrize("cmd, val", [
    ("choice /c yn /d n /t 0" if platform.system() == "Windows" else "sleep 0",
        2 if platform.system() == "Windows" else 0),
    ("pydm_shell_invalid_command_test invalid command", None),
    ("", None),
    (None, None),
])
def test_mouse_release_event(qtbot, caplog, cmd, val):
    """
    Test to ensure the widget's triggering of the Mouse Release event, which will also execute the shell command.

    Expectations:
    1. The mouse release will trigger the current shell command being assigned to the widget to execute
    2. If the command is not valid, there will be an error message in the log
    3. If the command is valid, there will be output in stdout (the result could be a success or failure, but at least
        the command will send out text to stdout)
    4. If the command is None or empty, there will be no output to stdout.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    caplog : fixture
        To capture the log messages
    cmd : str
        The shell command for the widget to execute
    val : int
        The expected exit code.
    """
    pydm_shell_command = PyDMShellCommand()
    qtbot.addWidget(pydm_shell_command)

    pydm_shell_command.command = cmd
    qtbot.mouseClick(pydm_shell_command, QtCore.Qt.LeftButton)

    if cmd:
        if "invalid" not in cmd:
            ret = pydm_shell_command.process.wait()
            assert ret == val
        else:
            for record in caplog.records:
                assert record.levelno == ERROR
            assert "Error in command" in caplog.text
    else:
        assert pydm_shell_command.process is None


@pytest.mark.parametrize("cmd, val", [
    ("choice /c yn /d n /t 0" if platform.system() == "Windows" else "sleep 0",
        2 if platform.system() == "Windows" else 0),
    ("pydm_shell_invalid_command_test invalid command", None),
    ("", None),
    (None, None),
])
def test_execute_command(qtbot, signals, caplog, cmd, val):
    """
    Test to ensure the widget's ability to execute a shell command.

    Expectations:
    1. If the command is not valid, there will be an error message in the log
    2. If the command is valid, there will be output in stdout (the result could be a success or failure, but at least
        the command will send out text to stdout)
    3. If the command is None or empty, there will be no output to stdout.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    caplog : fixture
        To capture the log messages
    cmd : str
        The shell command for the widget to execute
    val : int
        The expected exit code.
    """
    pydm_shell_command = PyDMShellCommand()
    qtbot.addWidget(pydm_shell_command)

    pydm_shell_command.command = cmd
    signals.send_value_signal[str].connect(pydm_shell_command.execute_command)
    signals.send_value_signal[str].emit(cmd)

    if cmd:
        if "invalid" not in cmd:
            ret = pydm_shell_command.process.wait()
            assert ret == val
        else:
            for record in caplog.records:
                assert record.levelno == ERROR
            assert "Error in command" in caplog.text
    else:
        assert pydm_shell_command.process is None


@pytest.mark.parametrize("allow_multiple", [
    True,
    False,
])
def test_execute_multiple_commands(qtbot, signals, caplog, allow_multiple):
    """
    Test the widget's ability to execute multiple shell commands when this setting is enabled.

    Expectations:
    1. If the multiple execution setting is enabled, the widget must execute another shell command while the previous
        one is still running.
    2. If the multiple execution setting is disabled, the widget will log the error "Command already active."

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    caplog : fixture
        To capture the log messages
    allow_multiple : bool
        True if multiple command executions are allowed for the widget; False otherwise
    """
    pydm_shell_command = PyDMShellCommand()
    qtbot.addWidget(pydm_shell_command)

    pydm_shell_command._allow_multiple = allow_multiple

    cmd = "choice /c yn /d y /t 1" if platform.system() == "Windows" else "sleep 0.1"
    pydm_shell_command.command = cmd
    signals.send_value_signal[str].connect(pydm_shell_command.execute_command)
    signals.send_value_signal[str].emit(cmd)
    signals.send_value_signal[str].emit(cmd)

    if not allow_multiple:
        for record in caplog.records:
            assert record.levelno == ERROR
        assert "Command already active." in caplog.text
    else:
        assert not caplog.text
