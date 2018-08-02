# Unit Tests for the PyDMPushButton Widget


import pytest
import hashlib
import numpy as np

import logging

from qtpy.QtCore import QSize
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QInputDialog, QMessageBox
from ...widgets.base import PyDMWidget
from ...widgets.pushbutton import PyDMPushButton
from ...utilities.iconfont import IconFont


# --------------------
# POSITIVE TEST CASES
# --------------------

@pytest.mark.parametrize("label, press_value, relative, init_channel, icon_font_name, icon_color", [
    # Testing different types of press value
    ("Test Button", "Test Button PressValue", True, "CA://MTEST", "cogs", QColor(255, 255, 255)),
    ("Test Button", 42, True, "CA://MTEST", "cogs", QColor(255, 255, 255)),
    ("Test Button", 42.42, True, "CA://MTEST", "cogs", QColor(255, 255, 255)),

    # Testing combinations of parameters
    ("Test Button", "Test Button PressValue", True, "CA://MTEST", None, None),
    ("Test Button", "Test Button PressValue", True, "CA://MTEST", "", None),
    ("Test Button", "Test Button PressValue", True, "CA://MTEST", None, ""),
    ("Test Button", "Test Button PressValue", True, "CA://MTEST", "cog", QColor(255, 0, 0)),
    ("Test Button", "Test Button PressValue", True, "CA://MTEST", "cogs", QColor(255, 255, 255)),

    ("", "Test Button PressValue", True, "", "fast-forward", QColor(0, 0, 0)),
    ("Test Button", "", True, None, "fast-forward", QColor(0, 0, 255)),
    ("", "", True, "CA://MTEST", "fast-forward", QColor(0, 255, 0)),
    ("", None, True, "CA://MTEST", "fast-forward", QColor(255, 0, 0)),

    ("Test Button", "Test Button PressValue", False, "CA://MTEST", None, None),
    ("Test Button", "Test Button PressValue", False, "CA://MTEST", "check", QColor(10, 20, 30)),
    ("", "Test Button PressValue", False, "", "check", QColor(10, 20, 30)),
    ("Test Button", "", False, None, "check", QColor(10, 20, 30)),
    ("", "", False, "CA://MTEST", "check", QColor(10, 20, 30)),
    ("", None, False, "CA://MTEST", "check", QColor(10, 20, 30)),

    # Testing variations of empty parameters
    (None, "", True, "", None, None),
    (None, None, True, None, None, None),
    (None, "", False, "", None, None),
    (None, None, False, None, None, None),
])
def test_construct(qtbot, label, press_value, relative, init_channel, icon_font_name, icon_color):
    """
    Test the basic instantiation of the widget.

    Expectations:
    1. The widget can be created successfully with no arguments, some arguments, or all of them
    2. The settings will be retained with the created widget instance.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    label : str
        The name of the button widget
    press_value : int, float, str
        The value to be sent when the button is pressed
    relative : bool
        Send a relative value (added with the existing value) if True, or just the new value otherwise
    init_channel : str
        The Channel ID to send the value to
    icon_font_name : str
        The name of a character from a font set to use as an icon (currently using "fontawesome.ttf")
    icon_color : QColor
        The RGB color value for the icon
    """
    icon = None
    if icon_font_name:
        icon = IconFont().icon(icon_font_name, icon_color)

    pydm_pushbutton = PyDMPushButton(label=label, pressValue=press_value, relative=relative,
                                     init_channel=init_channel, icon=icon)
    qtbot.addWidget(pydm_pushbutton)

    assert pydm_pushbutton.text() == label if label else pydm_pushbutton.text() == ""
    assert pydm_pushbutton.relativeChange == relative

    if press_value:
        assert pydm_pushbutton.pressValue == str(press_value)
    else:
        assert pydm_pushbutton.pressValue == "None" if press_value is None else pydm_pushbutton.pressValue == ""

    if init_channel:
        assert pydm_pushbutton.channel == init_channel
    else:
        assert pydm_pushbutton.channel is None

    if icon:
        size = QSize(30, 30)
        icon_pixmap = icon.pixmap(size)
        button_icon_pixmap = pydm_pushbutton.icon().pixmap(size)
        assert icon_pixmap.toImage() == button_icon_pixmap.toImage()

    assert pydm_pushbutton.showConfirmDialog == False
    assert pydm_pushbutton.confirmMessage == PyDMPushButton.DEFAULT_CONFIRM_MESSAGE
    assert pydm_pushbutton.passwordProtected == False
    assert pydm_pushbutton.password == ""
    assert pydm_pushbutton.protectedPassword == ""


@pytest.mark.parametrize("password_is_protected", [
    (True),
    (False),
])
def test_password_protected(qtbot, password_is_protected):
    """
    Test that the password protected property is properly set. The password protected is flag that, if set to True,
    will prompt the user to enter a password before the button can be pushed to send the data

    Expectation:
    The protect password property flag retains the same Boolean value as provided.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing

    password_is_protected : bool
        The flag to set the password to protected (True), or not (otherwise)
    """
    pydm_pushbutton = PyDMPushButton()
    qtbot.addWidget(pydm_pushbutton)

    pydm_pushbutton.passwordProtected = password_is_protected
    assert pydm_pushbutton._password_protected == password_is_protected


@pytest.mark.parametrize("relative_choice", [
    (True),
    (False),
])
def test_relative_change(qtbot, relative_choice):
    """
    Test that the relative attribute of the button.

    Expectations:
    The button retains the relative attribute setting

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    relative_choice : bool
        Send a relative value (added with the existing value) if True, or just the new value otherwise
    """
    pydm_pushbutton = PyDMPushButton()
    qtbot.addWidget(pydm_pushbutton)

    pydm_pushbutton.relativeChange = relative_choice
    assert pydm_pushbutton.relativeChange == relative_choice


@pytest.mark.parametrize("password_protected, plain_text_password", [
    (True, "$L4C_p4$$wd"),
    (True, ""),
    (True, None),
    (False, "$L4C_p4$$wd"),
    (False, ""),
    (False, None)
])
def test_set_password(qtbot, password_protected, plain_text_password):
    """
    Test the widget's password encryption mechanism.

    Expectations:
    1. The widget will retain the attribute specifying whether the button requires a password
    2. The widget's encrypted password must be the same as the expected encrypted password, i.e. if the encryption
        method changes, this test will have to be changed, and the new encryption method will also be reviewed
    3. Currently, unless the provided (plain text) password is empty, it will always be encrypted, no matter whether
        the passwordProtected attribute is True or False

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    password_protected : bool
        True if the Push Button requires a user-provided password before sending the data to the channel; False
        otherwise
    plain_text_password : str
        The password to be required by the Push Button before sending the data to the channel
    """
    pydm_pushbutton = PyDMPushButton()
    qtbot.addWidget(pydm_pushbutton)

    pydm_pushbutton.passwordProtected = password_protected

    # Produce the expected encrypted password
    expected_encrypted_password = ""
    if plain_text_password:
        sha = hashlib.sha256()
        sha.update(plain_text_password.encode())
        expected_encrypted_password = sha.hexdigest()

    # Provide the plain text password to the Push Button, and expect to have the encrypted password via
    # the passwordProtected attribute
    # This takes a plain-text password, encrypts it, and stores it to the widget
    pydm_pushbutton.password = plain_text_password

    encrypted_password = pydm_pushbutton.protectedPassword

    assert pydm_pushbutton._password_protected == password_protected
    assert encrypted_password == expected_encrypted_password

@pytest.mark.parametrize("is_widget_protected_with_password, plain_text_password, input_dialog_status,"
                         "expected_validation_status", [
    (True, "$L4C_p4$$wd", True, True),
    (False, "$L4C_p4$$wd", True, True),

    (True, "", True, False),
    (False, "", True, True),

    (True, "$L4C_p4$$wd", False, False),
    (False, "$L4C_p4$$wd", False, True),

    (True, "Wrong_Password", True, False),
    (False, "Wrong_Password", True, False),

    (True, "Wrong_Password", False, False),
    (False, "Wrong_Password", False, False),
])
def test_validate_password(qtbot, monkeypatch, is_widget_protected_with_password, plain_text_password,
                           input_dialog_status, expected_validation_status):
    """
    Test password validation.

    Expectations:
    1. The user-provided password to the QInputDialog produces the same message disgest like that of the existing
        password's message digest.
    2. If the user-provided password to the QInputDialog is empty, or if the QInputDialog returns False, the validation
        must fail
    3. For the two expectations above to hold, the passwordProtected attribute must be True. If not, the validation
        will pass even if the user-provided password is incorrect.
    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To override dialog behaviors
    is_widget_protected_with_password : bool
        True if the widget requires a password, False otherwise
    plain_text_password : str
        The user-input password, in plain text, i.e. not encrypted
    input_dialog_status : bool
        The True/False status returned by the QInputDialog. True means the dialog has successfully received the
        user-input password, and the user has clicked on its OK button; False otherwise
    expected_validation_status : bool
        The expected validation result. True means the user-input is validated; False otherwise
    """
    pydm_pushbutton = PyDMPushButton()
    qtbot.addWidget(pydm_pushbutton)

    pydm_pushbutton.passwordProtected = is_widget_protected_with_password
    if is_widget_protected_with_password:
        # We set the protected password first, and mock the QInputDialog accepting the user-entered password.
        # Then, we mock different scenarios with the input dialog's returning False (the user clicking on Cancel),
        # or the user-entered password is not matching
        pydm_pushbutton.password = "$L4C_p4$$wd"
        monkeypatch.setattr(QInputDialog, 'getText', lambda *args: (plain_text_password, input_dialog_status))
        if not expected_validation_status:
            # Turn off the "Invalid password" dialog so that it won't interfere with the test
            monkeypatch.setattr(QMessageBox, 'exec_', lambda *args: (False,))

        validation_status = pydm_pushbutton.validate_password()
        assert validation_status == expected_validation_status


@pytest.mark.parametrize("initial_value, press_value, is_password_protected, show_confirm_dialog,"
                         "confirm_message, confirm_dialog_response, is_password_validated, is_value_relative,", [
    (0, 1, True, True, "Continue?", QMessageBox.Yes, True, False),
    (123, 345, True, True, "Continue?", QMessageBox.Yes, True, True),
    (123, "345", True, True, "", QMessageBox.Yes, True, True),
    (123.345, 345.678, True, True, "", QMessageBox.Yes, True, True),
    (123.345, "345.678", True, True, "", QMessageBox.Yes, True, True),

    ("123", 345, False, True, "", QMessageBox.Yes, True, True),
    ("123", 345.678, True, False, "", QMessageBox.Yes, True, True),
    ("123.345", 345.678, False, False, "", QMessageBox.Yes, True, True),
    ("123.345", "345.678", False, False, "", QMessageBox.Yes, True, True),

    ("123", 345, True, True, "", QMessageBox.No, True, True),
    ("123", 345, False, True, "", QMessageBox.No, True, True),

    ("123", 345, True, True, "Continue?", QMessageBox.Yes, True, False),
    ("123", 345, True, True, "", QMessageBox.Yes, True, False),
    ("123.345", 345.678, True, True, "", QMessageBox.Yes, True, False),
    ("123.345", "345.678", True, True, "", QMessageBox.Yes, True, False),

    ("123", 345, True, True, "Continue?", QMessageBox.Yes, False, True),
    ("123", 345, True, True, "", QMessageBox.Yes, False, False),
    ("abc", "def", True, True, "", QMessageBox.Yes, False, False),
    ("abc", None, True, True, "", QMessageBox.Yes, False, False),
    (None, "def", True, True, "", QMessageBox.Yes, False, False),
    (None, None, True, True, "", QMessageBox.Yes, False, False),
])
def test_send_value(qtbot, monkeypatch, signals, initial_value, press_value, is_password_protected, show_confirm_dialog,
                    confirm_message, confirm_dialog_response, is_password_validated, is_value_relative):
    """
    Test sending a new value to the channel.

    Expectations:
    1. The new value will be sent to the channel and converted to the current channel type
    2. If the relativeChange attribute is set to True, the channel's value is the total of the current value and the
        new value. If the same attribute is set to False, or the channel type is str, the channel's value is just the
        updated value
    3. Scenarios involved whether the confirm dialog's "Yes" or "No" button will be tested. For the the dialog's
        question, we'll also test an empty question or a user-supplied question being provided
    4. Scenarios involved whether password validation passes or fails will also be tested

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To override dialog behaviors
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    initial_value : int, float, str
        The first value given to the button
    press_value : int, float, str
        The new value to send to the channel
    is_password_protected : bool
        True if password validation is required; False otherwise
    show_confirm_dialog : bool
        True if the user will have to confirm the password by clicking on the "Yes" button of a dialog, or "No" to
        cancel; False if no such dialog will be needed
    confirm_message : str
        The customized question to be displayed in the confirmation dialog
    confirm_dialog_response : str
        The simulated response (Yes/No) for the confirmation dialog
    is_password_validated : bool
        The simulated response (True/False) of the dialog validation dialog. True means the user has provided the
        correct password. False otherwise
    is_value_relative : bool
        If True, the new value will be added to the existing pressValue; if False, the widget, when pressed, will send
        only the new value
    """
    pydm_pushbutton = PyDMPushButton()
    qtbot.addWidget(pydm_pushbutton)

    pydm_pushbutton.showConfirmDialog = show_confirm_dialog
    pydm_pushbutton.confirmMessage = confirm_message
    pydm_pushbutton.relativeChange = is_value_relative
    pydm_pushbutton.pressValue = press_value

    if initial_value:
        # If the user sets the initial value, emit the channel change signal. Otherwise, skip this signal emit part
        # and continue the test to see if the widget can handle a None initial value
        channel_type = type(initial_value)

        # Change the channel value, and make sure the signal is received
        signals.new_value_signal[channel_type].connect(pydm_pushbutton.channelValueChanged)
        signals.new_value_signal[channel_type].emit(initial_value)
        assert pydm_pushbutton.value == initial_value

        # Set up the conftest fixture to receive the value sent out to the channel
        pydm_pushbutton.send_value_signal[channel_type].connect(signals.receiveValue)

    if show_confirm_dialog:
        # Monkeypatch the confirm dialog call if popping up the dialog is enabled for testing
        monkeypatch.setattr(QMessageBox, 'exec_', lambda *args: confirm_dialog_response)

    pydm_pushbutton.passwordProtected = is_password_protected
    if is_password_protected:
        # Monkeypatch the password input dialog if this dialog is enabled for testing
        # We assume the QInputDialog returns success. Further testing scenarios are performed at test_validate_password
        plain_text_password = "$L4C_p4$$wd"
        pydm_pushbutton.password = plain_text_password
        monkeypatch.setattr(QInputDialog, 'getText', lambda *args: (plain_text_password, is_password_validated))

    send_value = pydm_pushbutton.sendValue()
    if not pydm_pushbutton.pressValue or not initial_value:
        # send_value() should return None if either the initial value or the pressValue is empty
        assert send_value is None
    else:
        if confirm_dialog_response == QMessageBox.No or not is_password_validated:
            assert not signals.value
        else:
            if pydm_pushbutton.showConfirmDialog:
                if confirm_message and len(confirm_message):
                    assert pydm_pushbutton.confirmMessage == confirm_message
                else:
                    assert pydm_pushbutton.confirmMessage == PyDMPushButton.DEFAULT_CONFIRM_MESSAGE

            if not is_value_relative or channel_type == str:
                assert signals.value == pydm_pushbutton.channeltype(pydm_pushbutton.pressValue)
            else:
                assert signals.value == pydm_pushbutton.value + pydm_pushbutton.channeltype(pydm_pushbutton.pressValue)


@pytest.mark.parametrize("current_channel_value, updated_value", [
    # Current channel value type is array, getting a new int value
    (np.array([123, 456]), 10),

    # Test if the current channel value type is int, and the widget is getting new int, float, or string value
    (10, 20),
    (10, 20.20),
    (10, "100"),

    # Test if the current channel value type is float, and the widget getting new int, float, or string value
    (10.10, 20.20),
    (10.10, 42),
    (10.10, "100.5"),

    # Test if the current channel value type is string, and the widget is getting new int, float, or string value
    ("Old str value", "New str value"),
    ("Old str value", 42),
    ("Old str value", 10.10),
])
def test_update_press_value(qtbot, signals, current_channel_value, updated_value):
    """
    Test the conversion of a new press value given the existing channel type.

    Expectations:
    For supported types (int, float, str), the conversions to the existing value type must be successful.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    current_channel_value : int, float, str, ndarray
        The existing channel value, which will remain consistent with the type of the updated value, i.e. it must be
        possible to convert the updated value to the type of the existing channel value
    updated_value : int, float, str
        The new channel to send to the channel by clicking on the widget
    """
    pydm_pushbutton = PyDMPushButton()
    qtbot.addWidget(pydm_pushbutton)

    # First, set the current channel type
    signals.new_value_signal[type(current_channel_value)].connect(pydm_pushbutton.channelValueChanged)
    signals.new_value_signal[type(current_channel_value)].emit(current_channel_value)

    # Verify the new value can be converted/cast as long as the casting can be done
    signals.new_value_signal[type(updated_value)].connect(pydm_pushbutton.updatePressValue)
    signals.new_value_signal[type(updated_value)].emit(updated_value)

    # Verify the new value is assigned to be the new pressValue as a str
    assert pydm_pushbutton.pressValue == str(type(current_channel_value)(updated_value))

# --------------------
# NEGATIVE TEST CASES
# --------------------

@pytest.mark.parametrize("current_channel_value, updated_value, expected_log_error", [
    (np.array([123.123, 456.456]), 10.10, "'10.1' is not a valid pressValue"),
    (np.array(["abc", "string in an array"]), "New str value", "'New str value' is not a valid pressValue"),

    (10, "New str value", "not a valid"),
    (10.10, "New str value", "not a valid"),
])
def test_update_press_value_incompatible_update_value(qtbot, signals, caplog, current_channel_value, updated_value,
                                                      expected_log_error):
    """
    Test if the widget will log the correct error message if the update value's type is incompatible with the current
    data type established by the current data associated with the widget.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    caplog : fixture
        The fixture to capture log outputs
    current_channel_value : int, float, str, ndarray
        The existing channel value
    updated_value : int, float, str
        The new channel to send to the channel by clicking on the widget
    expected_log_error : str
        The expected error message in the log
    """
    pydm_pushbutton = PyDMPushButton()
    qtbot.addWidget(pydm_pushbutton)

    # First, set the current channel type
    signals.new_value_signal[type(current_channel_value)].connect(pydm_pushbutton.channelValueChanged)
    signals.new_value_signal[type(current_channel_value)].emit(current_channel_value)

    # Verify the new value can be converted/cast as long as the casting can be done
    signals.new_value_signal[type(updated_value)].connect(pydm_pushbutton.updatePressValue)
    signals.new_value_signal[type(updated_value)].emit(updated_value)

    # Make sure logging capture the error, and have the correct error message
    for record in caplog.records:
        assert record.levelno == logging.ERROR
    assert expected_log_error in caplog.text
