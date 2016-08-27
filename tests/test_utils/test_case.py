"""
Module that defines useful testing classes for PyDM unit tests.
"""
import unittest
import Queue
from pydm.application import PyDMApplication
from PyQt4.QtCore import QEventLoop, QTimer, QObject, pyqtSignal, pyqtSlot
from PyQt4.QtGui import QWidget

class PyDMTest(unittest.TestCase):
    """
    Parent class for pydm TestCase classes.
    """
    # If I don't do it this way, we'd have to import QTimer in every test file.
    # This probably has something to do with the way PyQt4 is implemented.
    QTimer = QTimer

    def setUp(self):
        """
        Create a PyDMApplication instance and set up test slots.
        """
        self.app = PyDMApplication([])

    def tearDown(self):
        """
        Clean up our PyDMApplication instance. In subclasses, call super LAST
        (reverse the normal order) for clean tearDown.
        """
        del self.app

    def event_loop(self, t):
        """
        Pause the current thread and run the event loop for t seconds. This
        will cause things like QTimers to process and signals to be recieved.

        If t=0, we'll just process queued signals and skip the timers.

        :param t: time in seconds to run the loop
        :type t:  float or int
        """
        if t != 0:
            timer = self.QTimer()
            timer.start(t * 1000.0)
            loop = QEventLoop()
            timer.timeout.connect(loop.quit)
            loop.exec_()
        self.app.processEvents()

    def signal_wait(self, signal, timeout):
        """
        Halt the current thread until signal emits something.
        Start a QEventLoop for this duration.
        Stop waiting after timeout seconds.
        If signal sent a value, return it, else return None.
        """
        # Make the objects we need
        loop = QEventLoop()
        queue = QueueSlots()
        timer = self.QTimer()
        timer.start(timeout * 1000.0)

        # Connect signals/slots so that whatever signal sends ends up in the
        # queue, with a timeout provided by QTimer. We can stop as soon as we
        # get any value.
        signal.connect(queue.put_to_queue)
        timer.timeout.connect(loop.quit)
        queue.got_value.connect(loop.quit)

        # Clear current events and go until loop.quit is called
        self.app.processEvents()
        loop.exec_()

        # Disconnect signals to defunct quit slot
        queue.got_value.disconnect(loop.quit)
        timer.timeout.disconnect(loop.quit)

        # One more process step just in case (this actually matters I think)
        self.app.processEvents()
        signal.disconnect(queue.put_to_queue)

        # Get value if we have one (otherwise, this is None)
        value = queue.get()
        return value

class QueueSlots(QObject):
    """
    Dummy object that contains a slot that puts signal results to a queue.
    Exists for the implementation of PyDMTest.signal_wait.
    """
    __pyqtSignals__ = ("got_value()",)
    got_value = pyqtSignal()

    def __init__(self, parent=None):
        """
        Set up QObject and create internal queue.
        """
        super(QueueSlots, self).__init__(parent=parent)
        self.queue = Queue.Queue()

    def get(self, timeout=None):
        """
        Retrieve queue value or None. Waits for timeout seconds.

        :param timeout: get timeout in seconds
        :type timeout:  float or int
        :rtyp: object or None
        """
        try:
            return self.queue.get(timeout)
        except Queue.Empty:
            return

    @pyqtSlot()
    @pyqtSlot(object)
    def put_to_queue(self, value=None):
        """
        Put incoming value into the queue and signal that we recieved data.

        :param value: Incoming value
        :type value:  object or None
        """
        self.queue.put(value)
        self.got_value.emit()


class PluginTest(PyDMTest):
    """
    Parent class for testing plugins.
    """
    def setUp(self):
        """
        Create a parent QWidget to organize the cleanup of test widgets.
        """
        super(PluginTest, self).setUp()
        self.parent = QWidget()

    def tearDown(self):
        """
        Clean up our parent widget and all of its children. In subclasses,
        call super LAST (reverse the normal order) for clean tearDown.
        """
        del self.parent
        super(PluginTest, self).tearDown()
