import pytest
from unittest import mock
from unittest.mock import patch
from pyqtgraph import AxisItem, PlotDataItem, ViewBox
from qtpy.QtWidgets import QGraphicsScene
from pydm.widgets.multi_axis_plot import MultiAxisPlot


@pytest.fixture
def sample_plot(qtbot, monkeypatch):
    """Set up a plot with a couple of test axis items for use in test cases below"""
    plot = MultiAxisPlot()
    scene = QGraphicsScene()
    monkeypatch.setattr(plot, "scene", lambda: scene)  # Have the plot return a dummy scene when needed

    # Create two axes, one with a fixed range and one that should auto-range (adjust to always display all data)
    fixed_range_axis = AxisItem("left")
    plot.addAxis(fixed_range_axis, "Fixed Range Axis", enableAutoRangeY=False, minRange=-5.0, maxRange=7.5)
    auto_range_axis = AxisItem("left")
    plot.addAxis(auto_range_axis, "Auto Range Axis", enableAutoRangeY=True)

    return plot


def test_original_ranges_set_correctly(sample_plot):
    """Check that the original ranges of x and y axes are preserved when adding them into the plot"""

    # The axis with a set range should have that preserved
    assert sample_plot.axesOriginalRanges["Fixed Range Axis"][0] == -5.0
    assert sample_plot.axesOriginalRanges["Fixed Range Axis"][1] == 7.5

    # And the axis set to auto-range should be set to None indicating there is no fixed range to preserve
    assert sample_plot.axesOriginalRanges["Auto Range Axis"][0] is None
    assert sample_plot.axesOriginalRanges["Auto Range Axis"][1] is None


@mock.patch("pyqtgraph.ViewBox.enableAutoRange")
@mock.patch("pyqtgraph.PlotItem.setXRange")
@mock.patch("pyqtgraph.ViewBox.setYRange")
def test_restore_axis_ranges(mocked_y_range, mocked_x_range, mocked_auto_range, sample_plot):
    """
    Verify that when axis ranges have been changed from their defaults, calling restore will set them back to
    their original values
    """

    # First let's set a starting range on the bottom axis as well as those set in the fixture
    sample_plot.axesOriginalRanges["bottom"] = (0.0, 10.0)

    sample_plot.restoreAxisRanges()

    # After the call to restore axis ranges, ensure the view box calls are made as expected. (Don't want to test
    # view box functionality here as that is very involved and covered in pyqtgraph itself)
    mocked_auto_range.assert_any_call(axis=ViewBox.YAxis, enable=True)  # Auto-range enabled for our auto-range axis
    mocked_y_range.assert_called_once_with(-5.0, 7.5)  # Fixed range restored for the other axis
    mocked_x_range.assert_called_once_with(0.0, 10.0, padding=0)  # X-axis restored to the values specified above


def test_link_data_to_logarithmic_axis(qtbot, monkeypatch, sample_plot):
    """Verify that when a curve is added to an axis with log mode on, that curve is set to log mode as well"""

    # Create one linear axis and one logarithmic axis
    linear_axis = AxisItem("left")
    log_axis = AxisItem("left")
    log_axis.setLogMode(True)

    sample_plot.addAxis(linear_axis, "Linear Axis")
    sample_plot.addAxis(log_axis, "Log Axis")

    # Create a data item to go along with each axis
    linear_data = PlotDataItem()
    log_data = PlotDataItem()

    # Upon creation, all data should default to non-log mode
    assert linear_data.opts["logMode"] == [False, False]
    assert log_data.opts["logMode"] == [False, False]

    sample_plot.linkDataToAxis(linear_data, "Linear Axis")
    sample_plot.linkDataToAxis(log_data, "Log Axis")

    # Now that we've linked the data to their associated axes, the log_data should have logMode set to true, while
    # linear data should still have it set to false
    assert linear_data.opts["logMode"] == [False, False]
    assert log_data.opts["logMode"] == [False, True]


def test_update_log_mode(qtbot, sample_plot):
    """Verify toggling log mode on and off for the entire plot works as expected"""
    data_item = PlotDataItem()
    sample_plot.addItem(data_item)

    # For a brand new plot, log mode defaults to false for everything. Verify this is the case.
    assert data_item.opts["logMode"] == [False, False]
    for axis in sample_plot.getAxes():
        assert not axis.logMode

    # Now set log mode on for y-values only. Verify this gets set correctly, and x-values are left alone.
    sample_plot.setLogMode(False, True)
    assert data_item.opts["logMode"] == [False, True]
    for axis in sample_plot.getAxes():
        if axis.orientation in ("bottom", "top"):
            assert not axis.logMode
        elif axis.orientation in ("left", "right"):
            assert axis.logMode
        else:
            raise ValueError(f"Invalid value for axis orientation: {axis.orientation}")

    # Now set log mode on for x-values only. Verify this gets set correctly, and y-values are left alone.
    sample_plot.setLogMode(True, False)
    assert data_item.opts["logMode"] == [True, False]
    for axis in sample_plot.getAxes():
        if axis.orientation in ("bottom", "top"):
            assert axis.logMode
        elif axis.orientation in ("left", "right"):
            assert not axis.logMode
        else:
            raise ValueError(f"Invalid value for axis orientation: {axis.orientation}")

    # Now set log mode on for everything. Verify this is set across all items.
    sample_plot.setLogMode(True, True)
    assert data_item.opts["logMode"] == [True, True]
    for axis in sample_plot.getAxes():
        assert axis.logMode

    # And finally return everything back to non-log mode. Verify all items are no longer in log mode for x or y.
    sample_plot.setLogMode(False, False)
    assert data_item.opts["logMode"] == [False, False]
    for axis in sample_plot.getAxes():
        assert not axis.logMode


def test_remove_item(qtbot, sample_plot: MultiAxisPlot):
    """Verify that removing an item from the plot works as expected"""

    # First create a couple of mock data items to plot, and add them to the plot
    data_item_one = PlotDataItem()
    data_item_two = PlotDataItem()

    sample_plot.addItem(data_item_one)
    sample_plot.addItem(data_item_two)
    linked_viewbox = data_item_one.getViewBox()

    assert len(sample_plot.items) == 2
    assert len(sample_plot.dataItems) == 2
    assert len(linked_viewbox.addedItems) == 2

    # Now remove them one at a time, and ensure they are cleared out correctly
    sample_plot.removeItem(data_item_one)
    assert len(sample_plot.items) == 1
    assert len(sample_plot.dataItems) == 1
    assert len(linked_viewbox.addedItems) == 1
    assert sample_plot.items[0] == data_item_two
    assert sample_plot.dataItems[0] == data_item_two
    assert linked_viewbox.addedItems[0] == data_item_two

    sample_plot.removeItem(data_item_two)
    assert len(sample_plot.items) == 0
    assert len(sample_plot.dataItems) == 0
    assert len(linked_viewbox.addedItems) == 0

    # Finally, re-add them and verify that clear() will remove both at the same time
    sample_plot.addItem(data_item_one)
    sample_plot.addItem(data_item_two)
    sample_plot.clear()
    assert len(sample_plot.items) == 0
    assert len(sample_plot.dataItems) == 0
    assert len(linked_viewbox.addedItems) == 0


def test_get_view_box_for_axis_valid_axis_with_link(sample_plot):
    """
    Test that if we pass a valid axis name that has a non-None linked ViewBox,
    getViewBoxForAxis returns that specific ViewBox.
    """
    axis_name = "Test Axis"
    test_axis = AxisItem("left")
    sample_plot.addAxis(test_axis, axis_name)

    linked_vb = test_axis.linkedView()
    assert linked_vb is not None, "Expected newly added axis to have a linked ViewBox."

    returned_vb = sample_plot.getViewBoxForAxis(axis_name)
    assert returned_vb == linked_vb, "getViewBoxForAxis should return the specific ViewBox linked to the axis."


def test_get_view_box_for_axis_valid_axis_no_link(sample_plot):
    """
    Test that if the axis name is valid but its linkedView() returns None,
    getViewBoxForAxis will return the main ViewBox instead.
    """
    axis_name = "Test Axis No Link"
    test_axis = AxisItem("left")
    sample_plot.addAxis(test_axis, axis_name)

    with patch.object(test_axis, "linkedView", return_value=None):
        returned_vb = sample_plot.getViewBoxForAxis(axis_name)
        main_vb = sample_plot.getViewBox()
        assert returned_vb == main_vb, "If linkedView() is None, getViewBoxForAxis should return the main ViewBox."


def test_get_view_box_for_axis_invalid_axis(sample_plot):
    """
    Test that if the axis name doesn't exist in the plot's axes dictionary,
    getViewBoxForAxis returns the main ViewBox.
    """
    axis_name = "NonExistentAxis"
    returned_vb = sample_plot.getViewBoxForAxis(axis_name)
    main_vb = sample_plot.getViewBox()
    assert returned_vb == main_vb, "An invalid axis name should cause getViewBoxForAxis to return the main ViewBox."
