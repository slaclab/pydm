from qtpy.QtWidgets import QFrame, QApplication, QLabel, QVBoxLayout, QWidget
from qtpy.QtCore import Qt, QSize
from qtpy.QtCore import Property
import json
import os.path
from .base import PyDMPrimitiveWidget
from ..utilities import (is_pydm_app, establish_widget_connections,
                         close_widget_connections)


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
            # If we aren't in a PyDMApplication (usually that means we are in Qt Designer),
            # don't try to load the file, just show text with the filename.
            if not is_pydm_app():
                self.err_label.setText(self._filename)
                self.err_label.show()
                return
            try:
                self.embedded_widget = self.open_file()
            except ValueError as e:
                self.err_label.setText(
                    "Could not parse macro string.\nError: {}".format(e))
                self.err_label.show()
            except IOError as e:
                self.err_label.setText(
                    "Could not open {filename}.\nError: {err}".format(
                        filename=self._filename, err=e))
                self.err_label.show()

    def parsed_macros(self):
        """
        Dictionary containing the key value pair for each macro specified.

        Returns
        --------
        dict
        """
        if self.macros is not None and len(self.macros) > 0:
            return json.loads(self.macros)
        else:
            return {}

    def open_file(self):
        """
        Opens the widget specified in the widget's filename property.

        Returns
        -------
        display : QWidget
        """
        # Expand user (~ or ~user) and environment variables.
        fname = os.path.expanduser(os.path.expandvars(self.filename))
        if os.path.isabs(fname):
            return self.app.open_file(fname, macros=self.parsed_macros())
        else:
            return self.app.open_relative(fname, self,
                                          macros=self.parsed_macros())

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
        self._embedded_widget = new_widget
        self._embedded_widget.setParent(self)
        self.layout.addWidget(self._embedded_widget)
        self.err_label.hide()
        self._embedded_widget.show()
        self._is_connected = True

    def connect(self):
        """
        Establish the connection between the embedded widget widgets and
        the channels associated with it.
        """
        if self._is_connected or self.embedded_widget is None:
            return
        establish_widget_connections(self.embedded_widget)

    def disconnect(self):
        """
        Disconnects the embedded widget widgets from the channels
        associated with it.
        """
        if not self._is_connected or self.embedded_widget is None:
            return
        close_widget_connections(self.embedded_widget)

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
