import functools

import numpy as np
import pytest

tango = pytest.importorskip("tango")

from tango.server import Device, attribute  # noqa: E402
from tango.test_context import DeviceTestContext  # noqa: E402

from pydm.data_plugins import tango_plugin  # noqa: E402
from pydm.data_plugins.tango_plugin import TangoPlugin, parse_precision, split_address  # noqa: E402
from pydm.widgets.channel import PyDMChannel  # noqa: E402

SLOTS = (
    "connection",
    "value",
    "severity",
    "write_access",
    "enum_strings",
    "unit",
    "prec",
    "upper_ctrl_limit",
    "lower_ctrl_limit",
    "upper_alarm_limit",
    "lower_alarm_limit",
    "upper_warning_limit",
    "lower_warning_limit",
    "timestamp",
)


class TangoTestDevice(Device):
    """Small device covering the attribute flavours handled by the plugin"""

    def init_device(self):
        super().init_device()
        self._position = 1.5
        self._mode = 1
        self.set_state(tango.DevState.ON)
        self.set_change_event("position", True, False)

    @attribute(
        dtype=float,
        access=tango.AttrWriteType.READ_WRITE,
        unit="mm",
        format="%6.3f",
        min_value=-10,
        max_value=10,
        min_alarm=-8,
        max_alarm=8,
        min_warning=-5,
        max_warning=5,
    )
    def position(self):
        return self._position

    @position.write
    def position(self, value):
        self._position = value
        self.push_change_event("position", value)

    # No change events configured: the plugin has to poll this one
    @attribute(dtype=int)
    def counter(self):
        return 42

    @attribute(dtype=tango.DevEnum, enum_labels=["Off", "Slow", "Fast"], access=tango.AttrWriteType.READ_WRITE)
    def mode(self):
        return self._mode

    @mode.write
    def mode(self, value):
        self._mode = value

    @attribute(dtype=bool)
    def flag(self):
        return True

    @attribute(dtype=(float,), max_dim_x=5)
    def spectrum(self):
        return [1.0, 2.0, 3.0]

    @attribute(dtype=str)
    def text(self):
        return "hello"

    @attribute(dtype=tango.DevUChar)
    def uchar(self):
        return 200

    # Read value differs from the write value, like a real setpoint / readback pair
    @attribute(dtype=float, access=tango.AttrWriteType.READ_WRITE)
    def doubled(self):
        return 2 * self._doubled

    @doubled.write
    def doubled(self, value):
        self._doubled = value

    _doubled = 1.0


@pytest.fixture(scope="module")
def device_access():
    context = DeviceTestContext(TangoTestDevice, process=True)
    with context:
        # e.g. tango://127.0.0.1:12345/test/nodb/tangotestdevice#dbase=no
        yield context.get_device_access()


@pytest.fixture
def plugin(monkeypatch):
    monkeypatch.setattr(tango_plugin, "POLL_PERIOD", 100)
    return TangoPlugin()


class Recorder:
    """Collects the latest value received on every slot of a PyDMChannel"""

    def __init__(self, address):
        self.received = {}
        kwargs = {name + "_slot": functools.partial(self.received.__setitem__, name) for name in SLOTS}
        self.channel = PyDMChannel(address=address, **kwargs)


def connect(qtbot, plugin, address, expected=("connection", "value")):
    recorder = Recorder(address)
    plugin.add_connection(recorder.channel)
    qtbot.waitUntil(lambda: all(name in recorder.received for name in expected), timeout=10000)
    qtbot.waitUntil(lambda: recorder.received["connection"], timeout=10000)
    return recorder


def address(device_access, attribute_name):
    device, _, fragment = device_access.partition("#")
    return "{}/{}#{}".format(device, attribute_name, fragment)


@pytest.mark.parametrize(
    "address, expected",
    [
        ("sys/tg_test/1/double_scalar", ("sys/tg_test/1", "double_scalar")),
        ("host:10000/sys/tg_test/1/double_scalar", ("tango://host:10000/sys/tg_test/1", "double_scalar")),
        ("host:10000/a/b/c/attr#dbase=no", ("tango://host:10000/a/b/c#dbase=no", "attr")),
        ("motor1/position", ("motor1", "position")),
    ],
)
def test_split_address(address, expected):
    assert split_address(address) == expected


def test_split_address_invalid():
    with pytest.raises(ValueError):
        split_address("no_attribute")


@pytest.mark.parametrize("fmt, expected", [("%6.2f", 2), ("%.4e", 4), ("%d", None), ("", None)])
def test_parse_precision(fmt, expected):
    assert parse_precision(fmt) == expected


def test_connection_id_uses_full_address(plugin):
    channel = PyDMChannel(address="tango://sys/tg_test/1/double_scalar")
    assert plugin.get_address(channel) == "sys/tg_test/1/double_scalar"
    assert plugin.get_connection_id(channel) == "sys/tg_test/1/double_scalar"


def test_change_events_and_metadata(qtbot, plugin, device_access):
    expected = ("connection", "value", "unit", "prec", "upper_warning_limit", "write_access")
    recorder = connect(qtbot, plugin, address(device_access, "position"), expected)
    received = recorder.received
    assert received["value"] == 1.5
    assert received["unit"] == "mm"
    assert received["prec"] == 3
    assert received["upper_ctrl_limit"] == 10
    assert received["lower_ctrl_limit"] == -10
    assert received["upper_alarm_limit"] == 8
    assert received["lower_alarm_limit"] == -8
    assert received["upper_warning_limit"] == 5
    assert received["lower_warning_limit"] == -5
    assert received["severity"] == 0
    assert received["write_access"] is True
    assert isinstance(received["timestamp"], float)
    connection = plugin.connections[plugin.get_connection_id(recorder.channel)]
    assert not connection._polling

    # Writing pushes a change event back to us, alarm limits are evaluated by the device
    connection.put_value(6.0)
    qtbot.waitUntil(lambda: received["value"] == 6.0, timeout=5000)
    qtbot.waitUntil(lambda: received["severity"] == 1, timeout=5000)
    connection.put_value(1.5)
    qtbot.waitUntil(lambda: received["value"] == 1.5, timeout=5000)

    plugin.remove_connection(recorder.channel)


def test_polling_fallback(qtbot, plugin, device_access):
    recorder = connect(qtbot, plugin, address(device_access, "counter"))
    assert recorder.received["value"] == 42
    assert recorder.received["write_access"] is False
    connection = plugin.connections[plugin.get_connection_id(recorder.channel)]
    assert connection._polling
    plugin.remove_connection(recorder.channel)


@pytest.mark.parametrize(
    "attribute_name, expected_value, expected_enum_strings",
    [
        ("mode", 1, ("Off", "Slow", "Fast")),
        ("flag", 1, ("False", "True")),
        ("State", int(tango.DevState.ON), tango_plugin.STATE_NAMES),
    ],
)
def test_enum_like_types(qtbot, plugin, device_access, attribute_name, expected_value, expected_enum_strings):
    recorder = connect(qtbot, plugin, address(device_access, attribute_name), ("connection", "value", "enum_strings"))
    assert recorder.received["value"] == expected_value
    assert isinstance(recorder.received["value"], int)
    assert recorder.received["enum_strings"] == expected_enum_strings
    plugin.remove_connection(recorder.channel)


def test_write_enum(qtbot, plugin, device_access):
    recorder = connect(qtbot, plugin, address(device_access, "mode"))
    connection = plugin.connections[plugin.get_connection_id(recorder.channel)]
    connection.put_value(2)
    qtbot.waitUntil(lambda: recorder.received["value"] == 2, timeout=5000)
    connection.put_value(1)
    qtbot.waitUntil(lambda: recorder.received["value"] == 1, timeout=5000)
    plugin.remove_connection(recorder.channel)


def test_uchar_is_sent_as_int(qtbot, plugin, device_access):
    recorder = connect(qtbot, plugin, address(device_access, "uchar"))
    assert recorder.received["value"] == 200
    assert isinstance(recorder.received["value"], int)
    plugin.remove_connection(recorder.channel)


def test_w_value(qtbot, plugin, device_access):
    readback = connect(qtbot, plugin, address(device_access, "doubled"))
    setpoint = connect(qtbot, plugin, address(device_access, "doubled") + "?w_value")
    assert len(plugin.connections) == 2
    connection = plugin.connections[plugin.get_connection_id(setpoint.channel)]
    assert connection.use_w_value

    connection.put_value(3.0)
    qtbot.waitUntil(lambda: setpoint.received["value"] == 3.0, timeout=5000)
    qtbot.waitUntil(lambda: readback.received["value"] == 6.0, timeout=5000)
    assert setpoint.received["write_access"] is True
    connection.put_value(1.0)
    qtbot.waitUntil(lambda: readback.received["value"] == 2.0, timeout=5000)

    plugin.remove_connection(readback.channel)
    plugin.remove_connection(setpoint.channel)


def test_spectrum_and_string(qtbot, plugin, device_access):
    spectrum = connect(qtbot, plugin, address(device_access, "spectrum"))
    text = connect(qtbot, plugin, address(device_access, "text"))
    assert isinstance(spectrum.received["value"], np.ndarray)
    np.testing.assert_array_equal(spectrum.received["value"], [1.0, 2.0, 3.0])
    assert text.received["value"] == "hello"
    plugin.remove_connection(spectrum.channel)
    plugin.remove_connection(text.channel)


def test_second_listener_gets_cached_state(qtbot, plugin, device_access):
    first = connect(qtbot, plugin, address(device_access, "position"), ("connection", "value", "unit"))
    second = connect(qtbot, plugin, address(device_access, "position"), ("connection", "value", "unit"))
    assert len(plugin.connections) == 1
    assert second.received["value"] == first.received["value"]
    assert second.received["unit"] == "mm"
    plugin.remove_connection(first.channel)
    plugin.remove_connection(second.channel)
    assert len(plugin.connections) == 0


def test_unreachable_device(qtbot, plugin):
    recorder = Recorder("tango://127.0.0.1:1/a/b/c/attr#dbase=no")
    plugin.add_connection(recorder.channel)
    qtbot.waitUntil(lambda: "connection" in recorder.received, timeout=5000)
    qtbot.wait(500)
    assert recorder.received["connection"] is False
    assert "value" not in recorder.received
    plugin.remove_connection(recorder.channel)
