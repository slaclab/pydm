import pytest
import logging
import numpy as np
from collections import OrderedDict
from pydm.widgets.channel import PyDMChannel
from pydm.widgets.scatterplot import ScatterPlotCurveItem, MINIMUM_BUFFER_SIZE, DEFAULT_BUFFER_SIZE
from pydm.utilities import remove_protocol

logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "y_addr, x_addr, redraw_mode, bufferSizeChannelAddress, name",
    [
        ("ca://test_value:FloatY", "ca://test_value:FloatX", None, None, "test_name"),
        ("ca://test_value:FloatY", "ca://test_value:FloatX", None, None, ""),
        ("ca://test_value:FloatY", "ca://test_value:FloatX", None, None, None),
        ("", "", None, None, None),
        (None, None, None, None, None),
        ("ca://test_value:FloatY", "ca://test_value:FloatX", ScatterPlotCurveItem.REDRAW_ON_BOTH, None, ""),
        ("ca://test_value:FloatY", "ca://test_value:FloatX", None, "ca://test_value:Int", "test_name"),
    ],
)
def test_scatterplotcurveitem_construct(qtbot, y_addr, x_addr, redraw_mode, bufferSizeChannelAddress, name):
    plot_curve_item = ScatterPlotCurveItem(
        y_addr, x_addr, redraw_mode=redraw_mode, bufferSizeChannelAddress=bufferSizeChannelAddress, name=name
    )
    assert plot_curve_item is not None
    assert isinstance(plot_curve_item, ScatterPlotCurveItem)

    assert plot_curve_item._bufferSize == DEFAULT_BUFFER_SIZE
    assert plot_curve_item.redraw_mode == redraw_mode or ScatterPlotCurveItem.REDRAW_ON_EITHER
    assert np.array_equal(
        plot_curve_item.data_buffer, np.zeros((2, plot_curve_item._bufferSize), order="f", dtype=float)
    )
    for item in "x_connected y_connected bufferSizeChannel_connected".split():
        assert getattr(plot_curve_item, item) is False
    assert plot_curve_item.points_accumulated == 0
    for item in "latest_x_value latest_y_value".split():
        assert getattr(plot_curve_item, item) is None

    keys = (
        ("x_address", x_addr),
        ("y_address", y_addr),
        ("bufferSizeChannelAddress", bufferSizeChannelAddress),
    )
    for attr, kw in keys:
        obj = getattr(plot_curve_item, attr)
        expect = kw if kw else None
        assert obj == expect, f"{attr} {kw} {expect}"


@pytest.mark.parametrize(
    "y_addr, x_addr, redraw_mode, bufferSizeChannelAddress, name",
    [
        ("ca://test_value:FloatY", "ca://test_value:FloatX", None, None, "test_name"),
        ("ca://test_value:FloatY", "ca://test_value:FloatX", None, None, ""),
        ("ca://test_value:FloatY", "ca://test_value:FloatX", None, None, None),
        ("", "", None, None, None),
        (None, None, None, None, None),
        ("ca://test_value:FloatY", "ca://test_value:FloatX", ScatterPlotCurveItem.REDRAW_ON_BOTH, None, ""),
        ("ca://test_value:FloatY", "ca://test_value:FloatX", None, "ca://test_value:Int", "test_name"),
    ],
)
def test_scatterplotcurveitem_to_dict(qtbot, y_addr, x_addr, redraw_mode, bufferSizeChannelAddress, name):
    plot_curve_item = ScatterPlotCurveItem(
        y_addr, x_addr, redraw_mode=redraw_mode, bufferSizeChannelAddress=bufferSizeChannelAddress, name=name
    )

    dictionary = plot_curve_item.to_dict()
    assert isinstance(dictionary, OrderedDict)

    y_name = remove_protocol(y_addr if y_addr is not None else "")
    x_name = remove_protocol(x_addr if x_addr is not None else "")
    if name is None:
        if y_addr is None and x_addr is None:
            assert dictionary["name"] == ""
        else:
            assert dictionary["name"] == f"{y_name} vs. {x_name}"
    else:
        assert dictionary["name"] == name


@pytest.mark.parametrize("new_address", ["new_address", "", None])
def test_scatterplotcurveitem_properties_and_setters(qtbot, new_address):
    plot_curve_item = ScatterPlotCurveItem(new_address, new_address, bufferSizeChannelAddress=new_address)

    assert plot_curve_item.x_address in (None, new_address)
    assert plot_curve_item.y_address in (None, new_address)
    assert plot_curve_item.bufferSizeChannelAddress in (None, new_address)

    if new_address:
        assert isinstance(plot_curve_item.x_channel, PyDMChannel)
        assert plot_curve_item.x_channel.address == new_address
        assert plot_curve_item.y_channel.address == new_address
    else:
        assert plot_curve_item.x_channel is None
        assert plot_curve_item.y_channel is None
        assert plot_curve_item.bufferSizeChannel is None


def test_scatterplotcurveitem_connection_state_changed(qtbot, signals):
    plot_curve_item = ScatterPlotCurveItem(None, None)
    assert plot_curve_item.x_connected is False
    assert plot_curve_item.y_connected is False

    signals.connection_state_signal.connect(plot_curve_item.xConnectionStateChanged)
    signals.connection_state_signal.emit(True)
    assert plot_curve_item.x_connected


@pytest.mark.parametrize(
    "redraw_mode, new_data",
    [
        (ScatterPlotCurveItem.REDRAW_ON_EITHER, [(0, 0), (1, 1), (2, 2), (2.5, 3.1)]),
        (ScatterPlotCurveItem.REDRAW_ON_BOTH, [(0, 0), (1, 1), (2, 2), (2.5, 3.1)]),
        (ScatterPlotCurveItem.REDRAW_ON_X, [(0, 0), (1, 1), (2, 2), (2.5, 3.1)]),
        (ScatterPlotCurveItem.REDRAW_ON_Y, [(0, 0), (1, 1), (2, 2), (2.5, 3.1)]),
    ],
)
def test_scatterplotcurveitem_receive_values(qtbot, signals, redraw_mode, new_data):
    # REDRAW_ON_X, REDRAW_ON_Y, REDRAW_ON_EITHER, REDRAW_ON_BOTH
    plot_curve_item = ScatterPlotCurveItem(None, None, redraw_mode=redraw_mode)

    expected_data_buffer = np.zeros((2, plot_curve_item._bufferSize), order="f", dtype=float)
    expected_data_buffer[0] = plot_curve_item.data_buffer[0]
    assert np.array_equal(expected_data_buffer, plot_curve_item.data_buffer)

    # inject the new_data, point by point
    assert plot_curve_item.points_accumulated == 0
    for i, pair in enumerate(new_data):
        new_x, new_y = pair

        plot_curve_item.receiveXValue(new_x)
        assert plot_curve_item.latest_x_value == new_x
        assert plot_curve_item.points_accumulated == 2 * i

        plot_curve_item.receiveYValue(new_y)
        assert plot_curve_item.latest_y_value == new_y
        assert plot_curve_item.points_accumulated == 2 * i + 1


def test_scatterplotcurve_initialize_buffer(qtbot):
    plot_curve_item = ScatterPlotCurveItem(None, None)

    plot_curve_item.initialize_buffer()

    assert plot_curve_item.points_accumulated == 0
    expected_data_buffer = np.zeros((2, plot_curve_item._bufferSize), order="f", dtype=float)
    expected_data_buffer[0] = plot_curve_item.data_buffer[0]

    assert np.array_equal(expected_data_buffer, plot_curve_item.data_buffer)


@pytest.mark.parametrize(
    "new_buffer_size, expected_set_buffer_size",
    [
        (0, MINIMUM_BUFFER_SIZE),
        (-5, MINIMUM_BUFFER_SIZE),
        (100, 100),
        (MINIMUM_BUFFER_SIZE + 1, MINIMUM_BUFFER_SIZE + 1),
    ],
)
def test_scatterplotcurve_get_set_reset_buffer_size(qtbot, new_buffer_size, expected_set_buffer_size):
    plot_curve_item = ScatterPlotCurveItem(None, None)

    assert plot_curve_item.getBufferSize() == DEFAULT_BUFFER_SIZE

    plot_curve_item.setBufferSize(new_buffer_size)
    assert plot_curve_item.getBufferSize() == expected_set_buffer_size

    plot_curve_item.resetBufferSize()
    assert plot_curve_item.getBufferSize() == DEFAULT_BUFFER_SIZE


@pytest.mark.parametrize(
    "addr, new_size, expected_buffer_size",
    [
        (None, None, DEFAULT_BUFFER_SIZE),
        ("", None, DEFAULT_BUFFER_SIZE),
        ("ca://test_value:Int", None, DEFAULT_BUFFER_SIZE),
    ],
)
def test_scatterplotcurve_get_set_reset_buffer_size_channel_addr(qtbot, addr, new_size, expected_buffer_size):
    plot_curve_item = ScatterPlotCurveItem(None, None, bufferSizeChannelAddress=addr)

    assert plot_curve_item.getBufferSize() == DEFAULT_BUFFER_SIZE

    if new_size is not None:
        plot_curve_item.bufferSizeChannelValueReceiver(new_size)
        assert plot_curve_item.getBufferSize() == new_size
        assert plot_curve_item.data_buffer.shape == (2, new_size)
