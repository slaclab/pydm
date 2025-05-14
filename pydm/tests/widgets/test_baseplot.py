import pytest
import logging
import numpy as np
from unittest.mock import MagicMock

from pydm.widgets.timeplot import PyDMTimePlot
from pydm.widgets.waveformplot import PyDMWaveformPlot, WaveformCurveItem
from qtpy.QtGui import QColor, QFont
from qtpy.QtCore import QTimer, Qt, QPointF
from qtpy.QtWidgets import QWidget

from collections import OrderedDict
from pydm.widgets.baseplot import BasePlotCurveItem, BasePlot


logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "color, line_style, line_width, name",
    [(QColor("red"), Qt.SolidLine, 1, "test_name"), (None, Qt.DashLine, 10, ""), (None, None, None, None)],
)
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

    base_plotcurve_item.symbol = "o"
    assert base_plotcurve_item.symbol == "o"
    assert base_plotcurve_item._pen.color() == base_plotcurve_item._color

    # The invalid symbol 'A' should be ejected
    base_plotcurve_item.symbol = "A"
    assert base_plotcurve_item.symbol == "o"
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
    assert base_plot._redraw_rate == 1
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
    """Test that when we add curves while specifying new y-axis names for them, those axes are created and
    added to the plot correctly. Also confirm that adding a curve to an existing axis works properly."""
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
    base_plot.addCurve(plot_curve_item_1, y_axis_name="Test Axis 1")
    base_plot.addCurve(plot_curve_item_2, y_axis_name="Test Axis 2")
    base_plot.addCurve(plot_curve_item_3, y_axis_name="Test Axis 3")
    base_plot.addCurve(plot_curve_item_4, y_axis_name="Test Axis 1")
    qtbot.addWidget(base_plot)

    # There should be 4 axes (the x-axis, and the 3 new y-axes we have just created)
    assert len(base_plot.plotItem.axes) == 4

    # Verify the 4 axes are indeed the ones we expect
    assert "bottom" in base_plot.plotItem.axes
    assert "Test Axis 1" in base_plot.plotItem.axes
    assert "Test Axis 2" in base_plot.plotItem.axes
    assert "Test Axis 3" in base_plot.plotItem.axes

    # Verify their orientations were set correctly
    assert base_plot.plotItem.axes["Test Axis 1"]["item"].orientation == "left"
    assert base_plot.plotItem.axes["Test Axis 2"]["item"].orientation == "left"
    assert base_plot.plotItem.axes["Test Axis 3"]["item"].orientation == "left"

    # Verify the curves got assigned to the correct axes
    assert len(base_plot.plotItem.axes["Test Axis 1"]["item"]._curves) == 2
    assert len(base_plot.plotItem.axes["Test Axis 2"]["item"]._curves) == 1
    assert len(base_plot.plotItem.axes["Test Axis 3"]["item"]._curves) == 1


def test_baseplot_no_added_y_axes(qtbot):
    """Confirm that if the user does not name or create any new y-axes, the plot will still work just fine"""
    parent = QWidget()
    qtbot.addWidget(parent)

    base_plot = BasePlot(parent)
    base_plot.clear()

    assert base_plot.parent() == parent

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
    assert "bottom" in base_plot.plotItem.axes
    assert "left" in base_plot.plotItem.axes
    assert "top" in base_plot.plotItem.axes
    assert "right" in base_plot.plotItem.axes

    # Verify their orientations were not changed in any way
    assert base_plot.plotItem.axes["bottom"]["item"].orientation == "bottom"
    assert base_plot.plotItem.axes["left"]["item"].orientation == "left"
    assert base_plot.plotItem.axes["top"]["item"].orientation == "top"
    assert base_plot.plotItem.axes["right"]["item"].orientation == "right"

    # This prevents pyside6 from deleting the internal c++ object
    # ("Internal C++ object (PyDMDateTimeLabel) already deleted")
    parent.deleteLater()
    base_plot.deleteLater()


def test_timeplot_add_multiple_axes(qtbot):
    """Similar to the multiple y axes test above, but this one creates the new axes first, and invokes the setters
    for the curves and axes directly, which is exactly what would happen in the flow initiated from designer.
    Since the base plot has no method for setting curves itself, we instead use a time plot."""
    time_plot = PyDMTimePlot()

    # A list of axes represented in json that would be auto-generated by a user creating a new plot
    # We have 4 unique axes, 2 on the left side of the plot and 2 on the right
    json_axes = [
        '{"name": "Axis 1", "orientation": "left", "minRange": -1.0, "maxRange": 1.0, "autoRange": true}',
        '{"name": "Axis 2", "orientation": "right", "minRange": -1.0, "maxRange": 1.0, "autoRange": true}',
        '{"name": "Axis 3", "orientation": "right", "minRange": -0.5, "maxRange": 0.5, "autoRange": false}',
        '{"name": "Axis 4", "orientation": "left", "minRange": -1.0, "maxRange": 1.0, "autoRange": true}',
    ]

    time_plot.setYAxes(json_axes)

    # There should be 5 axes, the x-axis and the 4 we have just created
    assert len(time_plot.plotItem.axes) == 5

    # Verify the 5 axes are indeed the ones we expect
    assert "bottom" in time_plot.plotItem.axes
    assert "Axis 1" in time_plot.plotItem.axes
    assert "Axis 2" in time_plot.plotItem.axes
    assert "Axis 3" in time_plot.plotItem.axes
    assert "Axis 4" in time_plot.plotItem.axes

    # Verify their orientations were set correctly
    assert time_plot.plotItem.axes["bottom"]["item"].orientation == "bottom"
    assert time_plot.plotItem.axes["Axis 1"]["item"].orientation == "left"
    assert time_plot.plotItem.axes["Axis 2"]["item"].orientation == "right"
    assert time_plot.plotItem.axes["Axis 3"]["item"].orientation == "right"
    assert time_plot.plotItem.axes["Axis 4"]["item"].orientation == "left"

    # Also confirm that setting a specific range on an axis works
    assert time_plot.plotItem.axes["Axis 3"]["item"].min_range == -0.5
    assert time_plot.plotItem.axes["Axis 3"]["item"].max_range == 0.5
    assert time_plot.plotItem.axes["Axis 3"]["item"].auto_range is False

    # Now let's connect 5 curves with these axes. Sine and cosine will share an axis, the rest will get their own
    json_curves = [
        '{"channel": "ca://MTEST:SinVal", "name": "Sine", "color": "white", "lineStyle": 1, '
        '"lineWidth": 1, "symbol": null, "symbolSize": 10, "yAxisName": "Axis 1"}',
        '{"channel": "ca://MTEST:CosVal", "name": "Cosine", "color": "red", "lineStyle": 1, '
        '"lineWidth": 1, "symbol": null, "symbolSize": 10, "yAxisName": "Axis 1"}',
        '{"channel": "ca://MTEST:MeanValue", "name": "Orange Value", "color": "orange", "lineStyle": 1, '
        '"lineWidth": 1, "symbol": null, "symbolSize": 10, "yAxisName": "Axis 2"}',
        '{"channel": "ca://MTEST:MaxValue", "name": "Green Value", "color": "forestgreen", "lineStyle": 1, '
        '"lineWidth": 1, "symbol": null, "symbolSize": 10, "yAxisName": "Axis 3"}',
        '{"channel": "ca://MTEST:MinValue", "name": "Yellow Value", "color": "yellow", "lineStyle": 1, '
        '"lineWidth": 1, "symbol": null, "symbolSize": 10, "yAxisName": "Axis 4"}',
    ]
    time_plot.setCurves(json_curves)

    # Verify the curves got assigned to the correct axes
    assert len(time_plot.curves) == 5
    assert len(time_plot.plotItem.axes["Axis 1"]["item"]._curves) == 2
    assert len(time_plot.plotItem.axes["Axis 2"]["item"]._curves) == 1
    assert len(time_plot.plotItem.axes["Axis 3"]["item"]._curves) == 1
    assert len(time_plot.plotItem.axes["Axis 4"]["item"]._curves) == 1


def test_multiaxis_plot_no_designer_flow(qtbot):
    """Similar to the tests above except don't use the qt designer flow at all. Verify the correct axes get
    added to the plot in this case as well."""

    # Setup a plot with three test data channels, 2 assigned to the same axis, the third to its own
    plot = PyDMTimePlot()
    plot.addYChannel(y_channel="ca://test_channel", yAxisName="Axis 1")
    plot.addYChannel(y_channel="ca://test_channel_2", yAxisName="Axis 1")
    plot.addYChannel(y_channel="ca://test_channel_3", yAxisName="Axis 2")

    # There should be 5 axes, the 3 we definitely expect ('Axis 1' 'Axis 2', and the default 'bottom' x-axis). But
    # pyqtgraph also adds a mirrored 'right' axis and a mirrored 'top' axis. These do not display by
    # default so we'll keep them.
    assert len(plot.plotItem.axes) == 5
    assert "bottom" in plot.plotItem.axes
    assert "Axis 1" in plot.plotItem.axes
    assert "Axis 2" in plot.plotItem.axes
    assert "right" in plot.plotItem.axes
    assert "top" in plot.plotItem.axes
    assert len(plot.plotItem.axes["Axis 1"]["item"]._curves) == 2
    assert len(plot.plotItem.axes["Axis 2"]["item"]._curves) == 1

    # Now check the case where no new y-axis name is specified for any of the new channels.
    plot = PyDMTimePlot()
    plot.addYChannel(y_channel="ca://test_channel")
    plot.addYChannel(y_channel="ca://test_channel_2")
    plot.addYChannel(y_channel="ca://test_channel_3")

    # Since no new axes were created, we just have the default ones provided by pyqtgraph
    assert len(plot.plotItem.axes) == 4
    assert "bottom" in plot.plotItem.axes
    assert "left" in plot.plotItem.axes
    assert "right" in plot.plotItem.axes
    assert "top" in plot.plotItem.axes


def test_reset_autorange(qtbot):
    """Verify that resetting the autorange properties of the plot works as expected"""
    plot = PyDMWaveformPlot()
    plot.setAutoRangeX(False)
    plot.setAutoRangeY(False)

    # Quick check to ensure autorange was turned off
    for view in plot.getPlotItem().stackedViews:
        assert not any(view.state["autoRange"])

    plot.resetAutoRangeX()
    plot.resetAutoRangeY()

    for view in plot.getPlotItem().stackedViews:
        assert all(view.state["autoRange"])


class DummyPlotDataItem:
    """Simulate a valid PlotDataItem."""

    pass


class DummyTextItem:
    """
    A dummy text item to simulate the TextItem created in initializeCurveLabels.
    It records calls to setPos, setAnchor, setFont, setText and tracks its visibility.
    """

    def __init__(self, text, color, border, fill):
        self.text = text
        self.color = color
        self.border = border
        self.fill = fill
        self._pos = None
        self._anchor = None
        self._font = None
        self._text = text
        self.visible = True

    def setPos(self, x, y=None):
        if y is None:
            self._pos = x
        else:
            self._pos = (x, y)

    def setAnchor(self, anchor):
        self._anchor = anchor

    def setFont(self, font):
        self._font = font

    def setText(self, text):
        self._text = text

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False


class DummyViewBox:
    """
    A dummy view box for use in updateLabel. Its mapSceneToView method returns
    a dummy point whose x() value we control.
    """

    def __init__(self, mapped_x=0):
        self.mapped_x = mapped_x

    def addItem(self, item):
        pass

    def mapSceneToView(self, point):
        dummy = MagicMock()
        dummy.x.return_value = self.mapped_x
        return dummy


class DummyPlotItem:
    """
    A dummy plot item that provides:
      - listDataItems() to supply data items.
      - removeItem(item) to simulate removal of an item.
      - getViewBoxForAxis(axis_name) to return a dummy view box.
      - An attribute axes (a list) and a vb (default view box).
    """

    def __init__(self, data_items=None, axes=None, viewbox=None):
        self._data_items = data_items if data_items is not None else []
        self.axes = axes if axes is not None else []
        self._viewbox = viewbox if viewbox is not None else DummyViewBox()

    def listDataItems(self):
        return self._data_items

    def removeItem(self, item):
        pass

    def getViewBoxForAxis(self, axis_name):
        return DummyViewBox(mapped_x=2.5)

    @property
    def vb(self):
        return self._viewbox


class DummyWidget:
    def __init__(self):
        self.textItems = {}  # Maps curves to labels.
        self.init_label = False
        self.plotItem = DummyPlotItem()

    def clearCurveLabels(self) -> None:
        """
        Remove all existing curve labels from the plot and clear the textItems dictionary.
        """
        if hasattr(self, "textItems"):
            for label in list(self.textItems.values()):
                self.plotItem.removeItem(label)
            self.textItems.clear()
            self.init_label = True

    def initializeCurveLabels(self, font: str = "arial", font_size: int = 8) -> None:
        """
        Create a TextItem for each PlotDataItem in the plot and stores them in self.textItems.
        """
        self.clearCurveLabels()
        self.init_label = False

        for item in self.plotItem.listDataItems():
            if not isinstance(item, DummyPlotDataItem):
                continue

            label = DummyTextItem(text="No data", color="w", border="dummy_pen", fill="dummy_brush")

            label.setPos(0, 0)
            label.setAnchor((0.5, 0.5))
            label.setFont(QFont(font, font_size))

            self.textItems[item] = label

    def getViewBox(self):
        """
        Return a dummy view box for use in updateLabel.
        """
        return DummyViewBox(mapped_x=2.3)

    def updateLabel(self, scene_x: float, scene_y: float) -> None:
        """
        Update the label for each curve based on the scene coordinates.
        """
        if self.init_label:
            self.initializeCurveLabels()
            self.init_label = False

        for curve, label in self.textItems.items():
            if hasattr(curve, "y_axis_name") and curve.y_axis_name in self.plotItem.axes:
                curve_vb = self.plotItem.getViewBoxForAxis(curve.y_axis_name)
            else:
                curve_vb = self.getViewBox()

            curve_vb.addItem(label)
            mouse_point_in_curve_vb = curve_vb.mapSceneToView(QPointF(scene_x, scene_y))
            x_val = mouse_point_in_curve_vb.x()

            xData, yData = curve.getData()
            if (
                xData is None
                or yData is None
                or len(xData) == 0
                or not np.isfinite(x_val)
                or x_val < xData[0]
                or x_val > xData[-1]
            ):
                label.hide()
                continue

            label.show()
            idx = np.searchsorted(xData, x_val, side="right") - 1
            idx = max(0, min(idx, len(yData) - 1))
            real_x = xData[idx]
            real_y = yData[idx]

            if not (np.isfinite(real_x) and np.isfinite(real_y)):
                label.hide()
                continue
            else:
                label.show()

            x_str = f"{real_x:.2f}"
            y_str = f"{real_y:.2f}"
            label.setText(f"x={x_str}\ny={y_str}")
            label.setPos(x_val, real_y)

    def getFormattedX(self, real_x: float) -> str:
        """
        Return a string representation for real_x.
        """
        return f"{real_x:.2f}"


# -----------------------------------------------------------------------------
# Pytest Unit Tests
# -----------------------------------------------------------------------------


def test_initializeCurveLabels():
    widget = DummyWidget()
    valid_item = DummyPlotDataItem()
    invalid_item = "not a data item"
    widget.plotItem._data_items = [valid_item, invalid_item]

    widget.initializeCurveLabels(font="Times", font_size=10)

    assert valid_item in widget.textItems
    assert invalid_item not in widget.textItems

    label = widget.textItems[valid_item]
    assert label._pos == (0, 0)
    assert label._anchor == (0.5, 0.5)
    assert isinstance(label._font, QFont)
    assert label._font.family() == "Times"
    assert label._font.pointSize() == 10


def test_clearCurveLabels(monkeypatch):
    widget = DummyWidget()
    dummy_item = DummyPlotDataItem()
    dummy_label = DummyTextItem("No data", "w", "dummy_pen", "dummy_brush")
    widget.textItems = {dummy_item: dummy_label}

    remove_calls = []

    def fake_remove(item):
        remove_calls.append(item)

    monkeypatch.setattr(widget.plotItem, "removeItem", fake_remove)

    widget.clearCurveLabels()
    assert dummy_label in remove_calls
    assert widget.textItems == {}
    assert widget.init_label is True


def test_updateLabel_valid():
    """
    Test updateLabel with a dummy curve that returns valid data.
    """
    widget = DummyWidget()
    widget.init_label = False  # So that initializeCurveLabels is not re-called.

    class DummyCurve:
        def __init__(self, xData, yData):
            self._xData = xData
            self._yData = yData

        def getData(self):
            return self._xData, self._yData

    curve = DummyCurve(np.array([0, 1, 2, 3]), np.array([10, 20, 30, 40]))
    label = DummyTextItem("No data", "w", "dummy_pen", "dummy_brush")
    widget.textItems = {curve: label}

    # When getViewBox() is called, our dummy view box returns x_val = 2.3.
    widget.updateLabel(100.0, 200.0)

    # For x_val = 2.3, np.searchsorted([0,1,2,3], 2.3, side="right") returns 3;
    # subtracting 1 gives index 2. Thus, real_x should be 2 and real_y should be 30.
    expected_text = "x=2.00\ny=30.00"
    expected_pos = (2.3, 30)
    assert label._text == expected_text
    assert label._pos == expected_pos
    assert label.visible is True


def test_updateLabel_invalid_data():
    """
    Test updateLabel with a curve that returns empty data.
    The label should be hidden.
    """
    widget = DummyWidget()
    widget.init_label = False

    class DummyCurve:
        def getData(self):
            return np.array([]), np.array([])

    curve = DummyCurve()
    label = DummyTextItem("No data", "w", "dummy_pen", "dummy_brush")
    widget.textItems = {curve: label}

    widget.updateLabel(100.0, 200.0)
    # Since the data arrays are empty, the label should be hidden.
    assert label.visible is False


def test_getFormattedX():
    widget = DummyWidget()
    result = widget.getFormattedX(3.14159)
    assert result == "3.14"
