import pytest
import logging
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
    qtbot.addWidget(base_plotcurve_item)

    assert base_plotcurve_item._color == color if color else QColor("white")
    assert base_plotcurve_item._pen.color() == color if color else QColor("white")
    assert base_plotcurve_item._pen.style() == line_style if line_style else Qt.SolidLine
    assert base_plotcurve_item._pen.width() == line_width if line_width else 1
    assert base_plotcurve_item.opts["name"] == name


def test_baseplotcurveitem_properties_and_setters(qtbot):
    base_plotcurve_item = BasePlotCurveItem()
    qtbot.addWidget(base_plotcurve_item)

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
    qtbot.addWidget(base_plotcurve_item)
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
