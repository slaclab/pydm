from ..PyQt.QtGui import QPushButton, QApplication, QFrame, QVBoxLayout, QSizePolicy, QLayout
from ..PyQt.QtCore import pyqtSlot, pyqtProperty, Qt
import json
from .base import PyDMWidget

class PyDMRelatedDisplayButton(QFrame, PyDMWidget):
    __pyqtSignals__ = ("request_open_signal(str)")

    # Constants for determining where to open the display.
    EXISTING_WINDOW = 0;
    NEW_WINDOW = 1;

    def __init__(self, parent=None, init_channel=None, filename=None):
        super().__init__(parent, init_channel=init_channel)
        self.fix_alarm_stylesheet_map()

        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSizeConstraint(QLayout.SetMaximumSize)

        self.push_button = QPushButton(self)
        self.push_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.push_button.mouseReleaseEvent = self.mouseReleaseEvent

        self._layout.addWidget(self.push_button)

        self.setLayout(self._layout)
        self.setFrameShape(QFrame.NoFrame)
        self.setLineWidth(0)

        self._display_filename = filename
        self._macro_string = None
        self._open_in_new_window = False
        self.app = QApplication.instance()

    def fix_alarm_stylesheet_map(self):
        for _, v in self.alarm_style_sheet_map.items():
            for ik, iv in v.items():
                if ik == 0:
                    continue
                if 'color' in iv:
                    iv['background-color'] = iv['color']

    @pyqtProperty(str)
    def text(self):
        return self.push_button.text()

    @text.setter
    def text(self, txt):
        self.push_button.setText(txt)

    @pyqtProperty(str)
    def displayFilename(self):
        """
        The filename to open
        """
        return str(self._display_filename)

    @displayFilename.setter
    def displayFilename(self, value):
        if self._display_filename != value:
            self._display_filename = str(value)
            if self._display_filename is None or len(self._display_filename) < 1:
                self.setEnabled(False)

    @pyqtProperty(str)
    def macros(self):
        """
        The macro substitutions to use when launching the display, in JSON object format.
        """
        if self._macro_string is None:
            return ""
        return self._macro_string

    @macros.setter
    def macros(self, new_macros):
        if len(new_macros) < 1:
            self._macro_string = None
        else:
            self._macro_string = new_macros

    @pyqtProperty(bool)
    def openInNewWindow(self):
        """
        If true, the button will open the display in a new window, rather than in the existing window.
        """
        return self._open_in_new_window

    @openInNewWindow.setter
    def openInNewWindow(self, open_in_new):
        self._open_in_new_window = open_in_new

    def mouseReleaseEvent(self, mouse_event):
        if mouse_event.modifiers() == Qt.ShiftModifier or self._open_in_new_window:
            self.open_display(target=self.NEW_WINDOW)
        else:
            self.open_display()
        super(PyDMRelatedDisplayButton, self).mouseReleaseEvent(mouse_event)

    @pyqtSlot()
    def open_display(self, target=EXISTING_WINDOW):
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
