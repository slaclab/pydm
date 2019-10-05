import logging
from qtpy.QtCore import QTimer, Property, QEvent
from qtpy.QtWidgets import QWidget

from .base import PyDMPrimitiveWidget
from ..utilities import is_qt_designer

logger = logging.getLogger(__name__)


class PyDMTerminator(QWidget, PyDMPrimitiveWidget):

    def __init__(self, parent=None, timeout=60, *args, **kwargs):
        super(PyDMTerminator, self).__init__(parent=parent, *args, **kwargs)
        logger.warning('Creating')
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
        logger.warning('Find Window')
        if self._window:
            logger.warning('Window already there')
            return self._window
        # go fish
        logger.warning('Lets go fish')
        w = self.parent()
        while w is not None:
            if w.isWindow():
                logger.warning('Window found')
                return w
            w = w.parent()

        logger.warning('Could not find Window')
        # we couldn't find it
        return None

    def _setup_activity_hook(self):
        logger.warning('Setup Hook')
        if self._hook_setup:
            logger.warning('Setup Hook Already there')
            return
        self._window = self._find_window()
        logger.warning('Install event filter at window')
        self._window.setMouseTracking(True)
        self._window.installEventFilter(self)
        self._hook_setup = True

    def eventFilter(self, obj, ev):
        print('Got Event...', ev.type())
        if ev.type() in (QEvent.MouseMove, QEvent.KeyPress):
            print('Got Event, reset timer...')
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
        logger.warning('Timeout time to the terminator')
        if is_qt_designer():
            return
        if self._window:
            logger.warning('Time to close the window')
            # self._window.close()
        else:
            logger.warning('No Window')