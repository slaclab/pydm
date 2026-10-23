import os
import pytest
import sys
import warnings
from qtpy.QtCore import Qt, QSize
from qtpy.QtWidgets import QApplication
from pydm.utilities.stylesheet import global_style
from pydm.widgets.related_display_button import PyDMRelatedDisplayButton
from pydm.utilities import IconFont, checkObjectProperties
from pydm.data_plugins import plugin_for_address

test_ui_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../test_data", "test.ui")
test_ui_path_with_stylesheet = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "../test_data", "test_emb_style.ui"
)
test_ui_path_with_relative_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "../test_data", "test_relative_filename_parent.ui"
)


# additional props we expect to get added to PyDMRelatedDisplayButton class RULE_PROPERTIES
expected_related_display_button_properties = {"Text": ["setText", str], "Filenames": ["filenames", list]}


def test_old_display_filename_property(qtbot):
    # This test is mostly only checking that the related display button
    # doesn't totally explode when the old 'displayFilename' property is used.
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    assert checkObjectProperties(button, expected_related_display_button_properties) is True
    with warnings.catch_warnings(record=True) as record:
        button.displayFilename = test_ui_path
    assert len(record) >= 1
    assert button.filenames[0] == test_ui_path
    qtbot.addWidget(button)
    button._rebuild_menu()
    qtbot.mouseRelease(button, Qt.LeftButton)

    def check_title():
        assert "Form" in QApplication.instance().main_window.windowTitle()

    qtbot.waitUntil(check_title)


def test_press_with_filename(qtbot):
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    button.filenames = [test_ui_path]
    qtbot.addWidget(button)
    button._rebuild_menu()
    qtbot.mouseRelease(button, Qt.LeftButton)

    # verify default icon is set as expected
    DEFAULT_ICON_NAME = "file"
    DEFAULT_ICON_SIZE = QSize(16, 16)

    default_icon = IconFont().icon(DEFAULT_ICON_NAME)

    default_icon_pixmap = default_icon.pixmap(DEFAULT_ICON_SIZE)
    related_display_button_icon_pixmap = button.icon().pixmap(DEFAULT_ICON_SIZE)

    assert related_display_button_icon_pixmap.toImage() == default_icon_pixmap.toImage()
    assert button.cursor().pixmap().toImage() == default_icon_pixmap.toImage()

    # verify that qt standard icons can be set through our custom property
    style = button.style()
    test_icon = style.standardIcon(style.StandardPixmap.SP_DesktopIcon)
    test_icon_image = test_icon.pixmap(DEFAULT_ICON_SIZE).toImage()

    button.PyDMIcon = "SP_DesktopIcon"
    shell_cmd_icon = button.icon()
    shell_cmd_icon_image = shell_cmd_icon.pixmap(DEFAULT_ICON_SIZE).toImage()

    assert test_icon_image == shell_cmd_icon_image

    # verify that "Font Awesome" icons can be set through our custom property
    icon_f = IconFont()
    test_icon = icon_f.icon("eye-slash", color=None)
    test_icon_image = test_icon.pixmap(DEFAULT_ICON_SIZE).toImage()

    button.PyDMIcon = "eye-slash"
    button_icon = button.icon()
    push_btn_icon_image = button_icon.pixmap(DEFAULT_ICON_SIZE).toImage()

    assert test_icon_image == push_btn_icon_image

    def check_title():
        assert "Form" in QApplication.instance().main_window.windowTitle()

    qtbot.waitUntil(check_title)


def test_press_without_filename(qtbot):
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    qtbot.addWidget(button)
    button._rebuild_menu()
    qtbot.mouseRelease(button, Qt.LeftButton)
    qtbot.wait(250)
    assert "Form" not in QApplication.instance().main_window.windowTitle()


def test_no_menu_with_one_file(qtbot):
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    button.filenames = [test_ui_path]
    qtbot.addWidget(button)
    button._rebuild_menu()
    assert button.menu() is None


def test_menu_with_additional_files(qtbot):
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    main_window.set_display_widget(button)
    button.filenames = [test_ui_path, test_ui_path]
    button.titles = ["One", "Two"]
    qtbot.addWidget(button)
    button._rebuild_menu()
    assert button.menu() is not None
    qtbot.mouseRelease(button, Qt.LeftButton)
    qtbot.waitExposed(button.menu())
    qtbot.mouseClick(button.menu(), Qt.LeftButton)
    button.menu().actions()[0].trigger()

    def check_title():
        assert "Form" in QApplication.instance().main_window.windowTitle()

    qtbot.waitUntil(check_title)


def test_menu_goes_away_when_files_removed(qtbot):
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    main_window.set_display_widget(button)
    button.filenames = ["one.ui", "two.ui"]
    button.titles = ["One", "Two"]
    qtbot.addWidget(button)
    button._rebuild_menu()
    assert button.menu() is not None
    button.filenames = []
    button.titles = []
    button._rebuild_menu()
    assert button.menu() is None


def test_menu_goes_away_when_files_all_blank(qtbot):
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    button.filenames = ["", ""]
    button.titles = ["", ""]
    qtbot.addWidget(button)
    button._rebuild_menu()
    assert button.menu() is None


def test_press_with_relative_filename(qtbot):
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.open(test_ui_path_with_relative_path)
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = main_window.home_widget.relatedDisplayButton
    # Default behavior should be to not follow symlinks (for backwards compat.).
    # Same effect as: button.followSymlinks = False
    qtbot.mouseRelease(button, Qt.LeftButton)

    def check_title():
        assert "Child" in QApplication.instance().main_window.windowTitle()

    qtbot.waitUntil(check_title)


@pytest.mark.skipif(
    sys.platform == "win32" and sys.version_info < (3, 8),
    reason="os.path.realpath on Python 3.7 and prior does not resolve symlinks on Windows",
)
def test_press_with_relative_filename_and_symlink(qtbot, tmp_path):
    symlinked_ui_file = tmp_path / "test_ui_with_relative_path.ui"
    try:
        os.symlink(test_ui_path_with_relative_path, symlinked_ui_file)
    except Exception:
        pytest.skip("Unable to create a symlink for testing purposes.")

    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.open(symlinked_ui_file)
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = main_window.home_widget.relatedDisplayButton
    button.followSymlinks = True
    qtbot.mouseRelease(button, Qt.LeftButton)

    def check_title():
        assert "Child" in QApplication.instance().main_window.windowTitle()

    qtbot.waitUntil(check_title)


def test_no_pydm_app_stylesheet(monkeypatch, qtbot):
    local_is_pydm_app = True

    def is_pydm_app():
        return local_is_pydm_app

    monkeypatch.setattr(
        "pydm.widgets.related_display_button.is_pydm_app",
        is_pydm_app,
    )

    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    main_window.setWindowTitle("Related Display Button Test")
    qtbot.addWidget(main_window)
    button = PyDMRelatedDisplayButton(parent=main_window)
    qtbot.addWidget(button)

    # In a pydm application, the stylesheet is set on PyDMApplication
    local_is_pydm_app = True
    display1 = button.open_display(test_ui_path)
    assert not display1.styleSheet()

    # In non-pydm applications, we add a stylesheet to the display
    local_is_pydm_app = False
    display2 = button.open_display(test_ui_path)
    assert global_style() in display2.styleSheet()

    # If there was already a stylesheet we need to maintain the original text
    local_is_pydm_app = True
    display3 = button.open_display(test_ui_path_with_stylesheet)
    original_style = display3.styleSheet()
    local_is_pydm_app = False
    display4 = button.open_display(test_ui_path_with_stylesheet)
    assert original_style in display4.styleSheet()
    # And we need to add the global stylesheet too
    assert global_style() in display4.styleSheet()


def _icon_key(button, severity):
    return button._alarm_icons[severity].cacheKey()


def test_alarm_channels_create_entry_channels(qtbot, test_plugin):
    """Setting alarmChannels creates a channel per non-blank entry, listed in channels() after the button's own."""
    button = PyDMRelatedDisplayButton()
    qtbot.addWidget(button)
    button.channel = "tst://main"
    button.filenames = ["one.ui", "", "three.ui", "four.ui"]
    button.alarmChannels = ["tst://one", "tst://two", "", "tst://four"]
    assert button.alarmChannels == ["tst://one", "tst://two", "", "tst://four"]
    # Blank filename and blank alarm channel entries get no channel; the button's own channel stays first
    assert [c.address for c in button.channels()] == ["tst://main", "tst://one", "tst://four"]
    plugin = plugin_for_address("tst://one")
    assert all(c in plugin.channels for c in button._entry_channels.values())


def test_alarm_channels_ignored_for_single_filename(qtbot, test_plugin):
    """Entry channels exist only while there is more than one filename, since one filename opens with no menu."""
    button = PyDMRelatedDisplayButton()
    qtbot.addWidget(button)
    button.filenames = ["one.ui"]
    button.alarmChannels = ["tst://one"]
    assert button.channels() is None
    button.filenames = ["one.ui", "two.ui"]
    assert [c.address for c in button.channels()] == ["tst://one"]
    button.filenames = ["one.ui"]
    assert button.channels() is None


def test_entry_channels_resync_when_lists_change(qtbot, test_plugin):
    """Changing filenames or alarmChannels disconnects only the affected entries and replaces changed addresses."""
    button = PyDMRelatedDisplayButton()
    qtbot.addWidget(button)
    button.filenames = ["one.ui", "two.ui"]
    button.alarmChannels = ["tst://one", "tst://two"]
    plugin = plugin_for_address("tst://one")
    first, second = button._entry_channels[0], button._entry_channels[1]

    # Dropping a filename disconnects only that entry's channel
    button.filenames = ["one.ui", ""]
    assert list(button._entry_channels) == [0]
    assert button._entry_channels[0] is first
    assert second not in plugin.channels

    # Changing an address replaces the channel
    button.alarmChannels = ["tst://other", ""]
    assert button._entry_channels[0] is not first
    assert first not in plugin.channels
    assert button._entry_channels[0].address == "tst://other"

    button.alarmChannels = []
    assert button.channels() is None
    assert button._entry_connected == {} and button._entry_severity == {}


def test_menu_entry_icons_follow_alarm_state(qtbot, test_plugin):
    """Menu entry icons track the connection and severity slots, showing disconnected until both have reported."""
    button = PyDMRelatedDisplayButton()
    qtbot.addWidget(button)
    button.filenames = ["one.ui", "two.ui"]
    button.titles = ["One", "Two"]
    button.alarmChannels = ["tst://one", ""]
    button._rebuild_menu()
    one, two = button.menu().actions()

    assert two.icon().isNull()
    assert two.toolTip() == "Two"  # Qt falls back to the action text when no tooltip is set
    assert one.toolTip() == "tst://one"
    assert one.isIconVisibleInMenu()
    assert button.menu().toolTipsVisible()

    # Disconnected until both a connection and a severity have been reported
    assert one.icon().cacheKey() == _icon_key(button, button.ALARM_DISCONNECTED)
    button._entry_alarm_changed(0, button.ALARM_MAJOR)
    assert one.icon().cacheKey() == _icon_key(button, button.ALARM_DISCONNECTED)
    button._entry_connection_changed(0, True)
    assert one.icon().cacheKey() == _icon_key(button, button.ALARM_MAJOR)
    button._entry_alarm_changed(0, button.ALARM_NONE)
    assert one.icon().cacheKey() == _icon_key(button, button.ALARM_NONE)

    # A disconnect forgets the old severity; reconnecting waits for a fresh one
    button._entry_connection_changed(0, False)
    assert one.icon().cacheKey() == _icon_key(button, button.ALARM_DISCONNECTED)
    button._entry_connection_changed(0, True)
    assert one.icon().cacheKey() == _icon_key(button, button.ALARM_DISCONNECTED)
    button._entry_alarm_changed(0, button.ALARM_MINOR)
    assert one.icon().cacheKey() == _icon_key(button, button.ALARM_MINOR)

    # Unknown severities fall back to the invalid icon rather than raising inside the slot
    button._entry_alarm_changed(0, 99)
    assert one.icon().cacheKey() == _icon_key(button, button.ALARM_INVALID)


def test_menu_entry_icons_survive_rebuild_and_context_menu(qtbot, test_plugin):
    """Alarm state recorded before or between menu rebuilds is applied to the dropdown and the right-click submenu."""
    button = PyDMRelatedDisplayButton()
    qtbot.addWidget(button)
    button.filenames = ["one.ui", "two.ui"]
    button.titles = ["One", "Two"]
    button.alarmChannels = ["", "tst://two"]
    button._entry_connection_changed(1, True)
    button._entry_alarm_changed(1, button.ALARM_MINOR)

    # State recorded before the menu existed is applied when it gets built, and again after a rebuild
    button._rebuild_menu()
    assert button.menu().actions()[1].icon().cacheKey() == _icon_key(button, button.ALARM_MINOR)
    button._entry_alarm_changed(1, button.ALARM_MAJOR)
    button._menu_needs_rebuild = True
    button._rebuild_menu()
    assert button.menu().actions()[0].icon().isNull()
    assert button.menu().actions()[1].icon().cacheKey() == _icon_key(button, button.ALARM_MAJOR)

    # The right-click "Open in New Window" submenu shows the same state
    context_menu = button.context_menu()
    # Hold the action, not just its submenu: PySide6 invalidates the submenu wrapper otherwise
    open_new_window = [a for a in context_menu.actions() if a.text() == "Open in New Window"]
    assert len(open_new_window) == 1
    sub_menu = open_new_window[0].menu()
    assert sub_menu.actions()[1].icon().cacheKey() == _icon_key(button, button.ALARM_MAJOR)
    assert sub_menu.actions()[1].toolTip() == "tst://two"

    # Removing the alarm channel clears the icon on the live menu without a rebuild
    button.alarmChannels = ["", ""]
    assert button.menu().actions()[1].icon().isNull()
