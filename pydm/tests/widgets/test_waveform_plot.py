import numpy as np
from pyqtgraph import BarGraphItem
from unittest import mock
from unittest.mock import MagicMock, patch
from pydm.widgets.waveformplot import PyDMWaveformPlot, WaveformCurveItem


@mock.patch("pydm.widgets.waveformplot.WaveformCurveItem.setData")
@mock.patch("pyqtgraph.BarGraphItem.setOpts")
def test_redraw_plot(mocked_set_opts, mocked_set_data, qtbot, monkeypatch):
    """Test redrawing a waveform plot using both a line and a bar graph"""

    # Create a waveform plot and add two data items to it, one to be rendered as a line and one as a bar graph
    waveform_plot = PyDMWaveformPlot()
    line_item = WaveformCurveItem()
    bar_item = WaveformCurveItem(plot_style="Bar")
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

    # The line item should result in a call to set data displaying all available data points as defined above
    assert np.array_equal(mocked_set_data.call_args_list[2][1]["x"], np.array([1, 5, 10]))
    assert np.array_equal(mocked_set_data.call_args_list[2][1]["y"], np.array([10, 15, 12]))

    # As should the bar item, using the set_opts call instead of setData
    assert np.array_equal(mocked_set_opts.call_args_list[1][1]["x"], np.array([0.5, 1, 1.5, 2, 10, 11]))
    assert np.array_equal(mocked_set_opts.call_args_list[1][1]["height"], np.array([45, 50, 52, 40, 24, 30]))

    # After a call to redraw, the plot returns to this state until more data arrives
    assert not waveform_plot._needs_redraw


def test_mismatched_shapes(qtbot):
    """Test that the logic around waveforms with differing lengths works as expected"""

    # Create a waveform plot and add data whose waveform components do not share the same length
    PyDMWaveformPlot()
    data_item_1 = WaveformCurveItem()

    # Start with the basic case, both waveforms share the same length
    data_item_1.receiveXWaveform(np.array([1, 5, 10, 15], dtype=float))
    data_item_1.receiveYWaveform(np.array([10, 11, 12, 13], dtype=float))
    data_item_1.redrawCurve()

    # The data should remain exactly as is, no truncation required
    assert np.array_equal(data_item_1.x_waveform, np.array([1, 5, 10, 15]))
    assert np.array_equal(data_item_1.y_waveform, np.array([10, 11, 12, 13]))

    data_item_1.receiveXWaveform(np.array([1, 5, 10], dtype=float))
    data_item_1.receiveYWaveform(np.array([10, 11, 12, 13], dtype=float))
    data_item_1.redrawCurve()

    # Now the y-waveform was longer than the x one, so it gets truncated to match the length of x
    assert np.array_equal(data_item_1.x_waveform, np.array([1, 5, 10]))
    assert np.array_equal(data_item_1.y_waveform, np.array([10, 11, 12]))

    data_item_1.receiveXWaveform(np.array([1, 5, 10, 15], dtype=float))
    data_item_1.receiveYWaveform(np.array([10, 11, 12], dtype=float))
    data_item_1.redrawCurve()

    # Opposite case: the x-waveform was longer than the y one, so it gets truncated to match the length of y
    assert np.array_equal(data_item_1.x_waveform, np.array([1, 5, 10]))
    assert np.array_equal(data_item_1.y_waveform, np.array([10, 11, 12]))


def test_clear_curves(qtbot):
    """Verify that all curves are removed from a waveform plot when clearCurves() is called"""
    # Create a plot with two curves added to it
    waveform_plot = PyDMWaveformPlot()
    qtbot.addWidget(waveform_plot)
    data_one = WaveformCurveItem()
    data_two = WaveformCurveItem()
    waveform_plot.addCurve(data_one)
    waveform_plot.addCurve(data_two)

    assert len(waveform_plot.plotItem.curves) == 2  # Confirm that the curves were added properly

    waveform_plot.clearCurves()
    assert len(waveform_plot.plotItem.curves) == 0  # Now they should be gone


def test_clear_axes(qtbot):
    """Verify that when multiple y-axes are added to a plot, clearing out the curves and axes cleans up everything"""
    # Create a plot with two separate y axes on it, each with its own associated view box
    waveform_plot = PyDMWaveformPlot()
    qtbot.addWidget(waveform_plot)
    data_one = WaveformCurveItem()
    data_two = WaveformCurveItem()
    waveform_plot.addCurve(data_one, y_axis_name="Axis 1")
    waveform_plot.addCurve(data_two, y_axis_name="Axis 2")

    # Ensure both axes were properly added
    assert "Axis 1" in waveform_plot.plotItem.axes
    assert "Axis 2" in waveform_plot.plotItem.axes
    assert len(waveform_plot.plotItem.stackedViews) == 3  # There is a main top level view in addition to the 2 we added

    waveform_plot.clearAxes()

    # After the call to clear both axes should be removed, and the stacked views are also empty until more data is added
    assert "Axis 1" not in waveform_plot.plotItem.axes
    assert "Axis 2" not in waveform_plot.plotItem.axes
    assert len(waveform_plot.plotItem.stackedViews) == 0


def test_redrawPlot_no_redraw():
    """
    Test that when _needs_redraw is False, nothing happens.
    """
    widget = PyDMWaveformPlot()
    widget._needs_redraw = False
    # Set up some dummy curves.
    widget._curves = [MagicMock(), MagicMock()]
    widget.crosshair = True  # even if crosshair is True, the method should exit early

    # Call redrawPlot.
    widget.redrawPlot()

    # Ensure that none of the curves had redrawCurve() called.
    for curve in widget._curves:
        curve.redrawCurve.assert_not_called()

    # _needs_redraw remains False.
    assert widget._needs_redraw is False


def test_redrawPlot_without_crosshair():
    """
    Test that when _needs_redraw is True but crosshair is False,
    the curves are redrawn and _needs_redraw is reset.
    """
    widget = PyDMWaveformPlot()
    widget._needs_redraw = True
    # Create dummy curves.
    curves = [MagicMock(), MagicMock()]
    widget._curves = curves
    widget.crosshair = False

    # Call redrawPlot.
    widget.redrawPlot()

    # Verify each curve's redrawCurve was called once.
    for curve in curves:
        curve.redrawCurve.assert_called_once()

    # _needs_redraw should now be False.
    assert widget._needs_redraw is False


def test_redrawPlot_with_crosshair():
    """
    Test that when _needs_redraw is True and crosshair is True,
    the curves are redrawn, crosshair is updated, and the signal is emitted.
    """
    widget = PyDMWaveformPlot()
    widget._needs_redraw = True
    # Create dummy curves.
    curves = [MagicMock(), MagicMock()]
    widget._curves = curves
    widget.crosshair = True

    # Set up dummy positions.
    dummy_global_pos = MagicMock()  # This will be returned by QCursor.pos()
    dummy_local_pos = MagicMock()  # Returned by mapFromGlobal
    dummy_scene_pos = MagicMock()  # Returned by mapToScene
    dummy_scene_pos.x.return_value = 150.0
    dummy_scene_pos.y.return_value = 250.0

    # Override mapFromGlobal and mapToScene.
    widget.mapFromGlobal = MagicMock(return_value=dummy_local_pos)
    widget.mapToScene = MagicMock(return_value=dummy_scene_pos)

    # Patch QCursor.pos to return dummy_global_pos.
    with patch("PyQt5.QtGui.QCursor.pos", return_value=dummy_global_pos):
        # Set up a dummy plotItem with sceneBoundingRect() and vb.mapSceneToView().
        dummy_rect = MagicMock()
        dummy_rect.contains.return_value = True  # Indicate scene_pos is within bounds
        dummy_mapped_point = MagicMock()
        dummy_mapped_point.x.return_value = 300.0
        dummy_mapped_point.y.return_value = 400.0

        dummy_vb = MagicMock()
        dummy_vb.mapSceneToView.return_value = dummy_mapped_point

        widget.plotItem = MagicMock()
        widget.plotItem.sceneBoundingRect.return_value = dummy_rect
        widget.plotItem.vb = dummy_vb

        # Create dummy crosshair line objects.
        widget.vertical_crosshair_line = MagicMock()
        widget.horizontal_crosshair_line = MagicMock()
        # Simulate a signal by using a MagicMock for emit.
        widget.crosshair_position_updated = MagicMock()

        # Call redrawPlot.
        widget.redrawPlot()

    # Verify that redrawCurve was called for each curve.
    for curve in curves:
        curve.redrawCurve.assert_called_once()

    # _needs_redraw should be reset.
    assert widget._needs_redraw is False

    # Verify that the crosshair lines' setPos methods were called with the mapped coordinates.
    widget.vertical_crosshair_line.setPos.assert_called_once_with(dummy_mapped_point.x())
    widget.horizontal_crosshair_line.setPos.assert_called_once_with(dummy_mapped_point.y())

    # Verify that the crosshair_position_updated signal was emitted with the scene position.
    widget.crosshair_position_updated.emit.assert_called_once_with(dummy_scene_pos.x(), dummy_scene_pos.y())
