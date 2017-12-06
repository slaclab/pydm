from ..PyQt.QtGui import QPushButton, QCursor
from ..PyQt.QtCore import pyqtSlot, pyqtProperty, Qt, QSize
import json
from .base import PyDMPrimitiveWidget
from ..utilities import IconFont


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
    EXISTING_WINDOW = 0;
    NEW_WINDOW = 1;

    def __init__(self, parent=None, filename=None):
        QPushButton.__init__(self, parent)
        PyDMPrimitiveWidget.__init__(self)
        self.mouseReleaseEvent = self.push_button_release_event

        self.iconFont = IconFont()
        icon = self.iconFont.icon("file")
        self.setIconSize(QSize(16, 16))
        self.setIcon(icon)

        self.setCursor(QCursor(icon.pixmap(16, 16)))

        self._display_filename = filename
        self._macro_string = None
        self._open_in_new_window = False

    def check_enable_state(self):
        """
        Because the related display button's channel is only used for alarm
        status, the widget is never disabled by connection state.
        """
        self.setEnabled(True)

    @pyqtProperty(str)
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
            if self._display_filename is None or len(self._display_filename) < 1:
                self.setEnabled(False)

    @pyqtProperty(str)
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

    @pyqtProperty(bool)
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
        try:
            if mouse_event.modifiers() == Qt.ShiftModifier or self._open_in_new_window:
                self.open_display(target=self.NEW_WINDOW)
            else:
                self.open_display()
        except:
            pass
        finally:
            super(PyDMRelatedDisplayButton, self).mouseReleaseEvent(mouse_event)

    @pyqtSlot()
    def open_display(self, target=EXISTING_WINDOW):
        """
        Open the configured `filename` with the given `target`.

        Parameters
        ----------
        target : int
            PyDMRelatedDisplayButton.EXISTING_WINDOW or 0 will open the
            file on the same window. PyDMRelatedDisplayButton.NEW_WINDOW
            or 1 will result on a new process.
        """
        if self.displayFilename is None:
            return
        macros = None
        if self._macro_string is not None:
            macros = json.loads(str(self._macro_string))
        try:
            if target == self.EXISTING_WINDOW:
                self.window().go(self.displayFilename, macros=macros)
            if target == self.NEW_WINDOW:
                self.window().new_window(self.displayFilename, macros=macros)
        except (IOError, OSError, ValueError, ImportError) as e:
            self.window().statusBar().showMessage("Cannot open file: '{0}'. Reason: '{1}'.".format(self.displayFilename, e), 5000)
