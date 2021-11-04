import pytest
import logging

from pydm.widgets.timeplot import PyDMTimePlot
from pydm.widgets.waveformplot import WaveformCurveItem

logger = logging.getLogger(__name__)

from qtpy.QtGui import QColor
from qtpy.QtCore import QTimer, Qt

from collections import OrderedDict
from ...widgets.baseplot import BasePlotCurveItem, BasePlot, NoDataError


@pytest.mark.parametrize("color, line_style, line_width, name", [
    (QColor("red"), Qt.SolidLine, 1, "test_name"),
    (None, Qt.DashLine, 10, ""),
    (None, None, None, None)
])


def test_baseplotcurveitem_construct(qtbot, color, line_style, line_width, name):
    base_plotcurve_item = BasePlotCurveItem(color, line_style, line_width, name=name)

    assert base_plotcurve_item._color == color if color else QColor("white")
    assert base_plotcurve_item._pen.color() == color if color else QColor("white")
    assert base_plotcurve_item._pen.style() == line_style if line_style else Qt.SolidLine
    assert base_plotcurve_item._pen.width() == line_width if line_width else 1
    assert base_plotcurve_item.opts["name"] == name


def test_baseplotcurveitem_properties_and_setters(qtbot):
    base_plotcurve_item = BasePlotCurveItem()

    assert base_plotcurve_item.color_string == "white"

    base_plotcurve_item.color_string = "blue"
    assert base_plotcurve_item.color_string == "blue"

    base_plotcurve_item.color = "green"
    assert base_plotcurve_item.color == QColor("green")

    base_plotcurve_item.color = QColor("orange")
    assert base_plotcurve_item.color == QColor("orange")
    assert base_plotcurve_item.lineStyle == Qt.SolidLine

    base_plotcurve_item.lineStyle = Qt.DashLine
    assert base_plotcurve_item.lineStyle == Qt.DashLine
    assert base_plotcurve_item.lineWidth == 1

    base_plotcurve_item.lineWidth = 3
    assert base_plotcurve_item.lineWidth == 3

    base_plotcurve_item.symbol = 'o'
    assert base_plotcurve_item.symbol == 'o'
    assert base_plotcurve_item._pen.color() == base_plotcurve_item._color

    # The invalid symbol 'A' should be ejected
    base_plotcurve_item.symbol = "A"
    assert base_plotcurve_item.symbol == 'o'
    base_plotcurve_item.symbolSize = 100
    assert base_plotcurve_item.symbolSize == 100


def test_baseplotcurveitem_to_dict(qtbot):
    base_plotcurve_item = BasePlotCurveItem()
    dictionary = base_plotcurve_item.to_dict()

    assert isinstance(dictionary, OrderedDict)
    assert dictionary["name"] == base_plotcurve_item.name()
    assert dictionary["color"] == base_plotcurve_item.color_string
    assert dictionary["lineStyle"] == base_plotcurve_item.lineStyle
    assert dictionary["lineWidth"] == base_plotcurve_item.lineWidth
    assert dictionary["symbol"] == base_plotcurve_item.symbol
    assert dictionary["symbolSize"] == base_plotcurve_item.symbolSize


def test_baseplot_construct(qtbot):
    base_plot = BasePlot()
    qtbot.addWidget(base_plot)

    assert base_plot.plotItem == base_plot.getPlotItem()
    assert base_plot.plotItem.buttonsHidden is True
    assert base_plot.getAutoRangeX() is True
    assert base_plot.getAutoRangeY() is True
    assert base_plot.getShowXGrid() is False
    assert base_plot.getShowYGrid() is False
    assert isinstance(base_plot.redraw_timer, QTimer)
    assert base_plot._redraw_rate == 30
    assert base_plot.maxRedrawRate == base_plot._redraw_rate
    assert len(base_plot._curves) == 0
    assert base_plot._title is None
    assert base_plot._show_legend is False
    assert base_plot._legend is not None
    assert base_plot._legend.isVisible() is False


def test_baseplot_add_curve(qtbot):
    base_plot = BasePlot()
    qtbot.addWidget(base_plot)


def test_baseplot_multiple_y_axes(qtbot):
    """ Test that when we add curves while specifying new y-axis names for them, those axes are created and
        added to the plot correctly. Also confirm that adding a curve to an existing axis works properly. """
    base_plot = BasePlot()
    base_plot.clear()
    base_plot.clearAxes()

    # Here we add 4 curves to our plot. Because we use 3 unique axis names, we should see that 3 axes are created. The
    # 4th curve is added with an axis name that already exists, so it should get assigned to that axis rather than
    # have a new one created for it.
    plot_curve_item_1 = WaveformCurveItem()
    plot_curve_item_2 = WaveformCurveItem()
    plot_curve_item_3 = WaveformCurveItem()
    plot_curve_item_4 = WaveformCurveItem()
    base_plot.addCurve(plot_curve_item_1, y_axis_name='Test Axis 1')
    base_plot.addCurve(plot_curve_item_2, y_axis_name='Test Axis 2')
    base_plot.addCurve(plot_curve_item_3, y_axis_name='Test Axis 3')
    base_plot.addCurve(plot_curve_item_4, y_axis_name='Test Axis 1')
    qtbot.addWidget(base_plot)

    # There should be 4 axes (the x-axis, and the 3 new y-axes we have just created)
    assert len(base_plot.plotItem.axes) == 4

    # Verify the 4 axes are indeed the ones we expect
    assert 'bottom' in base_plot.plotItem.axes
    assert 'Test Axis 1' in base_plot.plotItem.axes
    assert 'Test Axis 2' in base_plot.plotItem.axes
    assert 'Test Axis 3' in base_plot.plotItem.axes

    # Verify their orientations were set correctly
    assert base_plot.plotItem.axes['Test Axis 1']['item'].orientation == 'left'
    assert base_plot.plotItem.axes['Test Axis 2']['item'].orientation == 'left'
    assert base_plot.plotItem.axes['Test Axis 3']['item'].orientation == 'left'

    # Verify the curves got assigned to the correct axes
    assert base_plot.plotItem.curvesPerAxis['Test Axis 1'] == 2
    assert base_plot.plotItem.curvesPerAxis['Test Axis 2'] == 1
    assert base_plot.plotItem.curvesPerAxis['Test Axis 3'] == 1


def test_baseplot_no_added_y_axes(qtbot):
    """ Confirm that if the user does not name or create any new y-axes, the plot will still work just fine """
    base_plot = BasePlot()
    base_plot.clear()
    base_plot.clearAxes()

    # Add 3 curves to our plot, but don't bother to use any of the y-axis parameters
    # in addCurve() leaving them to their default of None
    plot_curve_item_1 = WaveformCurveItem()
    plot_curve_item_2 = WaveformCurveItem()
    plot_curve_item_3 = WaveformCurveItem()
    base_plot.addCurve(plot_curve_item_1)
    base_plot.addCurve(plot_curve_item_2)
    base_plot.addCurve(plot_curve_item_3)
    qtbot.addWidget(base_plot)

    # There should be 4 axes, the default ones for PyQtGraph (left, bottom, and the mirrored top and right)
    assert len(base_plot.plotItem.axes) == 4

    # Verify their names were not changed in any way
    assert 'bottom' in base_plot.plotItem.axes
    assert 'left' in base_plot.plotItem.axes
    assert 'top' in base_plot.plotItem.axes
    assert 'right' in base_plot.plotItem.axes

    # Verify their orientations were not changed in any way
    assert base_plot.plotItem.axes['bottom']['item'].orientation == 'bottom'
    assert base_plot.plotItem.axes['left']['item'].orientation == 'left'
    assert base_plot.plotItem.axes['top']['item'].orientation == 'top'
    assert base_plot.plotItem.axes['right']['item'].orientation == 'right'


def test_timeplot_add_multiple_axes(qtbot):
    """ Simliar to the multiple y axes test above, but this one creates the new axes first, and invokes the setters
        for the curves and axes directly, which is exactly what would happen in the flow initiated from designer.
        Since the base plot has no method for setting curves itself, we instead use a time plot. """
    time_plot = PyDMTimePlot()

    # A list of axes represented in json that would be auto-generated by a user creating a new plot
    # We have 4 unique axes, 2 on the left side of the plot and 2 on the right
    json_axes = ['{"name": "Axis 1", "orientation": "left", "minRange": -1.0, "maxRange": 1.0, "autoRange": true}',
                 '{"name": "Axis 2", "orientation": "right", "minRange": -1.0, "maxRange": 1.0, "autoRange": true}',
                 '{"name": "Axis 3", "orientation": "right", "minRange": -0.5, "maxRange": 0.5, "autoRange": false}',
                 '{"name": "Axis 4", "orientation": "left", "minRange": -1.0, "maxRange": 1.0, "autoRange": true}']

    time_plot.setYAxes(json_axes)

    # There should be 5 axes, the x-axis and the 4 we have just created
    assert len(time_plot.plotItem.axes) == 5

    # Verify the 5 axes are indeed the ones we expect
    assert 'bottom' in time_plot.plotItem.axes
    assert 'Axis 1' in time_plot.plotItem.axes
    assert 'Axis 2' in time_plot.plotItem.axes
    assert 'Axis 3' in time_plot.plotItem.axes
    assert 'Axis 4' in time_plot.plotItem.axes

    # Verify their orientations were set correctly
    assert time_plot.plotItem.axes['bottom']['item'].orientation == 'bottom'
    assert time_plot.plotItem.axes['Axis 1']['item'].orientation == 'left'
    assert time_plot.plotItem.axes['Axis 2']['item'].orientation == 'right'
    assert time_plot.plotItem.axes['Axis 3']['item'].orientation == 'right'
    assert time_plot.plotItem.axes['Axis 4']['item'].orientation == 'left'

    # Also confirm that setting a specific range on an axis works
    assert time_plot.plotItem.axes['Axis 3']['item'].min_range == -0.5
    assert time_plot.plotItem.axes['Axis 3']['item'].max_range == 0.5
    assert time_plot.plotItem.axes['Axis 3']['item'].auto_range is False

    # Now let's connect 5 curves with these axes. Sine and cosine will share an axis, the rest will get their own
    json_curves = ['{"channel": "ca://MTEST:SinVal", "name": "Sine", "color": "white", "lineStyle": 1, '
                   '"lineWidth": 1, "symbol": null, "symbolSize": 10, "yAxisName": "Axis 1"}',
                   '{"channel": "ca://MTEST:CosVal", "name": "Cosine", "color": "red", "lineStyle": 1, '
                   '"lineWidth": 1, "symbol": null, "symbolSize": 10, "yAxisName": "Axis 1"}',
                   '{"channel": "ca://MTEST:MeanValue", "name": "Orange Value", "color": "orange", "lineStyle": 1, '
                   '"lineWidth": 1, "symbol": null, "symbolSize": 10, "yAxisName": "Axis 2"}',
                   '{"channel": "ca://MTEST:MaxValue", "name": "Green Value", "color": "forestgreen", "lineStyle": 1, '
                   '"lineWidth": 1, "symbol": null, "symbolSize": 10, "yAxisName": "Axis 3"}',
                   '{"channel": "ca://MTEST:MinValue", "name": "Yellow Value", "color": "yellow", "lineStyle": 1, '
                   '"lineWidth": 1, "symbol": null, "symbolSize": 10, "yAxisName": "Axis 4"}']
    time_plot.setCurves(json_curves)

    # Verify the curves got assigned to the correct axes
    assert len(time_plot.curves) == 5
    assert time_plot.plotItem.curvesPerAxis['Axis 1'] == 2
    assert time_plot.plotItem.curvesPerAxis['Axis 2'] == 1
    assert time_plot.plotItem.curvesPerAxis['Axis 3'] == 1
    assert time_plot.plotItem.curvesPerAxis['Axis 4'] == 1
