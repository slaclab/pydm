# Unit Tests for the Channel widget class
import pytest

from pydm.widgets.channel import PyDMChannel, clear_channel_address
from pydm import data_plugins
from pydm.data_plugins import plugin_for_address
from pydm.data_store import DataStore, DataKeys, DEFAULT_INTROSPECTION


class A():
    pass


def test_clear_channel_address():
    assert clear_channel_address(None) is None
    assert clear_channel_address(" tst://foo ") == "tst://foo"


def test_construct(qapp):
    """
    Test the construct of the widget.

    Expectations:
    1. The widget is created with all the default values for its properties
    2. When created for a specific widget type, the Channel widget contains the default values, i.e. the appropriate
        slots, for that specific widget type
    3. Channel widgets can be compared for equality and inequality using the '==' and '!=' operators.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    def test_callback(data, introspection, *args, **kwargs):
        pass

    ch = PyDMChannel()

    assert ch._config == {}
    assert ch.address is None
    assert len(ch._monitors) == 0
    assert ch._use_introspection is True
    assert ch._introspection == {}
    assert ch.get_introspection() is None

    ch.subscribe(test_callback)
    assert test_callback in ch._monitors
    ch.unsubscribe(test_callback)
    assert test_callback not in ch._monitors
    ch.subscribe(test_callback)
    assert len(ch._monitors) > 0
    ch.clear_subscriptions()
    assert len(ch._monitors) == 0


def test_channel_data_flow(qtbot, test_plugin):
    class CallbackHandler:
        def __init__(self):
            self.data_payload = None
            self.intro_payload = None

        def clear(self):
            self.data_payload = None
            self.intro_payload = None

        def cb(self, data, introspection, *args, **kwargs):
            self.data_payload = data
            self.intro_payload = introspection

    handler = CallbackHandler()
    ch = PyDMChannel('tst://foo', callback=handler.cb)
    # Ensure that data is clean
    assert handler.data_payload is None
    assert handler.intro_payload is None

    # Connect the channel with the test data plugin
    ch.connect()
    assert len(test_plugin.connections) == 1
    connections = test_plugin.connections
    tst_conn = connections['foo']
    assert tst_conn.payload_received is None

    #
    blocker = qtbot.waitSignal(tst_conn.notify)
    tst_conn.send_to_channel()
    blocker.wait()
    ch.notified()

    assert handler.intro_payload == DEFAULT_INTROSPECTION
    assert handler.data_payload == {}

    blocker = qtbot.waitSignal(tst_conn.notify)
    intro = {'FOO': 'foo', 'BAR': 'bar'}
    data = {'DATA1': 'data1', 'DATA2': 'data2'}
    tst_conn.write_introspection(intro)
    tst_conn.write_data(data)
    blocker.wait()
    ch.notified()

    assert handler.intro_payload == intro
    assert handler.data_payload == data

    # Force the channel to be busy
    ch._busy = True
    blocker = qtbot.waitSignal(tst_conn.notify)
    ignored_intro = {'FOO2': 'foo', 'BAR2': 'bar'}
    ignored_data = {'DATA3': 'data3', 'DATA4': 'data4'}
    tst_conn.write_introspection(ignored_intro)
    tst_conn.write_data(ignored_data)
    blocker.wait()
    ch.notified()

    assert handler.intro_payload == intro
    assert handler.data_payload == data


def test_pydm_connection_and_cleanup(qapp, test_plugin):
    # Plugin, Channel and Registry
    chan = PyDMChannel('tst://Tst:this')
    plugin = plugin_for_address(chan.address)
    plugin_no = len(plugin.connections)
    # Make a connection
    chan.connect()
    assert chan.connected()
    assert len(plugin.connections) == plugin_no + 1
    # Remove connections
    chan.disconnect()
    assert len(plugin.connections) == plugin_no
    chan = PyDMChannel()
    chan.connect()
    chan.disconnect()


@pytest.mark.parametrize(
    "ch, ch_expected", [
        ("ca://MTEST:Float", "ca://MTEST:Float"),
        (" foo://bar", "foo://bar"),
        (" foo://bar ", "foo://bar"),
        ("foo://bar ", "foo://bar"),
        ("\nfoo://bar", "foo://bar"),
        ("\tfoo://bar", "foo://bar"),
        ("", ""),
        (None, None),
    ])
def test_channel_address(qtbot, ch, ch_expected):
    channel = PyDMChannel()
    channel.address = ch
    assert channel.address == ch_expected
