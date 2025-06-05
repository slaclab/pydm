# Unit Tests for the Shell Command widget class

from __future__ import annotations

import os
import pytest
import time

import platform
from logging import ERROR

from qtpy import QtCore
from qtpy.QtCore import QSize
from qtpy.QtWidgets import QMenu, QAction, QWidget

from pydm.widgets.shell_command import PyDMShellCommand, TermOutputMode
from pydm.utilities import IconFont


# --------------------
# POSITIVE TEST CASES
# --------------------


@pytest.mark.parametrize(
    "command, title",
    [
        ("foo", None),
        ("", None),
        (None, None),
        (["foo", "bar"], ["A", "B"]),
    ],
)
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
    parent = QWidget()
    qtbot.addWidget(parent)

    pydm_shell_command = PyDMShellCommand(parent=parent, command=command, title=title)
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

    # verify that qt standard icons can be set through our custom property
    style = pydm_shell_command.style()
    test_icon = style.standardIcon(style.StandardPixmap.SP_DesktopIcon)
    test_icon_image = test_icon.pixmap(DEFAULT_ICON_SIZE).toImage()

    pydm_shell_command.PyDMIcon = "SP_DesktopIcon"
    shell_cmd_icon = pydm_shell_command.icon()
    shell_cmd_icon_image = shell_cmd_icon.pixmap(DEFAULT_ICON_SIZE).toImage()

    assert test_icon_image == shell_cmd_icon_image

    # verify that "Font Awesome" icons can be set through our custom property
    icon_f = IconFont()
    test_icon = icon_f.icon("eye-slash", color=None)
    test_icon_image = test_icon.pixmap(DEFAULT_ICON_SIZE).toImage()

    pydm_shell_command.PyDMIcon = "eye-slash"
    shell_cmd_icon = pydm_shell_command.icon()
    shell_cmd_icon_image = shell_cmd_icon.pixmap(DEFAULT_ICON_SIZE).toImage()

    assert test_icon_image == shell_cmd_icon_image
    assert pydm_shell_command.parent() == parent

    # This prevents pyside6 from deleting the internal c++ object
    # ("Internal C++ object (PyDMDateTimeLabel) already deleted")
    parent.deleteLater()
    pydm_shell_command.deleteLater()


@pytest.mark.filterwarnings("ignore:'PyDMShellCommand.command' is deprecated")
def test_deprecated_command_property_with_no_commands(qtbot):
    pydm_shell_command = PyDMShellCommand()
    qtbot.addWidget(pydm_shell_command)
    with pytest.warns(UserWarning):
        pydm_shell_command.command = "test"
    assert pydm_shell_command.commands == ["test"]


@pytest.mark.filterwarnings("ignore:'PyDMShellCommand.command' is deprecated")
def test_deprecated_command_property_with_commands(qtbot):
    pydm_shell_command = PyDMShellCommand()
    qtbot.addWidget(pydm_shell_command)
    existing_commands = ["existing", "commands"]
    pydm_shell_command.commands = existing_commands
    with pytest.warns(UserWarning):
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
    with pytest.warns(UserWarning):
        pydm_shell_command.command = None
    qtbot.mouseClick(pydm_shell_command, QtCore.Qt.LeftButton)


def test_no_error_without_env_variable(qtbot, caplog):
    """Verify that the shell command works when the environment variable property is saved as an empty string"""
    pydm_shell_command = PyDMShellCommand()
    qtbot.addWidget(pydm_shell_command)
    pydm_shell_command.commands = ["echo hello"]
    pydm_shell_command.environmentVariables = ""
    qtbot.mouseClick(pydm_shell_command, QtCore.Qt.LeftButton)
    assert "error" not in caplog.text.lower()


@pytest.mark.parametrize(
    "cmd, retcode, stdout",
    [
        (
            ["choice /c yn /d n /t 0"] if platform.system() == "Windows" else ["sleep 0"],
            [2] if platform.system() == "Windows" else [0],
            ["[Y,N]?N"] if platform.system() == "Windows" else [""],
        ),
        (["pydm_shell_invalid_command_test invalid command"], [None], [""]),
        (["echo hello", "echo world"], [0, 0], ["hello", "world"]),
    ],
)
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
    pydm_shell_command.stdout = TermOutputMode.STORE
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


def test_long_running_command_shows_currently_running_text(qtbot):
    """
    Test that the button is updated to indicate when a command is currently running.
    These indications are:
        - Prepend "(Running...) " to the button's text
        - Make button text italic
        - Disable button while cmd is running (unless allowMultipleExecutions is set True)
        - Set button icon to hourglass symbol
    And the button should be reset back to it's original state after the command is done.
    """
    pydm_shell_command = PyDMShellCommand()
    pydm_shell_command.stdout = TermOutputMode.HIDE
    pydm_shell_command.showCurrentlyRunningIndication = True
    qtbot.addWidget(pydm_shell_command)

    # Long running cmd, which we will kill after checking button state while its running
    pydm_shell_command.commands = ["for i in {1..4}; do echo $i; sleep 0.25; done"]

    original_text = "Run Long Cmd"
    pydm_shell_command.setText(original_text)
    pydm_shell_command.runCommandsInFullShell = True

    # Execute the cmd
    qtbot.mouseClick(pydm_shell_command, QtCore.Qt.LeftButton)

    # Check icon is updated while cmd is running
    qtbot.wait_until(lambda: pydm_shell_command.text().startswith("(Running...)"))
    assert pydm_shell_command.text() == f"(Running...) {original_text}"
    icon_size = QSize(16, 16)
    default_icon = IconFont().icon("hourglass-start")
    default_icon_pixmap = default_icon.pixmap(icon_size)
    curr_icon_pixmap = pydm_shell_command.icon().pixmap(icon_size)
    assert curr_icon_pixmap.toImage() == default_icon_pixmap.toImage()

    assert pydm_shell_command.font().italic()

    assert not pydm_shell_command.isEnabled()

    # Temp disable this part of test
    """
    # This 2nd 'wait_until' in the 'long_running_command' testcases causes error only when running all tests together:
    # 'RuntimeError: wrapped C/C++ object of type PyDMShellCommand has been deleted'.
    # To prevent this, have tried giving shell_command a parent widget, using 'qtbot.wait(n)' instead,
    # calling shell_command.show(), etc, but nothing seems to prevent the C++ object deletion.

    # Check icon is reverted back after cmd stops running
    qtbot.wait_until(lambda: pydm_shell_command.text() == original_text)
    default_icon = IconFont().icon("cog")
    default_icon_pixmap = default_icon.pixmap(icon_size)
    curr_icon_pixmap = pydm_shell_command.icon().pixmap(icon_size)
    assert curr_icon_pixmap.toImage() == default_icon_pixmap.toImage()

    assert not pydm_shell_command.font().italic()

    assert pydm_shell_command.isEnabled()
    """


def test_long_running_command_shows_currently_running_text_dropdown(qtbot):
    """
    Test that A button with multiple-cmds (so it has a drop-down menu) is updated to indicate
    a drop-down menu command is currently running.
    These indications are:
        - Prepend "(Submenu cmd running...) " to the button's text
        - Prepend "(Running...) " to the curr running drop-down item
        - Make button and curr running drop-down text italic
        - Disable button and all drop-down menu items while cmd is running (unless allowMultipleExecutions is set True)
        - Set both button and curr running drop-down icons to hourglass symbol
    And the button should be reset back to it's original state after the command is done.
    """
    pydm_shell_command = PyDMShellCommand()
    pydm_shell_command.stdout = TermOutputMode.SHOW
    pydm_shell_command.showCurrentlyRunningIndication = True
    qtbot.addWidget(pydm_shell_command)

    original_button_text = "Run Long Cmd"
    # Text of the specific item in drop-down we want to check the state of
    original_action_text = "for i in {1..4}; do echo $i; sleep 0.25; done"
    pydm_shell_command.setText(original_button_text)
    pydm_shell_command.runCommandsInFullShell = True

    pydm_shell_command.commands = ["echo 'command 1'", "echo 'command 2'", original_action_text]

    # We need to execute the shell-cmd's mousePressEvent() so it can build the drop-down menu,
    # and right-click since left-click seems to cause this test to then display the drop-down menu
    # and just pauses waiting for user interaction.
    qtbot.mouseClick(pydm_shell_command, QtCore.Qt.RightButton)

    actions = pydm_shell_command.menu().actions()
    assert len(actions) >= 3

    # Activate drop-down menu button cmd
    actions[2].trigger()

    # Check button icon is changed while cmd is running
    qtbot.wait_until(lambda: pydm_shell_command.text().startswith("(Submenu cmd running...)"))
    assert pydm_shell_command.text() == f"(Submenu cmd running...) {original_button_text}"

    icon_size = QSize(16, 16)
    default_icon = IconFont().icon("hourglass-start")
    default_icon_pixmap = default_icon.pixmap(icon_size)
    curr_icon_pixmap = pydm_shell_command.icon().pixmap(icon_size)
    assert curr_icon_pixmap.toImage() == default_icon_pixmap.toImage()
    assert pydm_shell_command.font().italic()

    # Check state of action buttons in drop-down menu
    # Check icon is changed on curr running action button while cmd is running
    default_icon = IconFont().icon("hourglass-start")
    default_icon_pixmap = default_icon.pixmap(icon_size)
    curr_icon_pixmap = actions[2].icon().pixmap(icon_size)
    assert curr_icon_pixmap.toImage() == default_icon_pixmap.toImage()

    assert actions[2].text() == f"(Running...) {original_action_text}"
    assert actions[2].font().italic()

    assert all(not action.isEnabled() for action in actions)

    # Temp disable this part of test (see comment in other 'long_running_command' testcase)
    """
    # Check button icon is reverted back after cmd stops running
    qtbot.wait_until(lambda: pydm_shell_command.text() == original_button_text)
    default_icon = IconFont().icon("cog")
    default_icon_pixmap = default_icon.pixmap(icon_size)
    curr_icon_pixmap = pydm_shell_command.icon().pixmap(icon_size)
    assert curr_icon_pixmap.toImage() == default_icon_pixmap.toImage()
    assert not pydm_shell_command.font().italic()

    # Check drop-down menu icon is reverted
    actions[2].icon().isNull()  # Drop-down menu cmds have no icon by default
    assert all(action.isEnabled() for action in actions)
    """


@pytest.mark.parametrize(
    "allow_multiple",
    [
        True,
        False,
    ],
)
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
    pydm_shell_command.stdout = TermOutputMode.STORE

    qtbot.addWidget(pydm_shell_command)

    os.environ["PYDM_TEST_ENV_VAR"] = "this is a pydm test"
    cmd = "echo Test: $PYDM_TEST_ENV_VAR"
    if platform.system() == "Windows":
        cmd = "echo Test: %PYDM_TEST_ENV_VAR%"

    pydm_shell_command.commands = [cmd]
    qtbot.mouseClick(pydm_shell_command, QtCore.Qt.LeftButton)
    stdout, stderr = pydm_shell_command.process.communicate()
    assert pydm_shell_command.process.returncode == 0
    assert stdout.decode("utf-8") == "Test: this is a pydm test\n"


options = (
    TermOutputMode.HIDE,
    TermOutputMode.SHOW,
    TermOutputMode.STORE,
)


@pytest.mark.parametrize("stdout_setting, stderr_setting", [(first, second) for first in options for second in options])
def test_output_options(qtbot, capfd, stdout_setting, stderr_setting):
    """
    Test that the stdout and stderr options work properly.

    Parameters
    ----------
    qtbot : fixture
        Ensures clean up of the shell command button
    capfd : fixture
        Captures output to the stdout and stderr file descriptors.
        We need to use capfd instead of capsys because capsys
        doesn't catch the stdout from the subprocess called.
    stdout_setting : TermOutputMode
        The stdout setting to test
    stderr_setting : TermOutputMode
        The stderr setting to test
    """
    pydm_shell_command = PyDMShellCommand()
    pydm_shell_command.stdout = stdout_setting
    pydm_shell_command.stderr = stderr_setting
    pydm_shell_command.runCommandsInFullShell = True

    qtbot.addWidget(pydm_shell_command)

    if platform.system() == "Windows":
        cmdsep = " & "
        outterm = " \r\n"
    else:
        cmdsep = "; "
        outterm = "\n"

    capfd.readouterr()
    pydm_shell_command.execute_command(f"echo stdout{cmdsep}echo stderr 1>&2")
    pydm_shell_command.process.wait()
    out_show, err_show = capfd.readouterr()
    out_store, err_store = pydm_shell_command.process.communicate()

    if stdout_setting == TermOutputMode.HIDE:
        assert out_show == ""
        assert out_store is None
    elif stdout_setting == TermOutputMode.SHOW:
        assert out_show == f"stdout{outterm}"
        assert out_store is None
    elif stdout_setting == TermOutputMode.STORE:
        assert out_show == ""
        assert out_store.decode("utf-8") == f"stdout{outterm}"
    else:
        raise RuntimeError("Test written wrong, invalid stdout_setting")

    if stderr_setting == TermOutputMode.HIDE:
        assert err_show == ""
        assert err_store is None
    elif stderr_setting == TermOutputMode.SHOW:
        assert err_show == f"stderr{outterm}"
        assert err_store is None
    elif stderr_setting == TermOutputMode.STORE:
        assert err_show == ""
        assert err_store.decode("utf-8") == f"stderr{outterm}"
    else:
        raise RuntimeError("Test written wrong, invalid stderr_setting")


def test_output_options_backcompat(qtbot, caplog):
    """
    Test that existing screens that use redirectCommandOutput will still work.

    redirectCommandOutput is soft deprecated but should still be functional.

    Parameters
    ----------
    qtbot : fixture
        Ensures clean up of the shell command button
    caplog : fixture
        Used to capture and verify log warnings
    """
    pydm_shell_command = PyDMShellCommand()
    pydm_shell_command.setObjectName("testShellCommand")
    qtbot.addWidget(pydm_shell_command)

    # Defaults
    assert not pydm_shell_command.redirectCommandOutput
    assert pydm_shell_command.stdout == TermOutputMode.HIDE

    def assert_backcompat(value: bool | TermOutputMode, expect_warning: bool):
        """Helper for repeated assert checks in this unit test."""
        # Cache old value in case this isn't supposed to change the value
        orig_stdout = pydm_shell_command.stdout
        # Clear any stored logs from previous calls
        caplog.clear()
        # Set the new state
        if isinstance(value, bool):
            pydm_shell_command.redirectCommandOutput = value
        else:
            pydm_shell_command.stdout = value
        # Ensure we did or did not have a warning message
        if expect_warning:
            assert "WARNING" in caplog.text
        else:
            assert "WARNING" not in caplog.text
        # Depending on the input, verify the widget state is as expected
        # show == redirect command output (to the terminal)
        # other states do not redirect command output (to the terminal)
        # Setting redirect itself (bool) should flip between show and hide
        if isinstance(value, bool):
            if value:
                if expect_warning:
                    # Don't override the new property with the old one
                    assert pydm_shell_command.stdout == orig_stdout
                else:
                    assert pydm_shell_command.redirectCommandOutput
                    assert pydm_shell_command.stdout == TermOutputMode.SHOW
            else:
                if expect_warning:
                    # Don't override the new property with the old one
                    assert pydm_shell_command.stdout == orig_stdout
                else:
                    assert not pydm_shell_command.redirectCommandOutput
                    assert pydm_shell_command.stdout == TermOutputMode.HIDE
        else:
            if value == TermOutputMode.SHOW:
                assert pydm_shell_command.redirectCommandOutput
                assert pydm_shell_command.stdout == value
            elif value in (TermOutputMode.HIDE, TermOutputMode.STORE):
                assert not pydm_shell_command.redirectCommandOutput
                assert pydm_shell_command.stdout == value
            else:
                raise ValueError("Invalid value used in test suite")

    # Changing redirectCommandOutput should also change stdout. No warnings here.
    assert_backcompat(value=True, expect_warning=False)
    assert_backcompat(value=False, expect_warning=False)

    # Changing stdout should update the values without any warnings.
    assert_backcompat(value=TermOutputMode.SHOW, expect_warning=False)
    assert_backcompat(value=TermOutputMode.HIDE, expect_warning=False)
    assert_backcompat(value=TermOutputMode.STORE, expect_warning=False)

    # Now that we've changed stdout, changing redirectCommandOutput is a warning and a no-op.
    assert_backcompat(value=True, expect_warning=True)
    assert_backcompat(value=False, expect_warning=True)

    # A fresh widget should also not have warnings from changing stdout
    pydm_shell_command = PyDMShellCommand()
    qtbot.addWidget(pydm_shell_command)

    assert_backcompat(value=TermOutputMode.SHOW, expect_warning=False)
    assert_backcompat(value=TermOutputMode.HIDE, expect_warning=False)
    assert_backcompat(value=TermOutputMode.STORE, expect_warning=False)
