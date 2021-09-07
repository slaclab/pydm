from qtpy.QtWidgets import QFrame, QApplication, QLabel, QVBoxLayout, QWidget
from qtpy.QtCore import Qt, QSize, Property, QTimer

import copy
import os.path
import logging
from .base import PyDMPrimitiveWidget
from ..utilities import (is_pydm_app, establish_widget_connections,
                         close_widget_connections, macro, is_qt_designer,
                         find_file)
from ..display import (load_file)

logger = logging.getLogger(__name__)


class PyDMEmbeddedDisplay(QFrame, PyDMPrimitiveWidget):
    """
    A QFrame capable of rendering a PyDM Display

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label

    """

    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        PyDMPrimitiveWidget.__init__(self)
        self.app = QApplication.instance()
        self._filename = None
        self._macros = None
        self._embedded_widget = None
        self._disconnect_when_hidden = True
        self._is_connected = False
        self._only_load_when_shown = True
        self._needs_load = True
        self._load_error_timer = None
        self._load_error = None
        self.layout = QVBoxLayout(self)
        self.err_label = QLabel(self)
        self.err_label.setAlignment(Qt.AlignHCenter)
        self.layout.addWidget(self.err_label)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.err_label.hide()

    def init_for_designer(self):
        self.setFrameShape(QFrame.Box)

    def minimumSizeHint(self):
        """
        This property holds the recommended minimum size for the widget.

        Returns
        -------
        QSize
        """
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
        if self._needs_load and (
                not self._only_load_when_shown or self.isVisible() or is_qt_designer()):
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
                base_path = os.path.dirname(parent_display.loaded_file())

            fname = find_file(self.filename, base_path=base_path)
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
        self.err_label.setText(
            "Could not open {filename}.\nError: {err}".format(
                filename=self._filename, err=e))
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
        should_reconnect = False
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