import math
import logging
from qtpy.QtCore import QTimer, Property, QEvent
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QLabel, QMessageBox, QApplication

from .base import PyDMPrimitiveWidget, get_icon_file
from ..utilities import is_qt_designer

logger = logging.getLogger(__name__)


FAST_TIMER_INTERVAL = 1000  # 1 second
SLOW_TIMER_INTERVAL = 10000  # 10 seconds


class PyDMTerminator(QLabel, PyDMPrimitiveWidget):
    """
    A watchdog widget to close a window after X seconds of inactivity.
    """
    designer_icon = QIcon(get_icon_file("terminator.png"))

    def __init__(self, parent=None, timeout=60, *args, **kwargs):
        super(PyDMTerminator, self).__init__(parent=parent, *args, **kwargs)
        self.setText("")
        self._hook_setup = False
        self._timeout = 60
        self._time_rem_ms = 0

        self._timer = QTimer()
        self._timer.timeout.connect(self.handle_timeout)
        self._timer.setSingleShot(True)

        self._window = None

        if timeout and timeout > 0:
            self.timeout = timeout
        else:
            self._reset()

        self._setup_activity_hook()
        self._update_label()

    def _find_window(self):
        """
        Finds the first window available starting from this widget's parent

        Returns
        -------
        QWidget
        """
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

        # We must install the event filter in the application otherwise
        # it won't stop when typing or moving over other widgets or even
        # the PyDM main window if in use.
        QApplication.instance().installEventFilter(self)
        self._hook_setup = True

    def eventFilter(self, obj, ev):
        if ev.type() in (QEvent.MouseMove, QEvent.KeyPress, QEvent.KeyRelease):
            self.reset()
        return super(PyDMTerminator, self).eventFilter(obj, ev)

    def reset(self):
        if self._time_rem_ms != self._timeout * 1000:
            self._time_rem_ms = self._timeout * 1000
            self._update_label()
        self.stop()
        self.start()

    def start(self):
        if is_qt_designer():
            return
        interval = SLOW_TIMER_INTERVAL
        if self._time_rem_ms < 60*1000:
            interval = FAST_TIMER_INTERVAL
        self._timer.setInterval(interval)

        if not self._timer.isActive():
            self._timer.start()

    def stop(self):
        if self._timer.isActive():
            self._timer.stop()

    def _get_time_text(self, value):
        """
        Converts value in seconds into a text for days, hours, minutes and
        seconds remaining.

        Parameters
        ----------
        value : int
            The value in seconds to be converted

        Returns
        -------
        str
        """
        def time_msg(unit, val):
            return "{} {}{}".format(val, unit, "s" if val > 1 else "")

        units = ["day", "hour", "minute", "second"]
        scale = [86400, 3600, 60, 1]

        values = [0, 0, 0, 0]
        rem = value
        for idx, sc in enumerate(scale):
            val_scaled, rem = int(rem//sc), rem % sc
            if val_scaled >= 1:
                val_scaled = math.ceil(val_scaled+(rem/sc))
                values[idx] = val_scaled
                break
            values[idx] = val_scaled

        time_items = []
        for idx, un in enumerate(units):
            v = values[idx]
            if v > 0:
                time_items.append(time_msg(un, v))

        return ", ".join(time_items)

    def _update_label(self):
        """Updates the label text with the remaining time."""
        rem_time_s = self._time_rem_ms/1000.0
        text = self._get_time_text(rem_time_s)
        self.setText("This screen will close in {}.".format(text))

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
            self.reset()

    def handle_timeout(self):
        """
        Handles the timeout event for the timer.
        Decreases the time remaining counter until 0 and when it is time,
        cleans up the event filter and closes the window.
        """
        if is_qt_designer():
            return
        # Decrease remaining time
        self._time_rem_ms -= self._timer.interval()
        # Update screen label with new remaining time
        self._update_label()

        if self._time_rem_ms > 0:
            self.start()
            return
        QApplication.instance().removeEventFilter(self)

        if self._window:
            logger.debug('Time to close the window')
            self._window.close()
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText(
                "Your window was closed due to inactivity for {}.".format(
                    self._get_time_text(self.timeout)
                )
            )
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setDefaultButton(QMessageBox.Ok)
            msg.exec_()
