import logging
from qtpy.QtCore import QTimer, Property, QEvent
from qtpy.QtWidgets import QWidget, QMessageBox

from .base import PyDMPrimitiveWidget
from ..utilities import is_qt_designer

logger = logging.getLogger(__name__)


class PyDMTerminator(QWidget, PyDMPrimitiveWidget):
    """
    A watchdog widget to close a window after X seconds of inactivity.
    """
    def __init__(self, parent=None, timeout=60, *args, **kwargs):
        super(PyDMTerminator, self).__init__(parent=parent, *args, **kwargs)
        self._hook_setup = False

        self._timer = QTimer()
        self._timer.timeout.connect(self.handle_timeout)
        self._timer.setSingleShot(True)
        self._timeout = 60
        self._window = None

        if timeout and timeout > 0:
            self.timeout = timeout

        self._setup_activity_hook()

    def _find_window(self):
        # check buffer
        if self._window:
            return self._window
        # go fish
        w = self.parent()
        while w is not None:
            if w.isWindow():
                return w
            w = w.parent()

        # we couldn't find it
        return None

    def _setup_activity_hook(self):
        if is_qt_designer():
            return
        logger.debug('Setup Hook')
        if self._hook_setup:
            logger.debug('Setup Hook Already there')
            return
        self._window = self._find_window()
        logger.debug('Install event filter at window')
        self._window.setMouseTracking(True)
        self._window.installEventFilter(self)
        self._hook_setup = True

    def eventFilter(self, obj, ev):
        if ev.type() in (QEvent.MouseMove, QEvent.KeyPress):
            self.stop()
            self.start()

        return super(PyDMTerminator, self).eventFilter(obj, ev)

    def start(self):
        if not self._timer.isActive():
            self._timer.start()

    def stop(self):
        if self._timer.isActive():
            self._timer.stop()

    @Property(int)
    def timeout(self):
        """
        Timeout in seconds.

        Returns
        -------
        int
        """
        return self._timeout

    @timeout.setter
    def timeout(self, seconds):
        self.stop()
        if seconds and seconds > 0:
            self._timeout = seconds
            self._timer.setInterval(seconds * 1000)
            self.start()

    def handle_timeout(self):
        if is_qt_designer():
            return
        logger.debug('Timeout time to the terminator')
        if self._window:
            logger.debug('Time to close the window')
            self._window.close()
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText(
                "Your window was closed due to inactivity for {} seconds".format(
                    self.timeout
                )
            )
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setDefaultButton(QMessageBox.Ok)
            ret = msg.exec_()
