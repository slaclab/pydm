from qtpy.QtWidgets import QFrame, QApplication, QLabel, QVBoxLayout, QWidget
from qtpy.QtCore import Qt, QSize
from qtpy.QtCore import Property
import json
import os.path
import logging
from .base import PyDMPrimitiveWidget
from ..utilities import (is_pydm_app, establish_widget_connections,
                         close_widget_connections, macro, is_qt_designer)
from ..utilities.display_loading import (load_ui_file, load_py_file)

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
        self.base_path = ""
        self.base_macros = {}
        if is_pydm_app():
          self.base_path = self.app.directory_stack[-1]
          self.base_macros = self.app.macro_stack[-1]
        self.layout = QVBoxLayout(self)
        self.err_label = QLabel(self)
        self.err_label.setAlignment(Qt.AlignHCenter)
        self.layout.addWidget(self.err_label)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.err_label.hide()
        if not is_pydm_app():
            self.setFrameShape(QFrame.Box)
        else:
            self.setFrameShape(QFrame.NoFrame)
        

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
        self._macros = str(new_macros)

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
            if self._only_load_when_shown and (not is_qt_designer()):
                self._needs_load = True
            else:
                self.embedded_widget = self.open_file()

    def parsed_macros(self):
        """
        Dictionary containing the key value pair for each macro specified.

        Returns
        --------
        dict
        """
        m = macro.find_base_macros(self)
        m.update(macro.parse_macro_string(self.macros))
        return m

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
        # Expand user (~ or ~user) and environment variables.
        fname = os.path.expanduser(os.path.expandvars(self.filename))
        if self.base_path:
            fname = os.path.join(self.base_path, fname)
        if not is_pydm_app():
            (filename, extension) = os.path.splitext(fname)
            if extension == ".ui":
                loadfunc = load_ui_file
            elif extension == ".py":
                loadfunc = load_py_file
            try:
                w = loadfunc(fname, macros=self.parsed_macros())
                self._needs_load = False
                self.clear_error_text()
                return w
            except Exception as e:
                logger.exception("Exception while opening embedded display file.")
                self.display_error_text(e)
            return None
        
        # If you get this far, you are running inside a PyDMApplication, load
        # using that system.
        try:
            if os.path.isabs(fname):
                w = self.app.open_file(fname, macros=self.parsed_macros())
            else:
                w = self.app.open_relative(fname, self,
                                              macros=self.parsed_macros())
            self._needs_load = False
            self.clear_error_text()
            return w
        except (ValueError, IOError) as e:
            self.display_error_text(e)

    def clear_error_text(self):
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

    def disconnect(self):
        """
        Disconnects the embedded widget from the channels
        associated with it.
        """
        if not self._is_connected or self.embedded_widget is None:
            return
        close_widget_connections(self.embedded_widget)

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
        if val is False and self._needs_load:
            self.embedded_widget = self.open_file()

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
