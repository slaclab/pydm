from test_utils.test_case import PluginTest
from test_utils.fake_widgets import BasicValueWidget as Value
from test_utils.fake_widgets import BasicWaveformWidget as Wavef
from pydm.local_plugin import LocalPlugin

import time
import math
import numpy as np
from pydm.PyQt.QtCore import QObject, pyqtSignal

"""
Missing Tests:
- empty string arguments
- behavior with bad function calls
- handle odd np types
"""

class Position(object):
    """
    Arbitrary simple class to test with
    """
    def __init__(self, name="point", x=0, y=0, z=0):
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.data = np.asarray((0, 0, 0, 0, 0))
        self.n_set = 0
        self.n_mult = 0

    @property
    def r(self):
        return math.sqrt(sum([n*n for n in (self.x, self.y, self.z)]))

    def r_times_n(self, n):
        self.x, self.y, self.z = map(lambda x: x*n, (self.x, self.y, self.z))
        self.n_mult += 1
        return n 

    def sum(self):
        return sum((self.x, self.y, self.z))

    def set(self, x=None, y=None, z=None):
        if x is not None: self.x = x
        if y is not None: self.y = y
        if z is not None: self.z = z
        self.n_set += 1
        return self.get()

    def get(self):
        return np.asarray((self.x, self.y, self.z))

    def increase_x(self, n):
        self.x = self.x + n


class LocalPluginTest(PluginTest):
    """
    Define a comprehensive test setup
    """
    def setUp(self):
        """
        Create a testing object. Connect various widget types to various
        fields of the testing object using LocalPlugin. Process signals before
        loading test case.
        """
        super(LocalPluginTest, self).setUp()
        self.obj = Position()
        self.name_widget  = Value(channel="obj://name?t=0", parent=self.parent)
        self.x_widget     = Value(channel="obj://x", parent=self.parent)
        self.x2_widget    = Value(channel="obj://x", parent=self.parent)
        self.y_widget     = Value(channel="obj://y", parent=self.parent)
        self.z_widget     = Value(channel="obj://z", parent=self.parent)
        self.r_widget     = Value(channel="obj://r", parent=self.parent)
        self.rn_widget    = Value(channel="obj://r_times_n(1)?t=0", parent=self.parent)
        self.sum_widget   = Value(channel="obj://sum()", parent=self.parent)
        self.data_widget  = Wavef(channel="obj://data?t=0", parent=self.parent)
        self.set_widget   = Wavef(channel="obj://set()?t=0", parent=self.parent)
        self.get_widget   = Wavef(channel="obj://get()", parent=self.parent)
        self.stale_widget = Value(channel="obj://x?t=0", parent=self.parent)
        self.plugin = LocalPlugin("obj", self.obj, widgets=self.get_widgets(),
            refresh=1)
        self.event_loop(0)

    def tearDown(self):
        """
        Clean up the LocalPlugin and corresponding object.
        """
        del self.plugin
        del self.obj
        super(LocalPluginTest, self).tearDown()

    def widget_names(self):
        """
        Return a tuple of widget names for convenience.

        :rtyp: tuple of str
        """
        return ("name", "x", "x2", "y", "z", "r", "rn", "sum", "data", "set",
            "get", "stale")

    def get_widgets(self):
        """
        Return a list of widgets for convenience.

        :rtyp: list of QWidget
        """
        return [getattr(self, "{}_widget".format(n))
            for n in self.widget_names()]


class BasicTestCase(LocalPluginTest):
    def test_connections_exist(self):
        """
        Check that we have a Connection for each widget
        """
        for widget in self.get_widgets():
            address = self.plugin.get_address(widget.channels()[0])
            self.assertIsNotNone(self.plugin.connections.get(address),
                msg="No Connection for {}".format(address))

    def test_initialized(self):
        """
        Check that every widget has a value.
        """
        for widget in self.get_widgets():
            self.assertIsNotNone(widget.value,
                msg="{} value was None".format(widget.channel))

    def test_update(self):
        """
        Make sure the timed update fields update within 2 seconds,
        and again later.
        """
        self.obj.x = 3
        self.obj.y = 4
        self.obj.z = 0
        self.event_loop(1)
        msg = "1s timed update field {} did not update within 1s"
        self.assertEqual(self.x_widget.value, 3, msg=msg.format("x"))
        self.assertEqual(self.x2_widget.value, 3, msg=msg.format("x2"))
        self.assertEqual(self.y_widget.value, 4, msg=msg.format("y"))
        self.assertEqual(self.z_widget.value, 0, msg=msg.format("z"))
        self.assertEqual(self.r_widget.value, 5, msg=msg.format("r"))
        self.assertEqual(self.sum_widget.value, 7, msg=msg.format("sum"))
        self.assertEqual(tuple(self.get_widget.value),
            tuple(np.asarray((3, 4, 0))), msg=msg.format("get"))
        self.obj.x = 10
        self.event_loop(1)
        self.assertEqual(self.x_widget.value, 10, msg="fields stop updating")


class PutTestCase(LocalPluginTest):
    def test_field_puts(self):
        """
        Check that we can put to the fields
        """
        self.x_widget.send_value(1)
        self.y_widget.send_value(2)
        self.z_widget.send_value(3.7)
        self.name_widget.send_value("new_name")
        self.event_loop(0)
        msg = "cannot put to value field {0}: desired {1} but was {2}"
        self.assertEqual(self.obj.x, 1, msg=msg.format("x", 1, self.obj.x))
        self.assertEqual(self.obj.y, 2, msg=msg.format("y", 2, self.obj.y))
        self.assertEqual(self.obj.z, 3.7, msg=msg.format("z", 3.7, self.obj.z))
        self.assertEqual(self.obj.name, "new_name",
            msg=msg.format("name", "new_name", self.obj.name))

    def test_waveform_put(self):
        """
        Check that we can put to waveform fields
        """
        array = np.asarray((1, 2, 3, 4))
        self.data_widget.send_waveform(array)
        self.event_loop(0)
        self.assertEqual(tuple(self.obj.data), tuple(array),
            msg="cannot put to waveform")

    def test_same_connection(self):
        """
        Check that putting to one channel updates an identical channel
        """
        self.x_widget.send_value(3)
        self.event_loop(0.01)
        self.assertEqual(self.x2_widget.value, 3,
            msg="widgets with same connection do not share values" +
                ", expected {0} but was {1}".format(2, self.x2_widget.value))

    def test_function(self):
        """
        Check that we can call the r times n function with a put
        """
        self.obj.x = 1
        self.obj.y = 2
        self.obj.z = 3
        self.rn_widget.send_value(4)
        self.event_loop(0)
        msg = "function had wrong result: was {0}, expected {1}"
        self.assertEqual(self.obj.x, 4, msg=msg.format(self.obj.x, 4))
        self.assertEqual(self.obj.y, 8, msg=msg.format(self.obj.y, 8))
        self.assertEqual(self.obj.z, 12, msg=msg.format(self.obj.z, 12))

    def test_waveform_function(self):
        """
        Check that we can put to the waveform set function
        """
        array = np.asarray((5, 5, 6))
        self.set_widget.send_waveform(array)
        self.event_loop(0)
        result = self.obj.get()
        self.assertEqual(tuple(result), tuple(array),
            msg="waveform function has wrong result: was {0}, expected {1}".format(
            result, array))


class SignalHolder(QObject):
    """
    Dummy QObject to let us use pyqtSignal
    """
    value_sig = pyqtSignal([int], [float], [str])
    empty_sig = pyqtSignal()

class SignalTestCase(LocalPluginTest):
    def test_signal_update(self):
        """
        Check that we can update t=0 widgets intelligently with signals
        """
        sig = SignalHolder()
        self.plugin.connect_to_update("x?t=0", sig.empty_sig)
        self.stale_widget.send_value(4)
        self.event_loop(0.01)
        self.assertEqual(self.stale_widget.value, 4,
            msg="t=0 widgets do not update on puts")
        self.obj.x = 10
        self.event_loop(2)
        self.assertEqual(self.stale_widget.value, 4,
            msg="t=0 widgets update within 2s")
        sig.empty_sig.emit()
        self.event_loop(0.01)
        self.assertEqual(self.stale_widget.value, 10,
            msg="t=0 widgets do not update on signal")
