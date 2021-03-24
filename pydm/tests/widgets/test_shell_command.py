# Unit Tests for the Shell Command widget class

import os
import pytest

import platform
from logging import ERROR

from qtpy import QtCore
from qtpy.QtCore import QSize
from qtpy.QtWidgets import QMenu, QAction

from ...widgets.shell_command import PyDMShellCommand
from ...utilities import IconFont


# --------------------
# POSITIVE TEST CASES
# --------------------

@pytest.mark.parametrize("command, title", [
    ("foo", None),
    ("", None),
    (None, None),
    (["foo", "bar"], ["A", "B"]),
])
def test_construct(qtbot, command, title):
    """
    Test the construct of the widget.

    Expectations:
    The widget is initialized, and the commands and titles match the
    constructor arguments provided.  Also tests the icon and cursor pixmaps.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    command : str
        The shell command(s) to be executed when the widget is pressed
    title : str
        The titles for the shell commands.  Really only relevant if
        len(commands) > 1

    """
    pydm_shell_command = PyDMShellCommand(command=command, title=title)
    qtbot.addWidget(pydm_shell_command)
    if command and isinstance(command, str):
        assert pydm_shell_command._commands == [command]
    elif command:
        assert pydm_shell_command._commands == command
    else:
        assert pydm_shell_command._commands == []
    if title and isinstance(title, str):
        assert pydm_shell_command._titles == [title]
    elif title:
        assert pydm_shell_command._titles == title
    else:
        assert pydm_shell_command._titles == []
    
    DEFAULT_ICON_NAME = "cog"
    DEFAULT_ICON_SIZE = QSize(16, 16)

    default_icon = IconFont().icon(DEFAULT_ICON_NAME)

    default_icon_pixmap = default_icon.pixmap(DEFAULT_ICON_SIZE)
    shell_cmd_icon_pixmap = pydm_shell_command.icon().pixmap(DEFAULT_ICON_SIZE)

    assert shell_cmd_icon_pixmap.toImage() == default_icon_pixmap.toImage()
    assert pydm_shell_command.cursor().pixmap().toImage() == default_icon_pixmap.toImage()

def test_deprecated_command_property_with_no_commands(qtbot):
    pydm_shell_command = PyDMShellCommand()
    qtbot.addWidget(pydm_shell_command)
    pydm_shell_command.command = "test"
    assert pydm_shell_command.commands == ["test"]

def test_deprecated_command_property_with_commands(qtbot):
    pydm_shell_command = PyDMShellCommand()
    qtbot.addWidget(pydm_shell_command)
    existing_commands = ["existing", "commands"]
    pydm_shell_command.commands = existing_commands
    pydm_shell_command.command = "This shouldn't work"
    assert pydm_shell_command.commands == existing_commands

def test_no_crash_without_any_commands(qtbot):
     pydm_shell_command = PyDMShellCommand()
     qtbot.addWidget(pydm_shell_command)
     pydm_shell_command.commands = None
     qtbot.mouseClick(pydm_shell_command, QtCore.Qt.LeftButton)

def test_no_crash_with_none_command(qtbot):
     pydm_shell_command = PyDMShellCommand()
     qtbot.addWidget(pydm_shell_command)
     pydm_shell_command.command = None
     qtbot.mouseClick(pydm_shell_command, QtCore.Qt.LeftButton)

@pytest.mark.parametrize("cmd, retcode, stdout", [
    (["choice /c yn /d n /t 0"] if platform.system() == "Windows" else ["sleep 0"],
        [2] if platform.system() == "Windows" else [0], ["[Y,N]?N"] if platform.system() == "Windows" else [""]),
    (["pydm_shell_invalid_command_test invalid command"], [None], [""]),
    (["echo hello", "echo world"], [0, 0], ["hello", "world"])
])
def test_mouse_release_event(qtbot, caplog, cmd, retcode, stdout):
    """
    Test to ensure the widget's triggering of the Mouse Release event.
    
    Expectations if len(cmd) == 1:
    1. The mouse release will trigger the current shell command being assigned to the widget to execute
    2. If the command is not valid, there will be an error message in the log
    3. If the command is valid, there will be output in stdout (the result could be a success or failure, but at least
        the command will send out text to stdout)
    4. If the command is None or empty, there will be no output to stdout.
    
    Expectations if len(cmd) > 1:
    1. The mouse press will cause the widget to set its 'menu' attribute to an instance of QMenu.
    2. Triggering each menu item runs the right command.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    caplog : fixture
        To capture the log messages
    cmd : str
        The shell command for the widget to execute
    retcode : int
        The expected exit code.
    stdout : str
        The expected stdout for the command.
    """
    pydm_shell_command = PyDMShellCommand()
    qtbot.addWidget(pydm_shell_command)

    def check_command_output(command, expected_retcode, expected_stdout):
        if "invalid" not in command:
            stdout, stderr = pydm_shell_command.process.communicate()
            assert pydm_shell_command.process.returncode == expected_retcode
            assert expected_stdout in str(stdout)
        else:
            for record in caplog.records:
                assert record.levelno == ERROR
            assert "Error in shell command" in caplog.text

    pydm_shell_command.commands = cmd
    
    if len(cmd) > 1:
        for current_command, expected_retcode, expected_stdout in zip(cmd, retcode, stdout):
            # We can't actually do the click and show the menu - it halts the test and waits
            # for user input.  So instead, we'll force trigger _rebuild_menu().
            pydm_shell_command._rebuild_menu()
            assert isinstance(pydm_shell_command.menu(), QMenu)
            actions = pydm_shell_command.menu().findChildren(QAction)
            assert current_command in [a.text() for a in actions]
            action_for_current_command = [a for a in actions if a.text() == current_command][0]
            action_for_current_command.trigger()
            check_command_output(current_command, expected_retcode, expected_stdout)
    elif len(cmd) == 1:
        qtbot.mouseClick(pydm_shell_command, QtCore.Qt.LeftButton)
        check_command_output(cmd[0], retcode[0], stdout[0])
    else:
        qtbot.mouseClick(pydm_shell_command, QtCore.Qt.LeftButton)
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
    pydm_shell_command.execute_command(cmd)
    pydm_shell_command.execute_command(cmd)

    if not allow_multiple:
        for record in caplog.records:
            assert record.levelno == ERROR
        assert "already active" in caplog.text
    else:
        assert not caplog.text


def test_env_var(qtbot):
    """
    Test to ensure the widget can handle commands with environment variables
    in it.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_shell_command = PyDMShellCommand()
    qtbot.addWidget(pydm_shell_command)

    cmd = "echo Test: $PATH"
    if platform.system() == 'Windows':
        cmd = "echo Test: %PATH%"

    pydm_shell_command.commands = [cmd]
    qtbot.mouseClick(pydm_shell_command, QtCore.Qt.LeftButton)
    stdout, stderr = pydm_shell_command.process.communicate()
    assert pydm_shell_command.process.returncode == 0
    if platform.system() == 'Windows':
        # Windows changes C:\\ to C:\\\\
        assert os.getenv("PATH") in str(stdout).replace('\\\\', '\\')
    else:
        assert "Test: {}".format(os.getenv("PATH")) in str(stdout)
