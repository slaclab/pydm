import pytest
import logging
import numpy as np
from collections import OrderedDict
from pyqtgraph import AxisItem, BarGraphItem
from unittest import mock
from pydm.widgets.channel import PyDMChannel
from pydm.widgets.timeplot import (
    TimePlotCurveItem,
    PyDMTimePlot,
    TimeAxisItem,
    MINIMUM_BUFFER_SIZE,
    DEFAULT_BUFFER_SIZE,
)
from pydm.utilities import remove_protocol, ACTIVE_QT_WRAPPER, QtWrapperTypes
from qtpy.QtTest import QSignalSpy
from unittest.mock import MagicMock

logger = logging.getLogger(__name__)


@pytest.fixture
def time_plot(qtbot):
    """
    Fixture to provide a fresh PyDMTimePlot for each test.
    """
    plot = PyDMTimePlot()
    qtbot.addWidget(plot)
    return plot


@pytest.fixture
def timeplotcurveitem_widget(qtbot):
    """
    Fixture that creates and returns a TimePlotCurveItem instance for each test.
    """
    return TimePlotCurveItem()


def test_timeplotcurveitem_severityChanged_updates_attributes_and_emits(timeplotcurveitem_widget, qtbot):
    """
    Test that calling severityChanged:
    1) Sets self.severity_raw.
    2) Calls alarm_severity_changed -> updates self.severity.
    3) Emits severitySignal with the same severity int.
    """
    severity_spy = QSignalSpy(timeplotcurveitem_widget.severitySignal)
    timeplotcurveitem_widget.severityChanged(2)

    assert timeplotcurveitem_widget.severity_raw == 2
    assert timeplotcurveitem_widget.severity == "MAJOR"

    if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYQT5:
        assert len(severity_spy) == 1
        assert severity_spy[0] == [2]
    else:
        assert severity_spy.count() == 1
        assert severity_spy.at(0) == [2]


def test_timeplotcurveitem_alarm_severity_changed_valid_values(timeplotcurveitem_widget):
    """
    Test alarm_severity_changed with valid integer or string values for severity.
    """
    timeplotcurveitem_widget.alarm_severity_changed(0)
    assert timeplotcurveitem_widget.severity == "NO_ALARM"

    timeplotcurveitem_widget.alarm_severity_changed("1")
    assert timeplotcurveitem_widget.severity == "MINOR"

    timeplotcurveitem_widget.alarm_severity_changed(2)
    assert timeplotcurveitem_widget.severity == "MAJOR"

    timeplotcurveitem_widget.alarm_severity_changed("3")
    assert timeplotcurveitem_widget.severity == "INVALID"


def test_timeplotcurveitem_alarm_severity_changed_invalid_values(timeplotcurveitem_widget):
    """
    Test alarm_severity_changed with invalid severity input, expecting "N/A".
    """
    timeplotcurveitem_widget.alarm_severity_changed(-1)
    assert timeplotcurveitem_widget.severity == "N/A"

    timeplotcurveitem_widget.alarm_severity_changed("not_an_int")
    assert timeplotcurveitem_widget.severity == "N/A"

    timeplotcurveitem_widget.alarm_severity_changed(None)
    assert timeplotcurveitem_widget.severity == "N/A"


@pytest.mark.parametrize(
    "channel_address, name",
    [
        ("ca://test_value:Float", "test_name"),
        ("ca://test_value:Float", ""),
        ("ca://test_value:Float", None),
        ("", None),
        (None, None),
    ],
)
def test_timeplotcurveitem_construct(qtbot, channel_address, name):
    pydm_timeplot_curve_item = TimePlotCurveItem(channel_address=channel_address, name=name)

    if not name:
        assert (
            pydm_timeplot_curve_item.to_dict()["name"] == remove_protocol(channel_address)
            if channel_address
            else not pydm_timeplot_curve_item.to_dict()["name"]
        )

    assert pydm_timeplot_curve_item._bufferSize == MINIMUM_BUFFER_SIZE
    assert pydm_timeplot_curve_item._update_mode == PyDMTimePlot.OnValueChange
    assert np.array_equal(
        pydm_timeplot_curve_item.data_buffer,
        np.zeros((2, pydm_timeplot_curve_item._bufferSize), order="f", dtype=float),
    )
    assert pydm_timeplot_curve_item.connected is False
    assert pydm_timeplot_curve_item.points_accumulated == 0
    assert pydm_timeplot_curve_item.latest_value is None
    assert (
        pydm_timeplot_curve_item.address == channel_address
        if channel_address
        else pydm_timeplot_curve_item.address is None
    )


@pytest.mark.parametrize(
    "channel_address, name",
    [
        ("ca://test_value:Float", "test_name"),
        ("ca://test_value:Float", ""),
        ("ca://test_value:Float", None),
        ("", None),
        (None, None),
    ],
)
def test_timeplotcurveitem_to_dict(qtbot, channel_address, name):
    pydm_timeplot_curve_item = TimePlotCurveItem(channel_address=channel_address, name=name)

    dictionary = pydm_timeplot_curve_item.to_dict()
    assert isinstance(dictionary, OrderedDict)

    assert dictionary["channel"] == channel_address if channel_address else dictionary["channel"] is None
    if name:
        assert dictionary["name"] == name
    else:
        assert (
            pydm_timeplot_curve_item.to_dict()["name"] == remove_protocol(channel_address)
            if channel_address
            else not pydm_timeplot_curve_item.to_dict()["name"]
        )


@pytest.mark.parametrize("new_address", ["new_address", "", None])
def test_timeplotcurveitem_properties_and_setters(qtbot, new_address):
    pydm_timeplot_curve_item = TimePlotCurveItem()

    assert pydm_timeplot_curve_item.address is None

    pydm_timeplot_curve_item.address = new_address
    if new_address:
        assert isinstance(pydm_timeplot_curve_item.channel, PyDMChannel)
        assert pydm_timeplot_curve_item.channel.address == new_address
    else:
        assert pydm_timeplot_curve_item.channel is None


def test_timeplotcurveitem_connection_state_changed(qtbot, signals):
    pydm_timeplot_curve_item = TimePlotCurveItem()
    assert pydm_timeplot_curve_item.connected is False

    signals.connection_state_signal.connect(pydm_timeplot_curve_item.connectionStateChanged)
    signals.connection_state_signal.emit(True)
    assert pydm_timeplot_curve_item.connected


@pytest.mark.parametrize("async_update, new_data", [(False, -10), (False, 10.2333), (True, 100), (True, -123.456)])
def test_timeplotcurveitem_receive_value(qtbot, signals, async_update, new_data):
    """
    Also testing setUpdatesAsynchronously, resetUpdatesAsynchronously, and initialize_buffer
    Parameters
    ----------
    qtbot
    async_update

    Returns
    -------

    """
    pydm_timeplot_curve_item = TimePlotCurveItem()

    assert pydm_timeplot_curve_item._update_mode == PyDMTimePlot.OnValueChange

    pydm_timeplot_curve_item.setUpdatesAsynchronously(async_update)
    if async_update:
        assert (
            pydm_timeplot_curve_item._update_mode == PyDMTimePlot.AtFixedRate
            if async_update
            else pydm_timeplot_curve_item._update_mode == PyDMTimePlot.OnValueChange
        )

    expected_data_buffer = np.zeros((2, pydm_timeplot_curve_item._bufferSize), order="f", dtype=float)
    expected_data_buffer[0] = pydm_timeplot_curve_item.data_buffer[0]
    assert np.array_equal(expected_data_buffer, pydm_timeplot_curve_item.data_buffer)

    signals.new_value_signal[type(new_data)].connect(pydm_timeplot_curve_item.receiveNewValue)
    signals.new_value_signal[type(new_data)].emit(new_data)

    if async_update:
        assert np.array_equal(pydm_timeplot_curve_item.latest_value, new_data)
    else:
        assert np.array_equal(
            pydm_timeplot_curve_item.data_buffer[1, pydm_timeplot_curve_item._bufferSize - 1], new_data
        )
        assert pydm_timeplot_curve_item.points_accumulated == 1

    pydm_timeplot_curve_item.resetUpdatesAsynchronously()
    assert pydm_timeplot_curve_item._update_mode == PyDMTimePlot.OnValueChange


@pytest.mark.parametrize("async_update, new_data", [(False, -10), (False, 10.2333), (True, 100), (True, -123.456)])
def test_timeplotcurveitem_async_update(qtbot, signals, async_update, new_data):
    pydm_timeplot_curve_item = TimePlotCurveItem()

    assert pydm_timeplot_curve_item._update_mode == PyDMTimePlot.OnValueChange

    pydm_timeplot_curve_item.setUpdatesAsynchronously(async_update)

    signals.new_value_signal[type(new_data)].connect(pydm_timeplot_curve_item.receiveNewValue)
    signals.new_value_signal[type(new_data)].emit(new_data)

    signals.new_value_signal[type(new_data)].connect(pydm_timeplot_curve_item.asyncUpdate)
    signals.new_value_signal[type(new_data)].emit(new_data)

    if async_update:
        assert np.array_equal(
            pydm_timeplot_curve_item.data_buffer[1, pydm_timeplot_curve_item._bufferSize - 1], new_data
        )
        assert pydm_timeplot_curve_item.points_accumulated == 1
    else:
        assert pydm_timeplot_curve_item.points_accumulated == 2


def test_timeplotcurve_initialize_buffer(qtbot):
    pydm_timeplot_curve_item = TimePlotCurveItem()

    pydm_timeplot_curve_item.initialize_buffer()

    assert pydm_timeplot_curve_item.points_accumulated == 0
    expected_data_buffer = np.zeros((2, pydm_timeplot_curve_item._bufferSize), order="f", dtype=float)
    expected_data_buffer[0] = pydm_timeplot_curve_item.data_buffer[0]

    assert np.array_equal(expected_data_buffer, pydm_timeplot_curve_item.data_buffer)


@pytest.mark.parametrize(
    "new_buffer_size, expected_set_buffer_size",
    [
        (0, MINIMUM_BUFFER_SIZE),
        (-5, MINIMUM_BUFFER_SIZE),
        (100, 100),
        (MINIMUM_BUFFER_SIZE + 1, MINIMUM_BUFFER_SIZE + 1),
    ],
)
def test_timeplotcurve_get_set_reset_buffer_size(qtbot, new_buffer_size, expected_set_buffer_size):
    pydm_timeplot_curve_item = TimePlotCurveItem()

    assert pydm_timeplot_curve_item.getBufferSize() == MINIMUM_BUFFER_SIZE

    pydm_timeplot_curve_item.setBufferSize(new_buffer_size)
    assert pydm_timeplot_curve_item.getBufferSize() == expected_set_buffer_size

    pydm_timeplot_curve_item.resetBufferSize()
    assert pydm_timeplot_curve_item.getBufferSize() == DEFAULT_BUFFER_SIZE


def test_timeplotcurve_max_x(qtbot):
    pydm_timeplot_curve_item = TimePlotCurveItem()

    pydm_timeplot_curve_item.data_buffer[0, pydm_timeplot_curve_item._bufferSize - 1] = -1
    pydm_timeplot_curve_item.data_buffer[1, pydm_timeplot_curve_item._bufferSize - 1] = 100

    max_value = pydm_timeplot_curve_item.max_x()
    assert max_value == pydm_timeplot_curve_item.data_buffer[0, pydm_timeplot_curve_item._bufferSize - 1]
    assert pydm_timeplot_curve_item.data_buffer[1, pydm_timeplot_curve_item._bufferSize - 1] == 100


def test_timeaxisitem_tickstrings():
    time_axis_item = TimeAxisItem("bottom")
    assert len(time_axis_item.tickStrings((10, 20, 30), 1, 1)) > 0


def test_pydmtimeplot_construct(qtbot):
    pydm_timeplot = PyDMTimePlot()
    qtbot.addWidget(pydm_timeplot)

    assert isinstance(pydm_timeplot._bottom_axis, AxisItem)
    assert pydm_timeplot._bottom_axis.orientation == "bottom"


def test_pydmtimeplot_add_curve(qtbot):
    pydm_timeplot = PyDMTimePlot()
    qtbot.addWidget(pydm_timeplot)

    curve_pv = "loc://test:timeplot:pv"
    pydm_timeplot.addYChannel(curve_pv)

    assert pydm_timeplot.findCurve(curve_pv) is not None


@mock.patch("pydm.widgets.timeplot.TimePlotCurveItem.setData")
@mock.patch("pyqtgraph.BarGraphItem.setOpts")
def test_redraw_plot(mocked_set_opts, mocked_set_data, qtbot, monkeypatch):
    """Test redrawing a time plot using both a line and a bar graph"""

    # Create a time plot and add two data items to it, one to be rendered as a line and one as a bar graph
    time_plot = PyDMTimePlot()
    line_item = TimePlotCurveItem()
    bar_item = TimePlotCurveItem(plot_style="Bar")
    bar_item.bar_graph_item = BarGraphItem(x=[], height=[], width=1.0)
    time_plot.addCurve(line_item)
    time_plot.addCurve(bar_item)

    # Setup some mock data for our data items
    line_item.data_buffer = np.array([[1, 5, 10], [10, 15, 12]], dtype=float)
    line_item.points_accumulated = 3
    bar_item.data_buffer = np.array([[0.5, 1, 1.5, 2, 10, 11], [45, 50, 52, 40, 24, 30]], dtype=float)
    bar_item.points_accumulated = 6

    time_plot.set_needs_redraw()
    time_plot.plotItem.setXRange(1, 10)  # Sets the visible x-range of this time plot

    monkeypatch.setattr(time_plot, "updateXAxis", lambda: None)  # Ensure the view box range is deterministic

    # Simulate a redraw of the plot
    time_plot.redrawPlot()

    # The line item should result in a call to set data displaying all available data points as defined above
    assert np.array_equal(mocked_set_data.call_args_list[2][1]["x"], np.array([1, 5, 10]))
    assert np.array_equal(mocked_set_data.call_args_list[2][1]["y"], np.array([10, 15, 12]))

    # Because we want to limit rendering of bar graphs to only those data points which are visible, we should
    # see a call made with only 4 of the 6 data points. The data points associated with the x values 0.5 and 11
    # were omitted since they fell outside the viewable range of 1 to 10.
    assert np.array_equal(mocked_set_opts.call_args_list[1][1]["x"], np.array([1, 1.5, 2, 10]))
    assert np.array_equal(mocked_set_opts.call_args_list[1][1]["height"], np.array([50, 52, 40, 24]))

    # After a call to redraw, the plot returns to this state until more data arrives
    assert not time_plot._needs_redraw


class BasePlotDummy:
    def updateLabel(self, x_val, y_val):
        self.parent_called = True


class TimePlotDummy(BasePlotDummy):
    def __init__(self):
        self.textItems = {}
        self.parent_called = False

    def updateLabel(self, x_val: float, y_val: float) -> None:
        super().updateLabel(x_val, y_val)

        for curve, label in self.textItems.items():
            if getattr(curve, "severity_raw", -1) != -1:
                old_text = label.toPlainText()
                label.setText(old_text + "\n" + str(curve.severity))


def test_updateLabel():
    instance = TimePlotDummy()

    curve_with_severity = MagicMock()
    curve_with_severity.severity_raw = 1
    curve_with_severity.severity = "HIGH"

    curve_without_severity = MagicMock()
    curve_without_severity.severity_raw = -1

    label1 = MagicMock()
    label1.toPlainText.return_value = "Curve1"
    label2 = MagicMock()
    label2.toPlainText.return_value = "Curve2"

    instance.textItems = {
        curve_with_severity: label1,
        curve_without_severity: label2,
    }

    instance.updateLabel(10.0, 20.0)

    assert instance.parent_called, "Parent's updateLabel was not called."
    label1.setText.assert_called_once_with("Curve1\nHIGH")
    label2.setText.assert_not_called()
