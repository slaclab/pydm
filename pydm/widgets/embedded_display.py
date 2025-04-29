from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent
from qtpy.QtWidgets import QAction, QFrame, QApplication, QLabel, QMenu, QVBoxLayout
from qtpy.QtCore import QPoint, Qt, QSize, Property, QTimer

import copy
import os.path
import logging
from .base import PyDMPrimitiveWidget
from .baseplot import BasePlot
from pydm.utilities import (
    is_pydm_app,
    establish_widget_connections,
    close_widget_connections,
    macro,
    is_qt_designer,
    find_file,
)
from pydm.display import load_file, ScreenTarget

logger = logging.getLogger(__name__)

_embeddedDisplayRuleProperties = {"Filename": ["filename", str]}


class PyDMEmbeddedDisplay(QFrame, PyDMPrimitiveWidget):
    """
    A QFrame capable of rendering a PyDM Display

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label

    """

    new_properties = _embeddedDisplayRuleProperties

    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        PyDMPrimitiveWidget.__init__(self)
        self.app = QApplication.instance()
        self._filename = None
        self._recursive_display_search = False
        self._macros = None
        self._embedded_widget = None
        self._disconnect_when_hidden = True
        self._is_connected = False
        self._only_load_when_shown = True
        self._needs_load = True
        self._load_error_timer = None
        self._load_error = None
        self._follow_symlinks = False
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.open_in_new_window_action = QAction("Open in New Window", self)
        self.open_in_new_window_action.triggered.connect(self.open_display_in_new_window)

        self.layout = QVBoxLayout(self)
        self.err_label = QLabel(self)
        self.err_label.setAlignment(Qt.AlignHCenter)
        self.layout.addWidget(self.err_label)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.err_label.hide()

    def init_for_designer(self):
        self.setFrameShape(QFrame.Box)

    def sizePolicy(self):
        """
        This holds the sizePolicy for the widget.

        Returns
        -------
        QSize
        """
        if self._embedded_widget is not None:
            return self._embedded_widget.sizePolicy()
        return super().sizePolicy()

    def sizeHint(self):
        """
        This holds the recommended size for the widget.

        Returns
        -------
        QSize
        """
        if self._embedded_widget is not None:
            return self._embedded_widget.sizeHint()
        return QSize(100, 100)

    def minimumSizeHint(self):
        """
        This holds the recommended minimum size for the widget.

        Returns
        -------
        QSize
        """
        if self._embedded_widget is not None:
            return self._embedded_widget.minimumSizeHint()
        # This is totally arbitrary, I just want *some* visible nonzero size
        return QSize(100, 100)

    @Property(str)
    def macros(self):
        """
        JSON-formatted string containing macro variables to pass to the embedded file.

        Returns
        -------
        str
        """
        if self._macros is None:
            return ""
        return self._macros

    @macros.setter
    def macros(self, new_macros):
        """
        JSON-formatted string containing macro variables to pass to the embedded file.

        .. warning::
        If the macros property is not defined before the filename property,
        The widget will not have any macros defined when it loads the embedded file.
        This behavior will be fixed soon.

        Parameters
        ----------
        new_macros : str
        """
        new_macros = str(new_macros)
        if new_macros != self._macros:
            self._macros = new_macros
            self._needs_load = True
        self.load_if_needed()

    @Property(str)
    def filename(self):
        """
        Filename of the display to embed.

        Returns
        -------
        str
        """
        if self._filename is None:
            return ""
        return self._filename

    @filename.setter
    def filename(self, filename):
        """
        Filename of the display to embed.

        Parameters
        ----------
        filename : str
        """
        filename = str(filename)
        if filename != self._filename:
            self._filename = filename
            self._needs_load = True
            if is_qt_designer():
                if self._load_error_timer:
                    # Kill the timer here. If new filename still causes the problem, it will be restarted
                    self._load_error_timer.stop()
                    self._load_error_timer = None
                self.clear_error_text()
        self.load_if_needed()

    @Property(bool)
    def recursiveDisplaySearch(self) -> bool:
        """
        Whether or not to search for a provided display file recursively
        in subfolders relative to the location of this display.

        Returns
        -------
        bool
            If recursive search is enabled.
        """
        return self._recursive_display_search

    @recursiveDisplaySearch.setter
    def recursiveDisplaySearch(self, new_value) -> None:
        """
        Set whether or not to search for a provided display file recursively
        in subfolders relative to the location of this display.

        Parameters
        ----------
        new_value
            If recursive search should be enabled.
        """
        self._recursive_display_search = new_value

    def set_macros_and_filename(self, new_filename, new_macros):
        """
        A method to change both macros and the filename of an embedded display.
        the method takes in a Filename of the display to embed and a
        JSON-formatted string containing macro variables to pass to the embedded file.

        Parameters
        ----------
        new_macros : str
        new_filename : str
        """
        new_macros = str(new_macros)
        if new_macros != self._macros:
            self._macros = new_macros
            self._needs_load = True

        self.filename = new_filename

    def parsed_macros(self):
        """
        Dictionary containing the key value pair for each macro specified.

        Returns
        --------
        dict
        """
        parent_display = self.find_parent_display()
        parent_macros = {}
        if parent_display:
            parent_macros = copy.copy(parent_display.macros())
        widget_macros = macro.parse_macro_string(self.macros)
        parent_macros.update(widget_macros)
        return parent_macros

    def load_if_needed(self):
        if self._needs_load and (not self._only_load_when_shown or self.isVisible() or is_qt_designer()):
            self.embedded_widget = self.open_file()

    def open_file(self, force=False):
        """
        Opens the widget specified in the widget's filename property.

        Returns
        -------
        display : QWidget
        """
        if (not force) and (not self._needs_load):
            return

        if not self.filename:
            return

        try:
            parent_display = self.find_parent_display()
            base_path = ""
            if parent_display:
                parent_file_path = parent_display.loaded_file()
                if self._follow_symlinks:
                    parent_file_path = os.path.realpath(parent_file_path)
                base_path = os.path.dirname(parent_file_path)

            fname = find_file(
                self.filename,
                base_path=base_path,
                raise_if_not_found=True,
                subdir_scan_enabled=self._recursive_display_search,
            )
            w = load_file(fname, macros=self.parsed_macros(), target=None)
            self._needs_load = False
            self.clear_error_text()
            return w
        except Exception as e:
            self._load_error = e
            if self._load_error_timer:
                self._load_error_timer.stop()
            self._load_error_timer = QTimer(self)
            self._load_error_timer.setSingleShot(True)
            self._load_error_timer.setTimerType(Qt.VeryCoarseTimer)
            self._load_error_timer.timeout.connect(self._display_designer_load_error)
            self._load_error_timer.start(1000)
        return None

    def clear_error_text(self):
        if self._load_error_timer:
            self._load_error_timer.stop()
        self.err_label.clear()
        self.err_label.hide()

    def display_error_text(self, e):
        self.err_label.setText("Could not open {filename}.\nError: {err}".format(filename=self._filename, err=e))
        self.err_label.show()

    @property
    def embedded_widget(self):
        """
        The embedded widget being displayed.

        Returns
        -------
        QWidget
        """
        return self._embedded_widget

    @embedded_widget.setter
    def embedded_widget(self, new_widget):
        """
        Defines the embedded widget to display inside the QFrame

        Parameters
        ----------
        new_widget : QWidget
        """
        if new_widget is self._embedded_widget:
            return
        if self._embedded_widget is not None:
            self.layout.removeWidget(self._embedded_widget)
            self._embedded_widget.deleteLater()
            self._embedded_widget = None
        if new_widget is not None:
            self._embedded_widget = new_widget
            self._embedded_widget.setParent(self)
            self.layout.addWidget(self._embedded_widget)
            self.err_label.hide()
            self._embedded_widget.show()
            self._is_connected = True

    def connect(self):
        """
        Establish the connection between the embedded widget and
        the channels associated with it.
        """
        if self._is_connected or self.embedded_widget is None:
            return
        establish_widget_connections(self.embedded_widget)
        self._is_connected = True

    def disconnect(self):
        """
        Disconnects the embedded widget from the channels
        associated with it.
        """
        if not self._is_connected or self.embedded_widget is None:
            return
        close_widget_connections(self.embedded_widget)
        self._is_connected = False

    @Property(bool)
    def loadWhenShown(self):
        """
        If True, only load and display the file once the
        PyDMEmbeddedDisplayWidget is visible on screen.  This is very useful
        if you have many different PyDMEmbeddedWidgets in different tabs of a
        QTabBar or PyDMTabBar: only the tab that the user is looking at will
        be loaded, which can greatly speed up the launch time of a display.

        If this property is changed from 'True' to 'False', and the file has
        not been loaded yet, it will be loaded immediately.

        Returns
        -------
        bool
        """
        return self._only_load_when_shown

    @loadWhenShown.setter
    def loadWhenShown(self, val):
        self._only_load_when_shown = val
        self.load_if_needed()

    @Property(bool)
    def disconnectWhenHidden(self):
        """
        Disconnect from PVs when this widget is not visible.

        Returns
        -------
        bool
        """
        return self._disconnect_when_hidden

    @disconnectWhenHidden.setter
    def disconnectWhenHidden(self, disconnect_when_hidden):
        """
        Disconnect from PVs when this widget is not visible.

        Parameters
        ----------
        disconnect_when_hidden : bool
        """
        self._disconnect_when_hidden = disconnect_when_hidden

    @Property(bool)
    def followSymlinks(self) -> bool:
        """
        If True, any symlinks in the path to filename (including the base path of the parent display)
        will be followed, so that it will always use the canonical path. If False (default),
        the file will be searched without canonicalizing the path beforehand.

        Note that it will not work on Windows if you're using a Python version prior to 3.8.

        Returns
        -------
        bool
        """
        return self._follow_symlinks

    @followSymlinks.setter
    def followSymlinks(self, follow_symlinks: bool) -> None:
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

    def showEvent(self, e):
        """
        Show events are sent to widgets that become visible on the screen.

        Parameters
        ----------
        event : QShowEvent
        """
        if self._only_load_when_shown:
            w = self.open_file()
            if w:
                self.embedded_widget = w
        if self.disconnectWhenHidden:
            self.connect()

    def hideEvent(self, e):
        """
        Hide events are sent to widgets that become invisible on the screen.

        Parameters
        ----------
        event : QHideEvent
        """
        if self.disconnectWhenHidden:
            self.disconnect()

    def _display_designer_load_error(self):
        self._load_error_timer = None
        logger.exception("Exception while opening embedded display file.", exc_info=self._load_error)
        if self._load_error:
            self.display_error_text(self._load_error)

    def open_display_in_new_window(self) -> None:
        """Open the embedded display in a new window"""
        if not self.filename:
            return

        parent_display = self.find_parent_display()
        base_path = ""
        if parent_display:
            parent_file_path = parent_display.loaded_file()
            if self._follow_symlinks:
                parent_file_path = os.path.realpath(parent_file_path)
            base_path = os.path.dirname(parent_file_path)

        file_path = find_file(
            self.filename,
            base_path=base_path,
            raise_if_not_found=True,
            subdir_scan_enabled=self._recursive_display_search,
        )
        macros = self.parsed_macros()

        if is_pydm_app():
            load_file(file_path, macros=macros)
        else:
            load_file(file_path, macros=macros, target=ScreenTarget.DIALOG)

    def create_context_menu(self, pos: QPoint) -> QMenu:
        """Create the right-click context menu for this embedded widget based on the location of the mouse click"""
        if self._embedded_widget is None:
            return

        menu = None
        # Plot widgets use their own custom event handling, so we check to see if they were
        # clicked on here. If so, just reuse the context menu they already have built. (Not
        # specifically checking for these would clobber their context menus)
        plot_widgets = self.findChildren(BasePlot)
        for plot in plot_widgets:
            try:
                if plot.geometry().contains(pos):
                    menu = plot.getViewBox().getMenu(None)
                    if menu is not None:  # Need to add sub-menus still
                        # Mock up an event that the pyqtgraph api requires. Just want to create it without any
                        # initialization of attributes (would require more unnecessary object creations)
                        accept_event = object.__new__(MouseClickEvent)
                        accept_event.accepted = True
                        accept_event.acceptedItem = plot.getViewBox()
                        menu = plot.getViewBox().scene().addParentContextMenus(plot.getViewBox(), menu, accept_event)
            except AttributeError:
                pass

        # Otherwise check if a menu already exists, and create a new one if not
        if menu is None:
            try:
                menu = self._embedded_widget.context_menu()
            except AttributeError:
                menu = QMenu(self)

        if len(menu.findChildren(QAction)) > 0:
            menu.addSeparator()
        menu.addAction(self.open_in_new_window_action)
        return menu

    def show_context_menu(self, pos: QPoint) -> None:
        """Display the right-click context menu for this embedded widget at the location of the mouse click"""
        menu = self.create_context_menu(pos)
        if menu is not None:
            menu.exec_(self.mapToGlobal(pos))
