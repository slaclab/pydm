from qtpy.QtWidgets import QPushButton, QMenu, QAction
from qtpy.QtGui import QCursor, QIcon
from qtpy.QtCore import Slot, Property, Qt, QSize, QPoint
import os
import json
import logging
from functools import partial
from .base import PyDMPrimitiveWidget
from ..utilities import IconFont
from ..utilities.macro import find_base_macros, parse_macro_string

logger = logging.getLogger(__name__)


class PyDMRelatedDisplayButton(QPushButton, PyDMPrimitiveWidget):
    """
    A QPushButton capable of opening a new Display at the same of at a
    new window.

    Parameters
    ----------
    init_channel : str, optional
        The channel to be used by the widget.

    filename : str, optional
        The file to be opened
    """
    # Constants for determining where to open the display.
    EXISTING_WINDOW = 0
    NEW_WINDOW = 1

    def __init__(self, parent=None, filename=None):
        QPushButton.__init__(self, parent)
        PyDMPrimitiveWidget.__init__(self)
        self.mouseReleaseEvent = self.push_button_release_event
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.iconFont = IconFont()
        self._icon = self.iconFont.icon("file")
        self.setIconSize(QSize(16, 16))
        self.setIcon(self._icon)

        self._additional_filenames = []
        self._additional_titles = []
        self.num_additional_items = 0
        self._shift_key_was_down = False
        self.setCursor(QCursor(self._icon.pixmap(16, 16)))
        self._display_menu_items = None
        self._display_filename = filename if filename is not None else ""
        self._macro_string = None
        self._open_in_new_window = False
        self.open_in_new_window_action = QAction("Open in New Window", self)
        self.open_in_new_window_action.triggered.connect(partial(self.open_display, self.NEW_WINDOW))
        self._show_icon = True

    @Property('QStringList')
    def additionalFilenames(self):
        return self._additional_filenames
    
    @additionalFilenames.setter
    def additionalFilenames(self, val):
        self._additional_filenames = val
        self._rebuild_menu()
        
    @Property('QStringList')
    def additionalTitles(self):
        return self._additional_titles
    
    @additionalTitles.setter
    def additionalTitles(self, val):
        self._additional_titles = val
        self._rebuild_menu()
    
    def _rebuild_menu(self):
        if not (any(self._additional_titles) or any(self._additional_filenames)):
            self._additional_titles = []
            self._additional_filenames = []
        self.num_additional_items = max(len(self._additional_titles), len(self._additional_filenames))
        self._additional_titles.extend([""] * max(self.num_additional_items - len(self._additional_titles), 0))
        self._additional_filenames.extend([""] * max(self.num_additional_items - len(self._additional_filenames), 0))
        if self.num_additional_items < 1:
            self.setMenu(None)
        else:
            menu = QMenu(self)
            target = self.NEW_WINDOW if self._open_in_new_window else self.EXISTING_WINDOW
            if self.displayFilename:
                action = menu.addAction(self.text())
                action.triggered.connect(partial(self.open_display, target, self.displayFilename))
            for (title, filename) in zip(self._additional_titles, self._additional_filenames):
                action = menu.addAction(title)
                action.triggered.connect(partial(self.open_display, target, filename))
            self.setMenu(menu)
        self._disable_if_no_files()
    
    def _disable_if_no_files(self):
        if not self._display_filename and self.num_additional_items < 1:
            self.setEnabled(False)

    @Property(bool)
    def showIcon(self):
        """
        Whether or not we should show the selected Icon.

        Returns
        -------
        bool
        """
        return self._show_icon

    @showIcon.setter
    def showIcon(self, value):
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

    @Property(str)
    def displayFilename(self):
        """
        The filename to open

        Returns
        -------
        str
        """
        return str(self._display_filename)

    @displayFilename.setter
    def displayFilename(self, value):
        """
        The filename to open

        Parameters
        ----------
        value : str
        """
        if self._display_filename != value:
            self._display_filename = str(value)
            self._rebuild_menu()
            
    @Property(str)
    def macros(self):
        """
        The macro substitutions to use when launching the display, in JSON object format.

        Returns
        -------
        str
        """
        if self._macro_string is None:
            return ""
        return self._macro_string

    @macros.setter
    def macros(self, new_macros):
        """
        The macro substitutions to use when launching the display, in JSON object format.

        Parameters
        ----------
        new_macros : str
        """
        if len(new_macros) < 1:
            self._macro_string = None
        else:
            self._macro_string = new_macros

    @Property(bool)
    def openInNewWindow(self):
        """
        If true, the button will open the display in a new window, rather than in the existing window.

        Returns
        -------
        bool
        """
        return self._open_in_new_window

    @openInNewWindow.setter
    def openInNewWindow(self, open_in_new):
        """
        If true, the button will open the display in a new window, rather than in the existing window.

        Parameters
        ----------
        open_in_new : bool
        """
        self._open_in_new_window = open_in_new
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.modifiers() == Qt.ShiftModifier:
            self._shift_key_was_down = True
        else:
            self._shift_key_was_down = False
        super(PyDMRelatedDisplayButton, self).mousePressEvent(event)

    def push_button_release_event(self, mouse_event):
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
            return super(PyDMRelatedDisplayButton, self).mouseReleaseEvent(mouse_event)
        if self.menu() is not None:
            return super(PyDMRelatedDisplayButton, self).mouseReleaseEvent(mouse_event)
        try:
            if self._open_in_new_window:
                self.open_display(target=self.NEW_WINDOW)
            else:
                self.open_display()
        except Exception as ex:
            logger.exception("Failed to open display.")
            pass
        finally:
            super(PyDMRelatedDisplayButton, self).mouseReleaseEvent(mouse_event)

    @Slot()
    def open_display(self, target=EXISTING_WINDOW, filename=None):
        """
        Open the configured `filename` with the given `target`.

        Parameters
        ----------
        target : int
            PyDMRelatedDisplayButton.EXISTING_WINDOW or 0 will open the
            file on the same window. PyDMRelatedDisplayButton.NEW_WINDOW
            or 1 will result on a new process.
        """
        if not filename:
            filename = self.displayFilename
            
        # Check for None and ""
        if not filename:
            return
            
        if self._shift_key_was_down:
            target = self.NEW_WINDOW
        
        macros = parse_macro_string(self._macro_string)
        base_macros = find_base_macros(self)
        merged_macros = base_macros.copy()
        merged_macros.update(macros)

        if target == self.EXISTING_WINDOW:
            self.window().go(filename, macros=merged_macros)
        if target == self.NEW_WINDOW:
            self.window().new_window(filename,
                                     macros=merged_macros)

    def context_menu(self):
        try:
            menu = super(PyDMRelatedDisplayButton, self).context_menu()
        except:
            menu = QMenu(self)
        if len(menu.findChildren(QAction)) > 0:
            menu.addSeparator()
        menu.addAction(self.open_in_new_window_action)
        return menu

    @Slot(QPoint)
    def show_context_menu(self, pos):
        menu = self.context_menu()
        menu.exec_(self.mapToGlobal(pos))
