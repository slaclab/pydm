import copy
import os
import logging
import warnings
from functools import partial

from qtpy.QtWidgets import QPushButton, QMenu, QAction
from qtpy.QtGui import QCursor, QIcon
from qtpy.QtCore import Slot, Property, Qt, QSize, QPoint

from .base import PyDMPrimitiveWidget
from ..utilities import IconFont, find_file, is_pydm_app
from ..utilities.macro import parse_macro_string
from ..display import (load_file, ScreenTarget)


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

        if 'Text' not in PyDMRelatedDisplayButton.RULE_PROPERTIES:
            PyDMRelatedDisplayButton.RULE_PROPERTIES = PyDMRelatedDisplayButton.RULE_PROPERTIES.copy()
            PyDMRelatedDisplayButton.RULE_PROPERTIES.update(
                {'Text': ['setText', str]})

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
        self.num_additional_items = 0
        self._shift_key_was_down = False
        self.setCursor(QCursor(self._icon.pixmap(16, 16)))
        self._display_menu_items = None
        self._display_filename = ""
        self._macro_string = None
        self._open_in_new_window = False
        self.open_in_new_window_action = QAction("Open in New Window", self)
        self.open_in_new_window_action.triggered.connect(
            self.handle_open_new_window_action)
        self._show_icon = True
        self._menu_needs_rebuild = True

    @Property('QStringList')
    def filenames(self):
        return self._filenames
    
    @filenames.setter
    def filenames(self, val):
        self._filenames = val
        self._menu_needs_rebuild = True
        
    @Property('QStringList')
    def titles(self):
        return self._titles
    
    @titles.setter
    def titles(self, val):
        self._titles = val
        self._menu_needs_rebuild = True

    def _get_items(self):
        """
        Aggregate file entry information.

        Yields
        ------
        item : dict
            Containing filename, title, and macros/empy macros
            Only containing valid entries or nothing

        """
        for i, filename in enumerate(self.filenames):
            if not filename:
                continue
            item = {'filename': filename}
            if i >= len(self.titles):
                item['title'] = filename
            else:
                item['title'] = self.titles[i]
            if i < len(self.macros):
                item['macros'] = self.macros[i]
            else:
                item['macros'] = ""
            yield item

    def _rebuild_menu(self):
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
        self._assemble_menu(menu, target=None)
        self.setMenu(menu)
        self._menu_needs_rebuild = False

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

    @Property(str, designable=False)
    def displayFilename(self):
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

    @displayFilename.setter
    def displayFilename(self, value):
        """
        DEPRECATED: use the 'filenames' property.
        Any value set to this property is appended to the 'filenames'
        property, then 'displayFilename' is cleared.

        Parameters
        ----------
        value : str
        """
        warnings.warn("'PyDMRelatedDisplayButton.displayFilename' is deprecated, "
                      "use 'PyDMRelatedDisplayButton.filenames' instead.")
        if value:
            if value in self.filenames:
                return
            file_list = [value]
            self.filenames = self.filenames + file_list
        self._display_filename = ""
            
    @Property('QStringList')
    def macros(self):
        """
        The macro substitutions to use when launching the display, in JSON object format.

        Returns
        -------
        list of str
        """
        return self._macros

    @macros.setter
    def macros(self, new_macros):
        """
        The macro substitutions to use when launching the display, in JSON object format.

        Parameters
        ----------
        new_macros : list of str
        """
        #Handle the deprecated form of macros where it was a single string.
        if isinstance(new_macros, str):
            new_macros = [new_macros]
        self._macros = new_macros

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
        if self._menu_needs_rebuild:
            self._rebuild_menu()
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
            for item in self._get_items():
                self.open_display(item['filename'], item['macros'],
                                  target=None)
                break
        except Exception:
            logger.exception("Failed to open display.")
        finally:
            super(PyDMRelatedDisplayButton, self).mouseReleaseEvent(
                mouse_event)

    @Slot()
    def handle_open_new_window_action(self):
        """
        Handle the "Open in New Window" action.

        Returns
        -------
        None.

        """
        for item in self._get_items():
            try:
                self.open_display(item['filename'], item['macros'],
                                  target=self.NEW_WINDOW)
            except Exception:
                logger.exception("Failed to open display.")

    def _assemble_menu(self, menu, target=None):
        for item in self._get_items():
            try:
                action = menu.addAction(item['title'])
                action.triggered.connect(
                    partial(self.open_display, item['filename'],
                            item['macros'], target=target))
            except Exception:
                logger.exception("Failed to open display.")

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
        """
        parent_display = self.find_parent_display()
        base_path = ""
        macros = {}
        if parent_display:
            base_path = os.path.dirname(parent_display.loaded_file())
            macros = copy.copy(parent_display.macros())

        fname = find_file(filename, base_path=base_path)
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
                load_file(fname, macros=macros, target=screen_target)
            else:
                self.window().open(fname, macros=macros)
        else:
            w = load_file(fname, macros=macros, target=ScreenTarget.DIALOG)

    def context_menu(self):
        try:
            menu = super(PyDMRelatedDisplayButton, self).context_menu()
        except:
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
    def show_context_menu(self, pos):
        menu = self.context_menu()
        menu.exec_(self.mapToGlobal(pos))
