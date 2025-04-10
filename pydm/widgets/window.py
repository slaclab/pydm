import warnings
from qtpy.QtWidgets import QWidget
from qtpy.QtCore import Property
from typing import Optional
from .base import is_qt_designer


class PyDMWindow(QWidget):
    """
    QWidget with support for some custom PyDM properties. Right now it only
    supports disabling the menu bar, nav bar, and status bar by default. This
    widget will only function if it is at the root of the UI hierarchy.
    This class inherits from QWidget. It is NOT a PyDMWidget.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Window. Should ideally be None
    """

    def __init__(self, parent: Optional[QWidget] = None):
        if parent is not None and not is_qt_designer():
            warnings.warn("PyDMWindow must be at the root of the UI hierarchy, or it will not function properly!")

        super().__init__(parent)
        self._hide_menu_bar = False
        self._hide_nav_bar = False
        self._hide_status_bar = False

    @Property(bool)
    def hideMenuBar(self):
        """
        Whether or not the widget should automatically disable the
        menu bar when the display is loaded.

        Returns
        -------
        hide_menu_bar : bool
            The configured value
        """
        return self._hide_menu_bar

    @hideMenuBar.setter
    def hideMenuBar(self, new_val):
        """
        Whether or not the widget should automatically disable the
        menu bar when the display is loaded.

        Parameters
        ----------
        new_val : bool
            The new configuration to use
        """
        self._hide_menu_bar = new_val

    @Property(bool)
    def hideNavBar(self):
        """
        Whether or not the widget should automatically disable the
        nav bar when the display is loaded.

        Returns
        -------
        hide_nav_bar : bool
            The configured value
        """
        return self._hide_nav_bar

    @hideNavBar.setter
    def hideNavBar(self, new_val):
        """
        Whether or not the widget should automatically disable the
        nav bar when the display is loaded.

        Parameters
        ----------
        new_val : bool
            The new configuration to use
        """
        self._hide_nav_bar = new_val

    @Property(bool)
    def hideStatusBar(self):
        """
        Whether or not the widget should automatically disable the
        status bar when the display is loaded.

        Returns
        -------
        hide_status_bar : bool
            The configured value
        """
        return self._hide_status_bar

    @hideStatusBar.setter
    def hideStatusBar(self, new_val):
        """
        Whether or not the widget should automatically disable the
        status bar when the display is loaded.

        Parameters
        ----------
        new_val : bool
            The new configuration to use
        """
        self._hide_status_bar = new_val
