import copy
import os
import logging
import warnings
from functools import partial
import hashlib
from qtpy.QtWidgets import QPushButton, QMenu, QAction, QMessageBox, QInputDialog, QLineEdit, QWidget, QStyle
from qtpy.QtGui import QCursor, QIcon, QMouseEvent, QColor
from qtpy.QtCore import Slot, Qt, QSize, QPoint
from qtpy import QtDesigner
from .base import PyDMWidget, only_if_channel_set, PostParentClassInitSetup
from .channel import PyDMChannel
from pydm.utilities import IconFont, find_file, is_pydm_app
from pydm.utilities.macro import parse_macro_string
from pydm.utilities.stylesheet import merge_widget_stylesheet
from pydm.display import load_file, ScreenTarget
from typing import Optional, List, Dict
from pydm.utilities import ACTIVE_QT_WRAPPER, QtWrapperTypes

if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYSIDE6:
    from PySide6.QtCore import Property
else:
    from qtpy.QtCore import Property

logger = logging.getLogger(__name__)

_relatedDisplayRuleProperties = {"Text": ["setText", str], "Filenames": ["filenames", list]}


class PyDMRelatedDisplayButton(QPushButton, PyDMWidget):
    """
    A QPushButton capable of opening a new Display in the same or a new window.

    Parameters
    ----------
    parent : QWidget, optional
        The parent widget for the related display button
    filename : str, optional
        The file to be opened
    init_channel : str, optional
        The channel to be used by the widget
    """

    new_properties = _relatedDisplayRuleProperties
    # Constants for determining where to open the display.
    EXISTING_WINDOW = 0
    NEW_WINDOW = 1

    def __init__(
        self, parent: Optional[QWidget] = None, filename: str = None, init_channel: Optional[str] = None
    ) -> None:
        QPushButton.__init__(self, parent)
        PyDMWidget.__init__(self, init_channel=init_channel)

        self.mouseReleaseEvent = self.push_button_release_event
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.iconFont = IconFont()
        self._icon = self.iconFont.icon("file")
        self.setIconSize(QSize(16, 16))
        self.setIcon(self._icon)

        self._filenames = [filename] if filename is not None else []
        self._titles = []
        self._macros = []
        self._alarm_channels = []
        # Per-entry alarm indicators for the dropdown menu, keyed by index into filenames
        self._entry_channels: Dict[int, PyDMChannel] = {}
        self._entry_connected: Dict[int, bool] = {}
        self._entry_severity: Dict[int, int] = {}
        self._entry_actions: Dict[int, QAction] = {}
        self._alarm_icons = self._generate_alarm_icons()
        self.num_additional_items = 0
        self._shift_key_was_down = False
        self.setCursor(QCursor(self._icon.pixmap(16, 16)))
        self._display_menu_items = None
        self._display_filename = ""
        self._recursive_display_search = False
        self._macro_string = None
        self._open_in_new_window = False
        self.open_in_new_window_action = QAction("Open in New Window", self)
        self.open_in_new_window_action.triggered.connect(self.handle_open_new_window_action)
        self._show_icon = True
        self._menu_needs_rebuild = True

        self._password_protected = False
        self._password = ""
        self._protected_password = ""

        self._follow_symlinks = False

        # Standard icons (which come with the qt install, and work cross-platform),
        # and icons from the "Font Awesome" icon set (https://fontawesome.com/)
        # can not be set with a widget's "icon" property in designer, only in python.
        # so we provide our own property to specify standard icons and set them with python in the prop's setter.
        self._pydm_icon_name = ""
        # The color of "Font Awesome" icons can be set,
        # but standard icons are already colored and can not be set.
        self._pydm_icon_color = QColor(90, 90, 90)

        # Retain references to subdisplays to avoid garbage collection
        self._subdisplays = []

        # Execute setup calls that must be done here in the widget class's __init__,
        # and after it's parent __init__ calls have completed.
        # (so we can avoid pyside6 throwing an error, see func def for more info)
        PostParentClassInitSetup(self)

    # On pyside6, we need to expilcity call pydm's base class's eventFilter() call or events
    # will not propagate to the parent classes properly.
    def eventFilter(self, obj, event):
        return PyDMWidget.eventFilter(self, obj, event)

    @only_if_channel_set
    def check_enable_state(self) -> None:
        """
        override parent method, so this widget does not get disabled when the pv disconnects.
        This method adds a Tool Tip with the reason why it is disabled.
        """
        status = self._connected
        tooltip = self.restore_original_tooltip()
        if not status:
            if tooltip != "":
                tooltip += "\n"
            tooltip += "Alarm PV is disconnected."
            tooltip += "\n"
            tooltip += self.get_address()

        self.setToolTip(tooltip)

    def readPyDMIcon(self) -> str:
        """
        Name of icon to be set from Qt provided standard icons or from the fontawesome icon-set.
        See "enum QStyle::StandardPixmap" in Qt's QStyle documentation for full list of usable standard icons.
        See https://fontawesome.com/icons?d=gallery for list of usable fontawesome icons.

        Returns
        -------
        str
        """
        return self._pydm_icon_name

    def setPyDMIcon(self, value: str) -> None:
        """
        Name of icon to be set from Qt provided standard icons or from the "Font Awesome" icon-set.
        See "enum QStyle::StandardPixmap" in Qt's QStyle documentation for full list of usable standard icons.
        See https://fontawesome.com/icons?d=gallery for list of usable "Font Awesome" icons.

        Parameters
        ----------
        value : str
        """
        if self._pydm_icon_name == value:
            return

        # We don't know if user is trying to use a standard icon or an icon from "Font Awesome",
        # so 1st try to create a Font Awesome one, which hits exception if icon name is not valid.
        try:
            icon_f = IconFont()
            i = icon_f.icon(value, color=self._pydm_icon_color)
            self.setIcon(i)
        except Exception:
            icon = getattr(QStyle, value, None)
            if icon:
                self.setIcon(self.style().standardIcon(icon))

        self._pydm_icon_name = value

    PyDMIcon = Property(str, readPyDMIcon, setPyDMIcon)

    def readPyDMIconColor(self) -> QColor:
        """
        The color of the icon (color is only applied if using icon from the "Font Awesome" set)
        Returns
        -------
        QColor
        """
        return self._pydm_icon_color

    def setPyDMIconColor(self, state_color: QColor) -> None:
        """
        The color of the icon (color is only applied if using icon from the "Font Awesome" set)
        Parameters
        ----------
        new_color : QColor
        """
        if state_color != self._pydm_icon_color:
            self._pydm_icon_color = state_color
            # apply the new color
            try:
                icon_f = IconFont()
                i = icon_f.icon(self._pydm_icon_name, color=self._pydm_icon_color)
                self.setIcon(i)
            except Exception:
                return

    PyDMIconColor = Property(QColor, readPyDMIconColor, setPyDMIconColor)

    def readFilenames(self) -> List[str]:
        return self._filenames

    def setFilenames(self, val: List[str]) -> None:
        self._filenames = val
        self._menu_needs_rebuild = True
        self._sync_entry_channels()

    filenames = Property("QStringList", readFilenames, setFilenames)

    def readTitles(self) -> List[str]:
        return self._titles

    def setTitles(self, val: List[str]) -> None:
        self._titles = val
        self._menu_needs_rebuild = True

    titles = Property("QStringList", readTitles, setTitles)

    def readAlarmChannels(self) -> List[str]:
        """
        Alarm channels for the entries of the dropdown menu, one per entry in
        ``filenames``.  Each menu entry shows an icon reflecting the alarm
        severity of its channel.  Leave an entry blank for no indicator.
        Only used when the button has more than since a single filename opens without a menu.

        Returns
        -------
        list of str
        """
        return self._alarm_channels

    def setAlarmChannels(self, val: List[str]) -> None:
        """
        Alarm channels for the entries of the dropdown menu, one per entry in
        ``filenames``.

        Parameters
        ----------
        val : list of str
        """
        self._alarm_channels = list(val) if val else []
        self._menu_needs_rebuild = True
        self._sync_entry_channels()

    alarmChannels = Property("QStringList", readAlarmChannels, setAlarmChannels)

    def _generate_alarm_icons(self) -> Dict[int, QIcon]:
        icon_font = IconFont()
        return {
            self.ALARM_NONE: icon_font.icon("circle", color=QColor(0, 220, 0)),
            self.ALARM_MINOR: icon_font.icon("circle", color=QColor(220, 220, 0)),
            self.ALARM_MAJOR: icon_font.icon("exclamation-circle", color=QColor(255, 0, 0)),
            self.ALARM_INVALID: icon_font.icon("question-circle", color=QColor(220, 0, 220)),
            self.ALARM_DISCONNECTED: icon_font.icon("times-circle", color=QColor(150, 150, 150)),
        }

    def _entry_alarm_addresses(self) -> Dict[int, str]:
        """Index to alarm channel address for every entry that gets a menu item and has a channel."""
        if len(self._filenames) <= 1:
            return {}
        addresses = {}
        for i, filename in enumerate(self._filenames):
            if not filename or i >= len(self._alarm_channels):
                continue
            if self._alarm_channels[i]:
                addresses[i] = str(self._alarm_channels[i])
        return addresses

    def _sync_entry_channels(self) -> None:
        """Make the per-entry alarm channels match the current filenames/alarmChannels lists."""
        wanted = self._entry_alarm_addresses()
        for index, chan in list(self._entry_channels.items()):
            if wanted.get(index) == chan.address:
                continue
            chan.disconnect()
            del self._entry_channels[index]
            self._entry_connected.pop(index, None)
            self._entry_severity.pop(index, None)
            self._apply_entry_icon(index)
        for index, address in wanted.items():
            if index in self._entry_channels:
                continue
            chan = PyDMChannel(
                address=address,
                connection_slot=partial(self._entry_connection_changed, index),
                severity_slot=partial(self._entry_alarm_changed, index),
            )
            self._entry_channels[index] = chan
            chan.connect()

    def _entry_connection_changed(self, index: int, connected: bool) -> None:
        self._entry_connected[index] = connected
        if not connected:
            # Forget the stale severity so a reconnect shows disconnected until a fresh one arrives
            self._entry_severity.pop(index, None)
        self._apply_entry_icon(index)

    def _entry_alarm_changed(self, index: int, severity: int) -> None:
        self._entry_severity[index] = severity
        self._apply_entry_icon(index)

    def _entry_icon(self, index: int) -> QIcon:
        if index not in self._entry_channels:
            return QIcon()
        if self._entry_connected.get(index) and index in self._entry_severity:
            return self._alarm_icons.get(self._entry_severity[index], self._alarm_icons[self.ALARM_INVALID])
        return self._alarm_icons[self.ALARM_DISCONNECTED]

    def _apply_entry_icon(self, index: int) -> None:
        action = self._entry_actions.get(index)
        if action is None:
            return
        try:
            action.setIcon(self._entry_icon(index))
        except RuntimeError:
            # Menu already torn down (display closing) while a channel update was still queued
            self._entry_actions.pop(index, None)

    def _get_items(self):
        """
        Aggregate file entry information.

        Yields
        ------
        item : dict
            Containing index, filename, title, macros/empty macros and alarm channel/empty
            Only containing valid entries or nothing

        """
        for i, filename in enumerate(self.filenames):
            if not filename:
                continue
            item = {"index": i, "filename": filename}
            if i >= len(self.titles):
                item["title"] = filename
            else:
                item["title"] = self.titles[i]
            if i < len(self.macros):
                item["macros"] = self.macros[i]
            else:
                item["macros"] = ""
            item["alarm_channel"] = self._entry_channels[i].address if i in self._entry_channels else ""
            yield item

    def _rebuild_menu(self) -> None:
        self._entry_actions = {}
        if not any(self._filenames):
            self._filenames = []
        if not any(self._titles):
            self._titles = []
        if len(self._filenames) == 0:
            self.setEnabled(False)
        if len(self._filenames) <= 1:
            self.setMenu(None)
            self._menu_needs_rebuild = False
            return
        menu = QMenu(self)
        self._assemble_menu(menu, target=None, track_actions=True)
        self.setMenu(menu)
        self._menu_needs_rebuild = False

    def readShowIcon(self) -> bool:
        """
        Whether or not we should show the selected Icon.

        Returns
        -------
        bool
        """
        return self._show_icon

    def setShowIcon(self, value: bool) -> None:
        """
        Whether or not we should show the selected Icon.

        Parameters
        ----------
        value : bool
        """
        if self._show_icon != value:
            self._show_icon = value

            if self._show_icon:
                self.setIcon(self._icon)
            else:
                self._icon = self.icon()
                self.setIcon(QIcon())

    showIcon = Property(bool, readShowIcon, setShowIcon)

    def readDisplayFilename(self) -> str:
        """
        DEPRECATED: use the 'filenames' property.
        This property simply returns the first filename from the 'filenames'
        property.
        The filename to open

        Returns
        -------
        str
        """
        if len(self.filenames) == 0:
            return ""
        return self.filenames[0]

    def setDisplayFilename(self, value: str) -> None:
        """
        DEPRECATED: use the 'filenames' property.
        Any value set to this property is appended to the 'filenames'
        property, then 'displayFilename' is cleared.

        Parameters
        ----------
        value : str
        """
        warnings.warn(
            "'PyDMRelatedDisplayButton.displayFilename' is deprecated, "
            "use 'PyDMRelatedDisplayButton.filenames' instead."
        )
        if value:
            if value in self.filenames:
                return
            file_list = [value]
            self.filenames = self.filenames + file_list
        self._display_filename = ""

    displayFilename = Property(
        str,
        readDisplayFilename,
        setDisplayFilename,
        designable=False,
    )

    def readRecursiveDisplaySearch(self) -> bool:
        """
        Whether or not to search for a provided display file recursively
        in subfolders relative to the location of this display.

        Returns
        -------
        bool
            If recursive search is enabled.
        """
        return self._recursive_display_search

    def setRecursiveDisplaySearch(self, new_value) -> None:
        """
        Set whether or not to search for a provided display file recursively
        in subfolders relative to the location of this display.

        Parameters
        ----------
        new_value
            If recursive search should be enabled.
        """
        self._recursive_display_search = new_value

    recursiveDisplaySearch = Property(bool, readRecursiveDisplaySearch, setRecursiveDisplaySearch)

    def readMacros(self) -> List[str]:
        """
        The macro substitutions to use when launching the display, in JSON object format.

        Returns
        -------
        list of str
        """
        return self._macros

    def setMacros(self, new_macros: List[str]) -> None:
        """
        The macro substitutions to use when launching the display, in JSON object format.

        Parameters
        ----------
        new_macros : list of str
        """
        # Handle the deprecated form of macros where it was a single string.
        if isinstance(new_macros, str):
            new_macros = [new_macros]
        self._macros = new_macros

    macros = Property("QStringList", readMacros, setMacros)

    def readOpenInNewWindow(self) -> bool:
        """
        If true, the button will open the display in a new window, rather than in the existing window.

        Returns
        -------
        bool
        """
        return self._open_in_new_window

    def setOpenInNewWindow(self, open_in_new: bool) -> None:
        """
        If true, the button will open the display in a new window, rather than in the existing window.

        Parameters
        ----------
        open_in_new : bool
        """
        self._open_in_new_window = open_in_new

    openInNewWindow = Property(bool, readOpenInNewWindow, setOpenInNewWindow)

    def readPasswordProtected(self) -> bool:
        """
        Whether or not this button is password protected.

        Returns
        -------
        bool
        -------
        """
        return self._password_protected

    def setPasswordProtected(self, value: bool) -> None:
        """
        Whether or not this button is password protected.

        Parameters
        ----------
        value : bool
        """
        if self._password_protected != value:
            self._password_protected = value

    passwordProtected = Property(bool, readPasswordProtected, setPasswordProtected)

    def readPassword(self) -> str:
        """
        Password to be encrypted using SHA256.

        .. warning::
          To avoid issues exposing the password this method always returns an empty string.

        Returns
        -------
        str
        """
        return ""

    def setPassword(self, value: str) -> None:
        """
        Password to be encrypted using SHA256.

        Parameters
        ----------
        value : str
        The password to be encrypted
        """
        if value is not None and value != "":
            sha = hashlib.sha256()
            sha.update(value.encode())
            # Use the setter as it also checks whether the existing password is the same with the
            # new one, and only updates if the new password is different
            self.protectedPassword = sha.hexdigest()

            # Make sure designer knows it should save the protectedPassword field
            formWindow = QtDesigner.QDesignerFormWindowInterface.findFormWindow(self)
            if formWindow:
                formWindow.cursor().setProperty("protectedPassword", self.protectedPassword)

    password = Property(str, readPassword, setPassword)

    def readProtectedPassword(self) -> str:
        """
        The encrypted password.

        Returns
        -------
        str
        """
        return self._protected_password

    def setProtectedPassword(self, value: str) -> None:
        if self._protected_password != value:
            self._protected_password = value

    protectedPassword = Property(str, readProtectedPassword, setProtectedPassword)

    def readFollowSymlinks(self) -> bool:
        """
        If True, any symlinks in the path to filename (including the base path of the parent display) will be followed,
        so that it will always use the canonical path. If False (default), the file will be searched without
        canonicalizing the path beforehand.

        Note that it will not work on Windows if you're using a Python version prior to 3.8.

        Returns
        -------
        bool
        """
        return self._follow_symlinks

    def setFollowSymlinks(self, follow_symlinks: bool) -> None:
        """
        If True, any symlinks in the path to filename (including the base path of the parent display)
        will be followed, so that it will always use the canonical path.
        If False (default), the file will be searched using the non-canonical path.

        Note that it will not work on Windows if you're using a Python version prior to 3.8.

        Parameters
        ----------
        follow_symlinks : bool
        """
        self._follow_symlinks = follow_symlinks

    followSymlinks = Property(bool, readFollowSymlinks, setFollowSymlinks)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._menu_needs_rebuild:
            self._rebuild_menu()
        if event.button() == Qt.LeftButton and event.modifiers() == Qt.ShiftModifier:
            self._shift_key_was_down = True
        else:
            self._shift_key_was_down = False
        super().mousePressEvent(event)

    def push_button_release_event(self, mouse_event: QMouseEvent) -> None:
        """
        Opens the related display given by `filename`.
        If the Shift Key is hold it will open in a new window.

        Called when a mouse button is released. A widget receives mouse
        release events when it has received the corresponding mouse press
        event. This means that if the user presses the mouse inside your
        widget, then drags the mouse somewhere else before releasing the
        mouse button, your widget receives the release event.

        Parameters
        ----------
        mouse_event : QMouseEvent

        """
        if mouse_event.button() != Qt.LeftButton:
            return super().mouseReleaseEvent(mouse_event)
        if self.menu() is not None:
            return super(PyDMRelatedDisplayButton, self).mouseReleaseEvent(mouse_event)
        try:
            for item in self._get_items():
                self.open_display(item["filename"], item["macros"], target=None)
                break
        except Exception:
            logger.exception("Failed to open display.")
        finally:
            super().mouseReleaseEvent(mouse_event)

    def validate_password(self) -> bool:
        """
        If the widget is ```passwordProtected```, this method will prompt
        the user for the correct password.

        Returns
        -------
        bool
            True in case the password was correct of if the widget is not
            password protected.
        """
        if not self._password_protected:
            return True

        pwd, ok = QInputDialog().getText(None, "Authentication", "Please enter your password:", QLineEdit.Password, "")
        pwd = str(pwd)
        if not ok or pwd == "":
            return False

        sha = hashlib.sha256()
        sha.update(pwd.encode())
        pwd_encrypted = sha.hexdigest()
        if pwd_encrypted != self._protected_password:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Invalid password.")
            msg.setWindowTitle("Error")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setDefaultButton(QMessageBox.Ok)
            msg.setEscapeButton(QMessageBox.Ok)
            msg.exec_()
            return False
        return True

    @Slot()
    def handle_open_new_window_action(self) -> None:
        """
        Handle the "Open in New Window" action.

        Returns
        -------
        None.

        """
        for item in self._get_items():
            try:
                self.open_display(item["filename"], item["macros"], target=self.NEW_WINDOW)
            except Exception:
                logger.exception("Failed to open display.")

    def _assemble_menu(self, menu, target=None, track_actions=False):
        if self._entry_channels:
            menu.setToolTipsVisible(True)
        for item in self._get_items():
            try:
                action = menu.addAction(item["title"])
                action.triggered.connect(partial(self.open_display, item["filename"], item["macros"], target=target))
                if item["alarm_channel"]:
                    action.setIcon(self._entry_icon(item["index"]))
                    action.setIconVisibleInMenu(True)
                    action.setToolTip(item["alarm_channel"])
                if track_actions:
                    self._entry_actions[item["index"]] = action
            except Exception:
                logger.exception("Failed to open display.")

    def channels(self):
        """
        The button's own channel plus the per-entry alarm channels of the dropdown menu.

        Returns
        -------
        list of PyDMChannel or None
        """
        base = super().channels() or []
        chans = list(base) + list(self._entry_channels.values())
        return chans or None

    @Slot()
    def open_display(self, filename, macro_string="", target=None):
        """
        Open the configured `filename` with the given `target`.

        Parameters
        ----------
        target : int
            PyDMRelatedDisplayButton.EXISTING_WINDOW or 0 will open the
            file on the same window. PyDMRelatedDisplayButton.NEW_WINDOW
            or 1 will result on a new process.

        Returns
        -------
        display : Display
            The widget that was opened. Useful for testing and debug.
        """
        if not self.validate_password():
            return None

        parent_display = self.find_parent_display()
        base_path = ""
        macros = {}
        if parent_display:
            parent_file_path = parent_display.loaded_file()
            if self._follow_symlinks:
                parent_file_path = os.path.realpath(parent_file_path)
            base_path = os.path.dirname(parent_file_path)
            macros = copy.copy(parent_display.macros())

        fname = find_file(
            filename, base_path=base_path, raise_if_not_found=True, subdir_scan_enabled=self._recursive_display_search
        )
        widget_macros = parse_macro_string(macro_string)
        macros.update(widget_macros)

        screen_target = None
        if target is self.NEW_WINDOW:
            screen_target = ScreenTarget.NEW_PROCESS
        if self._shift_key_was_down:
            target = self.NEW_WINDOW
            screen_target = ScreenTarget.NEW_PROCESS
        if target is None:
            if self._open_in_new_window:
                target = self.NEW_WINDOW
                screen_target = ScreenTarget.NEW_PROCESS
            else:
                target = self.EXISTING_WINDOW
                screen_target = None

        if is_pydm_app():
            if target == self.NEW_WINDOW:
                return load_file(fname, macros=macros, target=screen_target)
            else:
                return self.window().open(fname, macros=macros)
        else:
            display = load_file(fname, macros=macros, target=ScreenTarget.DIALOG)
            # Not a pydm app: need to give our new display proper pydm styling
            # Usually done in PyDMApplication
            merge_widget_stylesheet(widget=display)
            # Clean up references to closed subdisplays
            for old_display in list(self._subdisplays):
                # isVisible only goes False after clicking "close"
                if not old_display.isVisible():
                    self._subdisplays.remove(old_display)
            # Retain a reference to avoid garbage collection
            self._subdisplays.append(display)
            return display

    def context_menu(self):
        try:
            menu = super().context_menu()
        except Exception:
            menu = QMenu(self)
        if len(menu.findChildren(QAction)) > 0:
            menu.addSeparator()
        if len(self.filenames) <= 1:
            menu.addAction(self.open_in_new_window_action)
            return menu
        sub_menu = menu.addMenu("Open in New Window")
        self._assemble_menu(sub_menu, target=self.NEW_WINDOW)
        return menu

    @Slot(QPoint)
    def show_context_menu(self, pos: QPoint) -> None:
        menu = self.context_menu()
        menu.exec_(self.mapToGlobal(pos))
