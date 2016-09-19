from test_utils.test_case import PluginTest
from test_utils.fake_widgets import ValueWidget as Value
from test_utils.fake_widgets import WaveformWidget as Wavef
from pydm.psp_plugin import PSPPlugin
import psp.Pv as Pv

from pcaspy.driver import Driver, SimpleServer
from pcaspy.tools import ServerThread
import sys
import time
import numpy as np

# We need a trivial subclass of Driver for pcaspy to work
class TestDriver(Driver):
    def __init__(self):
        super(TestDriver, self).__init__()

class TestServer(object):
    """
    Class to create temporary pvs to check in psp_plugin
    """
    def __init__(self, pvbase, **pvdb):
        self.pvbase = pvbase
        self.pvdb = pvdb
        self.kill_server()

    def make_server(self):
        """
        Create a new server and start it
        """
        self.server = SimpleServer()
        self.server.createPV(self.pvbase + ":", self.pvdb)
        self.driver = TestDriver()

    def kill_server(self):
        """
        Remove the existing server (if it exists) and re-initialize
        """
        self.stop_server()
        self.server = None
        self.driver = None

    def start_server(self):
        """
        Allow the current server to begin processing
        """
        if self.server is None:
            self.make_server()
        self.stop_server()
        self.server_thread = ServerThread(self.server)
        self.server_thread.start()

    def stop_server(self):
        """
        Pause server processing
        """
        try:
            self.server_thread.stop()
        except:
            pass

pvdb = dict(
    LONG = dict(type="int"),
    DOUBLE = dict(type="float"),
    STRING = dict(type="string"),
    ENUM = dict(type="enum", enums=["zero", "one", "two", "three"]),
    WAVEFORM = dict(type="char", count=60),
)
# Spoof some PVs until pyca makes info available
pvdb["LONG.EGU"] = dict(type="str", value="mm")
pvdb["LONG.PREC"] = dict(type="int", value=4)
pvdb["LONG.SEVR"] = dict(type="enum", 
    enums=["NO_ALARM", "MINOR", "MAJOR", "INVALID"], value=0)

myServer = TestServer("TEMP:UNITTEST", **pvdb)

class PSPPluginTest(PluginTest):
    """
    Define a comprehensive test setup
    """
    server = myServer

    def setUp(self):
        """
        Start pcaspy and set up testing widgets.
        """
        super(PSPPluginTest, self).setUp()
        self.server.start_server()
        protocol = PSPPlugin.protocol
        self.long_widget     = Value(channel=protocol + "TEMP:UNITTEST:LONG", parent=self.parent)
        self.double_widget   = Value(channel=protocol + "TEMP:UNITTEST:DOUBLE", parent=self.parent)
        self.string_widget   = Value(channel=protocol + "TEMP:UNITTEST:STRING", parent=self.parent)
        self.enum_widget     = Value(channel=protocol + "TEMP:UNITTEST:ENUM", parent=self.parent)
        self.waveform_widget = Wavef(channel=protocol + "TEMP:UNITTEST:WAVEFORM", parent=self.parent)
        self.app.establish_widget_connections(self.parent)
        self.event_loop(0)

    def tearDown(self):
        """
        Stop pcaspy process and clear psp.Pv cache
        """
        Pv.pv_cache = {}
        self.server.stop_server()
        super(PSPPluginTest, self).tearDown()

    def get_widgets(self):
        """
        Return a list of widgets for convenience.

        :rtyp: list of QWidget
        """
        return [self.long_widget, self.double_widget,
                self.string_widget, self.enum_widget, self.waveform_widget]


class PvSetupCase(PSPPluginTest):
    """
    Define a subclass where we set up some test PVs
    """
    def setUp(self):
        super(PvSetupCase, self).setUp()
        self.init_test_pvs()

    def tearDown(self):
        self.reset_pvs()
        super(PvSetupCase, self).tearDown()

    def init_test_pvs(self):
        self.pv_long = Pv.Pv("TEMP:UNITTEST:LONG", initialize=True)
        self.pv_double = Pv.Pv("TEMP:UNITTEST:DOUBLE", initialize=True)
        self.pv_string = Pv.Pv("TEMP:UNITTEST:STRING", initialize=True)
        self.pv_enum = Pv.Pv("TEMP:UNITTEST:ENUM", initialize=True)
        self.pv_enum.set_string_enum(True)
        self.pv_waveform = Pv.Pv("TEMP:UNITTEST:WAVEFORM", initialize=True)
        self.pv_long.wait_ready()
        self.pv_double.wait_ready()
        self.pv_string.wait_ready()
        self.pv_enum.wait_ready()
        self.pv_waveform.wait_ready()

    def reset_pvs(self):
        self.pv_long.put(0)
        self.pv_double.put(0)
        self.pv_string.put("")
        self.pv_enum.put(0)
        self.pv_waveform.put((0,))

class PvTestCase(PvSetupCase):
    """
    Check that our test environment is set up correctly.
    """
    def test_do_nothing(self):
        pass

    def test_pvs_exist(self):
        self.pv_long.get()
        self.pv_double.get()
        self.pv_string.get()
        self.pv_enum.get()
        self.pv_waveform.get()

    def test_reset_pvs_works(self):
        self.pv_long.put(14)
        self.pv_double.put(35)
        self.pv_string.put("text")
        self.pv_enum.put(1)
        ok = []
        ok.append(self.pv_waveform.put((2, 3, 4, 5)))
        ok.append(self.pv_long.wait_for_value(14, timeout=2))
        ok.append(self.pv_double.wait_for_value(35, timeout=2))
        ok.append(self.pv_string.wait_for_value("text", timeout=2))
        ok.append(self.pv_waveform.wait_for_value(tuple([2, 3, 4, 5] +
                  [0]*(self.pv_waveform.count-4))))
        self.assertTrue(all(ok))
        self.reset_pvs()
        ok = []
        ok.append(self.pv_long.wait_for_value(0, timeout=2))
        ok.append(self.pv_double.wait_for_value(0, timeout=2))
        ok.append(self.pv_string.wait_for_value("", timeout=2))
        ok.append(self.pv_enum.wait_for_value("zero", timeout=2))
        ok.append(self.pv_waveform.wait_for_value(tuple([0 for x in
                  range(self.pv_waveform.count)]), timeout=2))
        self.assertTrue(all(ok))

    def test_pvs_work(self):
        long = 24
        double = 63.2
        string = "test_string"
        waveform = tuple([i for i in range(self.pv_waveform.count)])
        enum_int = 2
        enum_txt = "two"
        self.pv_long.put(long)
        self.pv_double.put(double)
        self.pv_string.put(string)
        self.pv_enum.put(enum_int)
        self.pv_waveform.put(waveform)
        ok = []
        ok.append(self.pv_long.wait_for_value(long, timeout=2))
        ok.append(self.pv_double.wait_for_value(double, timeout=2))
        ok.append(self.pv_string.wait_for_value(string, timeout=2))
        ok.append(self.pv_enum.wait_for_value(enum_txt, timeout=2))
        ok.append(self.pv_waveform.wait_for_value(waveform, timeout=2))
        self.assertTrue(all(ok))

    def test_waveform_is_waveform(self):
        self.assertTrue(self.pv_waveform.count > 1)

class BasicTestCase(PvSetupCase):
    """
    Make sure we can get/set pvs from widgets in isolation.
    """
    def test_get_long(self):
        long = 55
        self.pv_long.put(long)
        self.signal_wait(self.long_widget.value_updated_signal, timeout=2)
        self.assertEqual(self.long_widget.value, long)

    def test_put_long(self):
        long = 23
        self.long_widget.send_value(long)
        self.event_loop(0)
        ok = self.pv_long.wait_for_value(long, timeout=2)
        self.assertTrue(ok)

    def test_get_double(self):
        double = 24.1
        self.pv_double.put(double)
        self.signal_wait(self.double_widget.value_updated_signal, timeout=2)
        self.assertEqual(self.double_widget.value, double)

    def test_put_double(self):
        double = 253.4
        self.double_widget.send_value(double)
        self.event_loop(0)
        ok = self.pv_double.wait_for_value(double, timeout=2)
        self.assertTrue(ok)

    def test_get_string(self):
        string = "applesauce"
        self.pv_string.put(string)
        self.signal_wait(self.string_widget.value_updated_signal, timeout=2)
        self.assertEqual(self.string_widget.value, string)

    def test_put_string(self):
        string = "potato"
        self.string_widget.send_value(string)
        self.event_loop(0)
        ok = self.pv_string.wait_for_value(string, timeout=2)
        self.assertTrue(ok)

    def test_get_enum(self):
        enum = 1
        self.pv_enum.put(enum)
        self.signal_wait(self.enum_widget.value_updated_signal, timeout=2)
        self.assertEqual(self.enum_widget.value, "one")

    def test_put_enum(self):
        enum = 2
        self.enum_widget.send_value(enum)
        self.event_loop(0)
        ok = self.pv_enum.wait_for_value("two", timeout=2)
        self.assertTrue(ok)

    def test_get_waveform(self):
        waveform = tuple([x for x in range(self.pv_waveform.count)])
        self.pv_waveform.put(waveform)
        self.signal_wait(self.waveform_widget.waveform_updated_signal,
            timeout=2)
        self.assertEqual(tuple(self.waveform_widget.value), waveform)

    def test_put_waveform(self):
        waveform = np.asarray([x+1 for x in range(self.pv_waveform.count)])
        self.waveform_widget.send_waveform(np.asarray(waveform))
        self.event_loop(0)
        ok = self.pv_waveform.wait_for_value(waveform, timeout=2)
        self.assertTrue(ok, "pv_waveform value was {}".format(self.pv_waveform.value))


class AuxTestCase(PSPPluginTest):
    """
    Make sure we are updated on connection state, sevr, etc.
    """
    def test_conn(self):
        print "\n----------------------------------------------------------"
        print   "This will spout out some EPICS error strings but it is ok."
        print   "----------------------------------------------------------"
        try:
            if not self.long_widget.conn:
                self.signal_wait(self.long_widget.conn_updated_signal,
                    timeout=2)
            self.assertTrue(self.long_widget.conn)
            self.server.kill_server()
            self.server.start_server()
            if self.long_widget.conn:
                self.signal_wait(self.long_widget.conn_updated_signal,
                    timeout=2)
            self.assertFalse(self.long_widget.conn)
            if not self.long_widget.conn:
                self.signal_wait(self.long_widget.conn_updated_signal,
                    timeout=10)
            self.assertTrue(self.long_widget.conn)
        except:
            if self.server is None:
                self.server.start_server()
                if not self.long_widget.conn:
                    self.signal_wait(self.long_widget.conn_updated_signal,
                        timeout=10)
            raise
        time.sleep(10) # Extra sleep to make sure things reinit correctly

    def test_sevr(self):
        # Currently implemented based on .SEVR field. Will change if we
        # update pyca to give us the alarm severity directly.
        sevr = Pv.Pv("TEMP:UNITTEST:LONG.SEVR", initialize=True)
        sevr.wait_ready()
        sevr.put(0)
        self.signal_wait(self.long_widget.sevr_updated_signal, timeout=2)
        self.assertEqual(self.long_widget.sevr, 0)
        sevr.put(1)
        self.signal_wait(self.long_widget.sevr_updated_signal, timeout=2)
        self.assertEqual(self.long_widget.sevr, 1)
        sevr.put(2)
        self.signal_wait(self.long_widget.sevr_updated_signal, timeout=2)
        self.assertEqual(self.long_widget.sevr, 2)
        sevr.put(3)
        self.signal_wait(self.long_widget.sevr_updated_signal, timeout=2)
        self.assertEqual(self.long_widget.sevr, 3)
        sevr.put(0)

    def test_rwacc(self):
        # Not sure how to create a read-only pv to test this on...
        if not self.long_widget.rwacc:
            self.signal_wait(self.long_widget.rwacc_updated_signal, timeout=2)
        self.assertTrue(self.long_widget.rwacc)

    def test_enums(self):
        enums = ("zero", "one", "two", "three")
        if self.enum_widget.enums != enums:
            self.signal_wait(self.enum_widget.enums_updated_signal, timeout=2)
        self.assertEqual(self.enum_widget.enums, enums)

    def test_units(self):
        # Currently implemented based on .EGU field. Will change if we
        # update pyca to give us the alarm severity directly.
        egu = Pv.Pv("TEMP:UNITTEST:LONG.EGU", initialize=True)
        egu.wait_ready()
        egu.put("miles")
        self.signal_wait(self.long_widget.units_updated_signal, timeout=2)
        self.assertEqual(self.long_widget.units, "miles")
        egu.put("mm")
        self.signal_wait(self.long_widget.units_updated_signal, timeout=2)
        self.assertEqual(self.long_widget.units, "mm")

    def test_prec(self):
        # Currently implemented based on .PREC field. Will change if we
        # update pyca to give us the alarm severity directly.
        prec = Pv.Pv("TEMP:UNITTEST:LONG.PREC", initialize=True)
        prec.wait_ready()
        prec.put(0)
        self.signal_wait(self.long_widget.prec_updated_signal, timeout=2)
        self.assertEqual(self.long_widget.prec, 0)
        prec.put(4)
        self.signal_wait(self.long_widget.prec_updated_signal, timeout=2)
        self.assertEqual(self.long_widget.prec, 4)

