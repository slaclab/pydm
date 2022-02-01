import pytest
from unittest import mock
from pyqtgraph import AxisItem, ViewBox
from qtpy.QtWidgets import QGraphicsScene
from ...widgets.multi_axis_plot import MultiAxisPlot


@pytest.fixture
def sample_plot(qtbot, monkeypatch):
    """ Set up a plot with a couple of test axis items for use in test cases below """
    plot = MultiAxisPlot()
    scene = QGraphicsScene()
    monkeypatch.setattr(plot, 'scene', lambda: scene)  # Have the plot return a dummy scene when needed

    # Create two axes, one with a fixed range and one that should auto-range (adjust to always display all data)
    fixed_range_axis = AxisItem('left')
    plot.addAxis(fixed_range_axis, 'Fixed Range Axis', enableAutoRangeY=False, minRange=-5.0, maxRange=7.5)
    auto_range_axis = AxisItem('left')
    plot.addAxis(auto_range_axis, 'Auto Range Axis', enableAutoRangeY=True)

    return plot


def test_original_ranges_set_correctly(sample_plot):
    """ Check that the original ranges of x and y axes are preserved when adding them into the plot """

    # The axis with a set range should have that preserved
    assert sample_plot.axesOriginalRanges['Fixed Range Axis'][0] == -5.0
    assert sample_plot.axesOriginalRanges['Fixed Range Axis'][1] == 7.5

    # And the axis set to auto-range should be set to None indicating there is no fixed range to preserve
    assert sample_plot.axesOriginalRanges['Auto Range Axis'][0] is None
    assert sample_plot.axesOriginalRanges['Auto Range Axis'][1] is None


@mock.patch('pyqtgraph.ViewBox.enableAutoRange')
@mock.patch('pyqtgraph.PlotItem.setXRange')
@mock.patch('pyqtgraph.ViewBox.setYRange')
def test_restore_axis_ranges(mocked_y_range, mocked_x_range, mocked_auto_range, sample_plot):
    """
    Verify that when axis ranges have been changed from their defaults, calling restore will set them back to
    their original values
    """

    # First let's set a starting range on the bottom axis as well as those set in the fixture
    sample_plot.axesOriginalRanges['bottom'] = (0.0, 10.0)

    sample_plot.restoreAxisRanges()

    # After the call to restore axis ranges, ensure the view box calls are made as expected. (Don't want to test
    # view box functionality here as that is very involved and covered in pyqtgraph itself)
    mocked_auto_range.assert_any_call(axis=ViewBox.YAxis, enable=True)  # Auto-range enabled for our auto-range axis
    mocked_y_range.assert_called_once_with(-5.0, 7.5)  # Fixed range restored for the other axis
    mocked_x_range.assert_called_once_with(0.0, 10.0, padding=0)  # X-axis restored to the values specified above
