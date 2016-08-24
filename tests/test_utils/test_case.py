"""
Module that defines useful testing classes for PyDM unit tests.
"""
import unittest
from pydm.application import PyDMApplication
from PyQt4.QtCore import QEventLoop, QTimer
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
        Create a PyDMApplication instance.
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
