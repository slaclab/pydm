import numpy as np
from pyqtgraph import BarGraphItem
from unittest import mock
from ...widgets.waveformplot import PyDMWaveformPlot, WaveformCurveItem


@mock.patch('pydm.widgets.waveformplot.WaveformCurveItem.setData')
@mock.patch('pyqtgraph.BarGraphItem.setOpts')
def test_redraw_plot(mocked_set_opts, mocked_set_data, qtbot, monkeypatch):
    """ Test redrawing a waveform plot using both a line and a bar graph """

    # Create a time plot and add two data items to it, one to be rendered as a line and one as a bar graph
    waveform_plot = PyDMWaveformPlot()
    line_item = WaveformCurveItem()
    bar_item = WaveformCurveItem(plot_style='Bar')
    bar_item.bar_graph_item = BarGraphItem(x=[], height=[], width=1.0)
    waveform_plot.addCurve(line_item)
    waveform_plot.addCurve(bar_item)

    # Setup some mock data for our data items
    line_item.receiveXWaveform(np.array([1, 5, 10], dtype=float))
    line_item.receiveYWaveform(np.array([10, 15, 12], dtype=float))
    bar_item.receiveXWaveform(np.array([0.5, 1, 1.5, 2, 10, 11], dtype=float))
    bar_item.receiveYWaveform(np.array([45, 50, 52, 40, 24, 30], dtype=float))

    waveform_plot.set_needs_redraw()

    # Simulate a redraw of the plot
    waveform_plot.redrawPlot()

    print(mocked_set_data.call_args_list)
    # The line item should result in a call to set data displaying all available data points as defined above
    assert np.array_equal(mocked_set_data.call_args_list[2][1]['x'], np.array([1, 5, 10]))
    assert np.array_equal(mocked_set_data.call_args_list[2][1]['y'], np.array([10, 15, 12]))

    # As should the bar item, using the set_opts call instead of setData
    assert np.array_equal(mocked_set_opts.call_args_list[1][1]['x'], np.array([0.5, 1, 1.5, 2, 10, 11]))
    assert np.array_equal(mocked_set_opts.call_args_list[1][1]['height'], np.array([45, 50, 52, 40, 24, 30]))

    # After a call to redraw, the plot returns to this state until more data arrives
    assert not waveform_plot._needs_redraw
