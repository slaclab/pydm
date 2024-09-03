import functools
import json
import warnings
from abc import abstractmethod
from qtpy.QtGui import QColor, QBrush, QMouseEvent
from qtpy.QtCore import Signal, Slot, Property, QTimer, Qt, QEvent, QObject, QRect
from qtpy.QtWidgets import QToolTip, QWidget
from .. import utilities
from pyqtgraph import (
    AxisItem,
    PlotWidget,
    PlotDataItem,
    mkPen,
    ViewBox,
    InfiniteLine,
    SignalProxy,
)
from collections import OrderedDict
from typing import Dict, List, Optional, Union
from .base import PyDMPrimitiveWidget, widget_destroyed
from .multi_axis_plot import MultiAxisPlot


class NoDataError(Exception):
    """NoDataError is raised when a curve tries to perform an operation,
    but does not yet have any data."""

    pass


class BasePlotCurveItem(PlotDataItem):
    """
    BasePlotCurveItem represents a single curve in a plot.

    In addition to the parameters listed below, WaveformCurveItem accepts
    keyword arguments for all plot options that pyqtgraph.PlotDataItem accepts.
    Each subclass of ``BasePlotCurveItem`` should have a class attribute
    `_channels` that lets us know the attribute names where we can find
    PyDMChannel objects. This allows us to connect and disconnect these
    connections when appropriate

    Parameters
    ----------
    color : QColor, optional
        The color used to draw the curve line and the symbols.
    lineStyle: Qt.PenStyle, optional
        Style of the line connecting the data points.
        Must be a value from the Qt::PenStyle enum
        (see http://doc.qt.io/qt-5/qt.html#PenStyle-enum).
    lineWidth: int, optional
        Width of the line connecting the data points.
    yAxisName: str, optional
        The name of the axis to link this curve with. Leaving it None will result in the default
        name of 'Axis 1' which may still be modified later if needed.
    **kargs: optional
        PlotDataItem keyword arguments, such as symbol and symbolSize.
    """

    REDRAW_ON_X, REDRAW_ON_Y, REDRAW_ON_EITHER, REDRAW_ON_BOTH = range(4)
    symbols = OrderedDict(
        [
            ("None", None),
            ("Circle", "o"),
            ("Square", "s"),
            ("Triangle", "t"),
            ("Star", "star"),
            ("Pentagon", "p"),
            ("Hexagon", "h"),
            ("X", "x"),
            ("Diamond", "d"),
            ("Plus", "+"),
        ]
    )
    lines = OrderedDict(
        [
            ("NoLine", Qt.NoPen),
            ("Solid", Qt.SolidLine),
            ("Dash", Qt.DashLine),
            ("Dot", Qt.DotLine),
            ("DashDot", Qt.DashDotLine),
            ("DashDotDot", Qt.DashDotDotLine),
        ]
    )

    data_changed = Signal()

    def __init__(
        self,
        color: Optional[QColor] = None,
        lineStyle: Optional[Qt.PenStyle] = None,
        lineWidth: Optional[int] = None,
        yAxisName: Optional[str] = None,
        exists: bool = True,
        **kws,
    ) -> None:
        self._color = QColor("white")
        self._thresholdColor = QColor("white")
        self.exists = exists
        self._pen = mkPen(self._color)
        if lineWidth is not None:
            self._pen.setWidth(lineWidth)
        if lineStyle is not None:
            self._pen.setStyle(lineStyle)
        kws["pen"] = self._pen
        super(BasePlotCurveItem, self).__init__(**kws)
        self.setSymbolBrush(None)
        if color is not None:
            self.color = color

        if yAxisName is None:
            self._y_axis_name = "Axis 1"
        else:
            self._y_axis_name = yAxisName

        # Bar related items will only be set if the user wants to render the plot as a bar graph
        self.bar_width = None
        # Value above or below these thresholds will be drawn in the threshold color on bar graphs
        self.upper_threshold = None
        self.lower_threshold = None
        self.bar_graph_item = None

        if hasattr(self, "channels"):
            self.destroyed.connect(functools.partial(widget_destroyed, self.channels))

    @property
    def color_string(self) -> str:
        """
        A string representation of the color used for the curve.  This string
        will be a hex color code, like #FF00FF, or an SVG spec color name, if
        a name exists for the color.

        Returns
        -------
        str
        """
        return str(utilities.colors.svg_color_from_hex(self.color.name(), hex_on_fail=True))

    @color_string.setter
    def color_string(self, new_color_string: str) -> None:
        """
        A string representation of the color used for the curve.  This string
        will be a hex color code, like #FF00FF, or an SVG spec color name, if
        a name exists for the color.

        Parameters
        -------
        new_color_string: str
            The new string to use for the curve color.
        """
        self.color = QColor(str(new_color_string))

    @property
    def color(self) -> QColor:
        """
        The color used for the curve.

        Returns
        -------
        QColor
        """
        return self._color

    @color.setter
    def color(self, new_color: Union[QColor, str]) -> None:
        """
        The color used for the curve.

        Parameters
        -------
        new_color: QColor or str
            The new color to use for the curve.
            Strings are passed to WaveformCurveItem.color_string.
        """
        if isinstance(new_color, str):
            self.color_string = new_color
            return
        self._color = new_color
        self._pen.setColor(self._color)
        self.setPen(self._pen)
        self.setSymbolPen(self._color)

    @property
    def threshold_color_string(self) -> str:
        """
        A string representation of the threshold color used for the bar graph.  This string
        will be a hex color code, like #FF00FF, or an SVG spec color name, if
        a name exists for the color.

        Returns
        -------
        str
        """
        return str(utilities.colors.svg_color_from_hex(self.threshold_color.name(), hex_on_fail=True))

    @property
    def threshold_color(self) -> QColor:
        """
        The color used for bars exceeding either the upper or lower thresholds.

        Returns
        -------
        QColor
        """
        return self._thresholdColor

    @threshold_color.setter
    def threshold_color(self, new_color: Union[QColor, str]):
        """
        Set the color used for bars exceeding either the upper or lower thresholds.

        Parameters
        -------
        new_color: QColor
        """
        if isinstance(new_color, str):
            new_color = QColor(new_color)
        self._thresholdColor = new_color

    @property
    def y_axis_name(self) -> str:
        """
        Return the name of the y-axis that this curve should be associated with. This allows us to have plots that
        contain multiple y-axes, with each curve assigned to either a unique or shared axis as needed.
        Returns
        -------
        str
        """
        return self._y_axis_name

    @y_axis_name.setter
    def y_axis_name(self, axis_name: str) -> None:
        """
        Set the name of the y-axis that should be associated with this curve.
        Parameters
        ----------
        axis_name: str
        """
        self._y_axis_name = axis_name

    @property
    def stepMode(self) -> str:
        """
        Returns the stepMode of the curve.

        Returns
        -------
        str
            The stepMode for the curve, one of ["center", "left", "right", None]
        """
        return self.opts.get("stepMode", None)

    @stepMode.setter
    def stepMode(self, new_step: str) -> None:
        """
        Set a new stepMode for the curve. Options are below:
        - "" or None: Draw lines directly from y-value to y-value.
        - "left" or "right": Draw the step with the associated y-value
        to the left or right. Ensure that `len(x) == len(y)`
        - "center": Draw the step with the associated y-value in the center
        of the step. Ensure that `len(x) == len(y) + 1`

        Parameters
        ----------
        new_step : str
            The new stepMode for the curve, can be one of
            ["center", "left", "right", None]
        """
        if new_step == self.stepMode:
            return
        self.setData(stepMode=new_step)
        self.redrawCurve()

    @property
    def lineStyle(self) -> Qt.PenStyle:
        """
        Return the style of the line connecting the data points.
        Must be a value from the Qt::PenStyle enum
        (see http://doc.qt.io/qt-5/qt.html#PenStyle-enum).

        Returns
        -------
        Qt.PenStyle
        """
        return self._pen.style()

    @lineStyle.setter
    def lineStyle(self, new_style: Qt.PenStyle) -> None:
        """
        Set the style of the line connecting the data points.
        Must be a value from the Qt::PenStyle enum
        (see http://doc.qt.io/qt-5/qt.html#PenStyle-enum).

        Parameters
        -------
        new_style: Qt.PenStyle
        """
        if new_style in self.lines.values():
            self._pen.setStyle(new_style)
            self.setPen(self._pen)

    @property
    def lineWidth(self) -> int:
        """
        Return the width of the line connecting the data points.

        Returns
        -------
        int
        """
        return self._pen.width()

    @lineWidth.setter
    def lineWidth(self, new_width: int) -> None:
        """
        Set the width of the line connecting the data points.

        Parameters
        -------
        new_width: int
        """
        self._pen.setWidth(int(new_width))
        self.setPen(self._pen)

    @property
    def symbol(self) -> Union[str, None]:
        """
        The single-character code for the symbol drawn at each datapoint.

        See the documentation for pyqtgraph.PlotDataItem for possible values.

        Returns
        -------
        str or None
        """
        return self.opts["symbol"]

    @symbol.setter
    def symbol(self, new_symbol: Union[str, None]) -> None:
        """
        The single-character code for the symbol drawn at each datapoint.

        See the documentation for pyqtgraph.PlotDataItem for possible values.

        Parameters
        -------
        new_symbol: str or None
        """
        if new_symbol in self.symbols.values():
            self.setSymbol(new_symbol)
            self.setSymbolPen(self._color)

    @property
    def symbolSize(self) -> int:
        """
        Return the size of the symbol to represent the data.

        Returns
        -------
        int
        """
        return self.opts["symbolSize"]

    @symbolSize.setter
    def symbolSize(self, new_size: int) -> None:
        """
        Set the size of the symbol to represent the data.

        Parameters
        -------
        new_size: int
        """
        self.setSymbolSize(int(new_size))

    def setBarGraphInfo(
        self,
        bar_width: Optional[float] = 1.0,
        upper_threshold: Optional[float] = None,
        lower_threshold: Optional[float] = None,
        color: Optional[QColor] = None,
    ) -> None:
        """
        Set the attributes associated with displaying a plot as a bar graph. These will only be set
        if the plot is to be rendered as a bar graph. And any or all of them may be omitted even if it
        is a bar graph. Omitting color parameters will result in the plot displaying a uniform color.

        Parameters
        ----------
        bar_width: float, optional
            The width of all bars displayed on the plot
        upper_threshold: float, optional
            Any bar above this value will be drawn in the threshold color
        lower_threshold: float, optional
            Any bar below this value will be drawn in the threshold color.
        color: QColor, optional
            The color to draw bars exceeding either threshold in.
        """
        self.bar_width = bar_width
        self.upper_threshold = upper_threshold
        self.lower_threshold = lower_threshold
        self.threshold_color = color

    def to_dict(self) -> OrderedDict:
        """
        Returns an OrderedDict representation with values for all properties
        needed to recreate this curve.

        Returns
        -------
        OrderedDict
        """
        return OrderedDict(
            [
                ("name", self.name()),
                ("color", self.color_string),
                ("lineStyle", self.lineStyle),
                ("lineWidth", self.lineWidth),
                ("symbol", self.symbol),
                ("symbolSize", self.symbolSize),
                ("yAxisName", self.y_axis_name),
                ("barWidth", self.bar_width),
                ("upperThreshold", self.upper_threshold),
                ("lowerThreshold", self.lower_threshold),
                ("thresholdColor", self.threshold_color_string),
            ]
        )

    @abstractmethod
    def redrawCurve(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class BasePlotAxisItem(AxisItem):
    """
    BasePlotAxisItem represents a single axis in a plot.

    Parameters
    ----------
    name: str
        The name of the axis
    orientation: str, optional
        The orientation of this axis. The default for this value is 'left'. Must be set to either 'right', 'top',
        'bottom', or 'left'. See: https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/axisitem.html
    label: str, optional
        The label to be displayed along the axis
    minRange: float, optional
        The minimum value to be displayed on this axis
    maxRange: float, optional
        The maximum value to be displayed on this axis
    autoRange: bool, optional
        Whether or not this axis should automatically update its range as it receives new data
    logMode: bool, optional
        If true, this axis will start in logarithmic mode, will be linear otherwise
    **kws: optional
        Extra arguments for CSS style options for this axis
    """

    log_mode_updated = Signal(str, bool)
    sigXRangeChanged = Signal(object, object)
    sigYRangeChanged = Signal(object, object)
    axis_orientations = OrderedDict([("Left", "left"), ("Right", "right")])

    def __init__(
        self,
        name: str,
        orientation: Optional[str] = "left",
        label: Optional[str] = None,
        minRange: Optional[float] = -1.0,
        maxRange: Optional[float] = 1.0,
        autoRange: Optional[bool] = True,
        logMode: Optional[bool] = False,
        **kws,
    ) -> None:
        super(BasePlotAxisItem, self).__init__(orientation, **kws)
        self._curves: List[BasePlotCurveItem] = []
        self._name = name
        self._orientation = orientation
        self._label = label
        self._auto_range = autoRange
        self._log_mode = logMode
        self.setRange(minRange, maxRange)

    def linkToView(self, view):
        if oldView := self.linkedView():
            oldView.sigXRangeChanged.disconnect(self.sigXRangeChanged.emit)
            oldView.sigYRangeChanged.disconnect(self.sigYRangeChanged.emit)
        view.sigXRangeChanged.connect(self.sigXRangeChanged.emit)
        view.sigYRangeChanged.connect(self.sigYRangeChanged.emit)
        super().linkToView(view)

    @property
    def name(self) -> str:
        """
        Return the name of the axis

        Returns
        -------
        str
        """
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        """
        Set the name of the axis

        Parameters
        ----------
        name: str
        """
        if name == self._name:
            return
        self.parentItem().change_axis_name(self._name, name)
        self._name = name

    @property
    def orientation(self) -> str:
        """
        Return the orientation of the y-axis this curve is associated with. Will be 'left', 'right', 'bottom', or 'top'
        See: https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/axisitem.html

        Returns
        -------
        str
        """
        return self._orientation

    @orientation.setter
    def orientation(self, orientation: str) -> None:
        """
        Set the orientation of the y-axis this curve is associated with. Must be 'left', 'right', 'bottom', or 'top'

        Parameters
        ----------
        orientation: str
        """
        self._orientation = orientation

    @property
    def label_text(self) -> str:
        """Return the label to be displayed along this axis."""
        return self._label

    @label_text.setter
    def label_text(self, label: str):
        """Set the label to be displayed along this axis"""
        self._label = label
        self.setLabel(self._label)

    @property
    def min_range(self) -> float:
        """
        Return the minimum range displayed on this axis

        Returns
        -------
        float
        """
        return self.range[0]

    @min_range.setter
    def min_range(self, min_range: float) -> None:
        """
        Set the minimum range for this axis

        Parameters
        ----------
        min_range: float
        """
        self.linkedView().setYRange(min_range, self.range[1], padding=0)

    @property
    def max_range(self) -> float:
        """
        Return the maximum range displayed on this axis

        Returns
        -------
        float
        """
        return self.range[1]

    @max_range.setter
    def max_range(self, max_range: float) -> None:
        """
        Set the maximum range for this axis

        Parameters
        ----------
        max_range: float
        """
        self.linkedView().setYRange(self.range[0], max_range, padding=0)

    @property
    def auto_range(self) -> bool:
        """
        Return whether or not this axis should automatically update its range when receiving new data

        Returns
        -------
        bool
        """
        return self._auto_range

    @auto_range.setter
    def auto_range(self, auto_range: bool) -> None:
        """
        Set whether or not this axis should automatically update its range when receiving new data

        Parameters
        ----------
        auto_range: bool
        """
        self._auto_range = auto_range

    @property
    def log_mode(self) -> bool:
        """
        Return whether or not this axis is using logarithmic mode

        Returns
        -------
        bool
        """
        return self._log_mode

    @log_mode.setter
    def log_mode(self, log_mode: bool) -> None:
        """
        Set whether or not this axis is using logarithmic mode

        Parameters
        ----------
        log_mode: bool
        """
        self._log_mode = log_mode
        self.setLogMode(x=False, y=log_mode)
        self.log_mode_updated.emit(self.name, log_mode)

    def setHidden(self, shouldHide: bool):
        """Set an axis to hide/show and do the same for all of its connected curves"""
        if shouldHide:
            for curve in self._curves:
                curve.hide()
            self.hide()
        else:
            for curve in self._curves:
                curve.show()
            self.show()

    def to_dict(self) -> OrderedDict:
        """
        Returns an OrderedDict representation with values for all properties
        needed to recreate this axis.

        Returns
        -------
        OrderedDict
        """
        return OrderedDict(
            [
                ("name", self._name),
                ("orientation", self._orientation),
                ("label", self._label),
                ("minRange", self.range[0]),
                ("maxRange", self.range[1]),
                ("autoRange", self._auto_range),
                ("logMode", self._log_mode),
            ]
        )


class BasePlot(PlotWidget, PyDMPrimitiveWidget):
    crosshair_position_updated = Signal(float, float)
    """
    BasePlot is the parent class for all specific types of PyDM plots. It is built on top of the
    pyqtgraph plotting library.

    Parameters
    ----------
    parent : QWidget, optional
        The parent of this widget.
    background: str, optional
        The background color for the plot.  Accepts any arguments that pyqtgraph.mkColor will accept.
    axisItems: dict, optional
        A mapping from axis name (str) to pyqtgraph AxisItem for each axis to be added to the plot. If
        not specified, the default pyqtgraph axis items (top, bottom, left, right) will be used
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        background: Optional[str] = "default",
        axisItems: Optional[Dict[str, AxisItem]] = None,
    ) -> None:
        # First create a custom MultiAxisPlot to pass to the base PlotWidget class to support multiple y axes. Note
        # that this plot will still function just fine in the case the user doesn't need additional y axes.
        plotItem = MultiAxisPlot(axisItems=axisItems)
        if axisItems is None or "left" not in axisItems:
            # The pyqtgraph PlotItem.setAxisItems() will always add an an AxisItem called left whether you asked
            # it to or not. This will clear it if not specifically requested.
            plotItem.removeAxis("left")
        super(BasePlot, self).__init__(parent=parent, background=background, plotItem=plotItem)

        self.plotItem = plotItem
        self.plotItem.hideButtons()
        self._auto_range_x = None
        self.setAutoRangeX(True)
        self._auto_range_y = None
        self.setAutoRangeY(True)
        self._min_x = 0.0
        self._max_x = 1.0
        self._min_y = 0.0
        self._max_y = 1.0
        self._show_x_grid = None
        self.setShowXGrid(False)
        self._show_y_grid = None
        self.setShowYGrid(False)

        self._show_right_axis = False

        self.redraw_timer = QTimer(self)
        self.redraw_timer.timeout.connect(self.redrawPlot)

        self._redraw_rate = 1  # Redraw at 1 Hz by default.
        self.maxRedrawRate = self._redraw_rate
        self._axes = []
        self._curves: List[BasePlotCurveItem] = []
        self._x_labels = []
        self._y_labels = []
        self._title = None
        self._show_legend = False
        self._legend = self.addLegend()
        self._legend.hide()

        # Drawing crosshair on the ViewBox
        self.vertical_crosshair_line = None
        self.horizontal_crosshair_line = None
        self.crosshair_movement_proxy = None

        # Mouse mode to 1 button (left button draw rectangle for zoom)
        self.plotItem.getViewBox().setMouseMode(ViewBox.RectMode)

        if self.getAxis("bottom") is not None:
            # Disables unexpected axis tick behavior described here:
            # https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/axisitem.html
            self.getAxis("bottom").enableAutoSIPrefix(False)

        if utilities.is_qt_designer():
            self.installEventFilter(self)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Display a tool tip upon mousing over the plot in Qt designer explaining how to edit curves on it"""
        ret = super(BasePlot, self).eventFilter(obj, event)
        if utilities.is_qt_designer():
            if event.type() == QEvent.Enter:
                QToolTip.showText(
                    self.mapToGlobal(self.rect().center()),
                    'Edit plot curves via Right-Click and select "Edit Curves..."',
                    self,
                    QRect(0, 0, 200, 100),
                    4000,
                )
        else:
            # Somehow super here is not invoking the PyDMPrimitiveWidget
            # eventFilter
            ret = PyDMPrimitiveWidget.eventFilter(self, obj, event)

        return ret

    def addCurve(
        self,
        plot_data_item: BasePlotCurveItem,
        curve_color: Optional[QColor] = None,
        y_axis_name: Optional[str] = None,
    ):
        """
        Adds a curve to this plot.

        If the y axis parameters are specified, either link this curve to an
        existing axis if that axis is already part of this plot, or create a
        new one and link the curve to it.

        Parameters
        ----------
        plot_data_item: BasePlotCurveItem
            The curve to add to this plot
        curve_color: QColor, optional
            The color to draw the curve and axis label in
        y_axis_name: str, optional
            The name of the axis to link the curve with. If this is the first
            time seeing this name, then a new axis will be created for it.
        """

        if curve_color is None:
            curve_color = utilities.colors.default_colors[len(self._curves) % len(utilities.colors.default_colors)]
            plot_data_item.color_string = curve_color

        self._curves.append(plot_data_item)

        if y_axis_name is None:
            if utilities.is_qt_designer():
                # If we are just in designer, add an axis that will not conflict with the pyqtgraph default
                self.addAxis(plot_data_item=plot_data_item, name="Axis 1", orientation="left")
            # If not in designer and the user did not name the axis, use the pyqtgraph default one named left
            elif "left" not in self.plotItem.axes:
                self.addAxis(plot_data_item=plot_data_item, name="left", orientation="left")
            else:
                self.plotItem.linkDataToAxis(plot_data_item, "left")
        elif y_axis_name in self.plotItem.axes:
            # If the user has chosen an axis that already exists for this curve, simply link the data to that axis
            self.plotItem.linkDataToAxis(plot_data_item, y_axis_name)
        else:
            # Otherwise we create a brand new axis for this data
            self.addAxis(plot_data_item, y_axis_name, "left")
        self.redraw_timer.start()
        # Connect channels
        for chan in plot_data_item.channels():
            if chan:
                chan.connect()

    def addAxis(
        self,
        plot_data_item: BasePlotCurveItem,
        name: str,
        orientation: str,
        label: Optional[str] = None,
        min_range: Optional[float] = -1.0,
        max_range: Optional[float] = 1.0,
        enable_auto_range: Optional[bool] = True,
        log_mode: Optional[bool] = False,
    ):
        """
        Create an AxisItem with the input name and orientation, and add it to
        this plot.

        Parameters
        ----------
        plot_data_item: BasePlotCurveItem
            The curve that will be linked with this new axis
        name: str
            The name that will be assigned to this axis
        orientation: str
            The orientation of this axis, must be in 'left' or 'right'
        label: str, optional
            The label to be displayed along this axis
        min_range: float
            The minimum range to display on the axis
        max_range: float
            The maximum range to display on the axis
        enable_auto_range: bool, optional
            Whether or not to use autorange for this axis. Min and max range will not be respected
            when data goes out of range if this is set to True
        log_mode: bool, optional
            Whether or not this axis should start out in logarithmic mode.

        Raises
        ------
        Exception
            Raised by PyQtGraph if the orientation is not in 'left' or 'right'
        """

        if name in self.plotItem.axes:
            return

        axis = BasePlotAxisItem(
            name=name,
            orientation=orientation,
            label=label,
            minRange=min_range,
            maxRange=max_range,
            autoRange=enable_auto_range,
            logMode=log_mode,
        )
        axis.setLabel(text=label)
        axis.enableAutoSIPrefix(False)
        if plot_data_item is not None:
            plot_data_item.setLogMode(False, log_mode)
        axis.setLogMode(log_mode)
        axis.log_mode_updated.connect(self.setAxisLogMode)
        self._axes.append(axis)
        # If the x axis is just timestamps, we don't want autorange on the x axis
        setXLink = hasattr(self, "_plot_by_timestamps") and self._plot_by_timestamps
        self.plotItem.addAxis(
            axis,
            name=name,
            plotDataItem=plot_data_item,
            setXLink=setXLink,
            enableAutoRangeX=self.getAutoRangeX(),
            enableAutoRangeY=enable_auto_range,
            minRange=min_range,
            maxRange=max_range,
        )

    def removeCurve(self, plot_item: BasePlotCurveItem) -> None:
        """
        Remove the given curve from the plot, disconnecting it from any channels it was connected to

        Parameters
        ----------
        plot_item : BasePlotCurveItem
            The cureve to be removed from this plot
        """
        # Mark it as not existing so all curves that rely on this curve get destroyed as well
        plot_item.exists = False
        if plot_item.y_axis_name in self.plotItem.axes:
            self.plotItem.unlinkDataFromAxis(plot_item)

        self.removeItem(plot_item)
        self._curves.remove(plot_item)
        if len(self._curves) < 1:
            self.redraw_timer.stop()
        # Disconnect channels
        for chan in plot_item.channels():
            if chan:
                chan.disconnect()

    def removeAxisAtIndex(self, axis_index: int) -> None:
        axis = self._axes[axis_index]
        self.plotItem.removeAxis(axis.name)
        self._axes.remove(axis)

    def removeCurveWithName(self, name: str) -> None:
        for curve in self._curves:
            if curve.name() == name:
                self.removeCurve(curve)

    def removeCurveAtIndex(self, index: int) -> None:
        curve_to_remove = self._curves[index]
        self.removeCurve(curve_to_remove)

    def setCurveAtIndex(self, index: int, new_curve: BasePlotCurveItem) -> None:
        old_curve = self._curves[index]
        self._curves[index] = new_curve
        # self._legend.addItem(new_curve, new_curve.name())
        self.removeCurve(old_curve)

    def curveAtIndex(self, index: int) -> BasePlotCurveItem:
        return self._curves[index]

    def curves(self) -> List[BasePlotCurveItem]:
        return self._curves

    def clear(self) -> None:
        """Remove all curves from the plot, as well as all items from the main view box"""
        legend_items = [label.text for (sample, label) in self._legend.items]
        for item in legend_items:
            self._legend.removeItem(item)
        self.plotItem.clear()
        self._curves = []

    def clearAxes(self) -> None:
        """Clear out any added axes on this plot"""
        for axis in self._axes:
            axis.deleteLater()
        self.plotItem.clearAxes()
        self._axes = []

    @Slot()
    def redrawPlot(self) -> None:
        pass

    @Slot(str, bool)
    def setAxisLogMode(self, axis_name: str, log_mode: bool) -> None:
        axis_curves = [c for c in self._curves if c.y_axis_name == axis_name]
        for curve in axis_curves:
            curve.setLogMode(False, log_mode)
        self.plotItem.recomputeAverages()

    def getShowXGrid(self) -> bool:
        """True if showing x grid lines on the plot, False otherwise"""
        return self._show_x_grid

    def setShowXGrid(self, value: bool, alpha: Optional[float] = None) -> None:
        """
        Set the x grid lines on the plot

        Parameters
        ----------
        value : bool
            True if we should show x grid lines, False to hide them
        alpha : float, optional
            The opacity of the grid lines, from 0.0 to 1.0 (strongest), defaults to 0.5
        """
        self._show_x_grid = value
        self.showGrid(x=self._show_x_grid, alpha=alpha)

    def resetShowXGrid(self) -> None:
        self.setShowXGrid(False)

    showXGrid = Property("bool", getShowXGrid, setShowXGrid, resetShowXGrid)

    def getShowYGrid(self) -> bool:
        return self._show_y_grid

    def setShowYGrid(self, value: bool, alpha: Optional[float] = None) -> None:
        """
        Set the y grid lines on the plot

        Parameters
        ----------
        value : bool
            True if we should show y grid lines, False to hide them
        alpha : float, optional
            The opacity of the grid lines, from 0.0 to 1.0 (strongest), defaults to 0.5
        """
        self._show_y_grid = value
        self.showGrid(y=self._show_y_grid, alpha=alpha)

    def resetShowYGrid(self) -> None:
        self.setShowYGrid(False)

    showYGrid = Property("bool", getShowYGrid, setShowYGrid, resetShowYGrid)

    def getBackgroundColor(self) -> QColor:
        return self.backgroundBrush().color()

    def setBackgroundColor(self, color: QColor) -> None:
        if self.backgroundBrush().color() != color:
            self.setBackgroundBrush(QBrush(color))

    backgroundColor = Property(QColor, getBackgroundColor, setBackgroundColor)

    def getAxisColor(self) -> QColor:
        return self.getAxis("bottom")._pen.color()

    def setAxisColor(self, color: QColor) -> None:
        for axis in self.plotItem.axes.values():
            axis["item"].setPen(color)

    axisColor = Property(QColor, getAxisColor, setAxisColor)

    def getYAxes(self) -> List[str]:
        """
        Dump the current list of axes and each axis's settings into a list
        of JSON-formatted strings.

        Returns
        -------
        settings : list
            A list of JSON-formatted strings, each containing a curve's
            settings
        """
        return [json.dumps(axis.to_dict()) for axis in self._axes]

    def getXAxis(self) -> BasePlotAxisItem:
        """Return the plot's X-Axis item."""
        return self.getAxis("bottom")

    def setYAxes(self, new_list: List[str]) -> None:
        """
        Add a list of axes into the graph.

        Parameters
        ----------
        new_list : list
            A list of JSON-formatted strings, each contains an axis and its
            settings
        """
        try:
            new_list = [json.loads(str(i)) for i in new_list]
        except ValueError as e:
            print("Error parsing curve json data: {}".format(e))
            return
        self.clearAxes()
        for d in new_list:
            self.addAxis(
                plot_data_item=None,
                name=d.get("name"),
                orientation=d.get("orientation"),
                label=d.get("label"),
                min_range=d.get("minRange"),
                max_range=d.get("maxRange"),
                enable_auto_range=d.get("autoRange"),
                log_mode=d.get("logMode"),
            )
        if "bottom" in self.plotItem.axes:
            # Ensure the added y axes get the color that was set
            self.setAxisColor(self.getAxis("bottom")._pen.color())
        if self.getShowYGrid() or self.getShowXGrid():
            self.plotItem.updateGrid()

    yAxes = Property("QStringList", getYAxes, setYAxes, designable=False)

    def getBottomAxisLabel(self) -> str:
        return self.getAxis("bottom").labelText

    def getShowRightAxis(self) -> bool:
        """
        Provide whether the right y-axis is being shown.

        Returns
        -------
        bool
            True if the graph shows the right y-axis. False if not.
        """
        return self._show_right_axis

    def setShowRightAxis(self, show: bool) -> None:
        """
        Set whether the graph should show the right y-axis.

        Parameters
        ----------
        show : bool
            True for showing the right axis; False is for not showing.
        """
        if show:
            self.showAxis("right")
        else:
            self.hideAxis("right")
        self._show_right_axis = show

    showRightAxis = Property("bool", getShowRightAxis, setShowRightAxis)

    def getPlotTitle(self) -> str:
        if self._title is None:
            return ""
        return str(self._title)

    def setPlotTitle(self, value: str) -> None:
        self._title = str(value)
        if len(self._title) < 1:
            self._title = None
        self.setTitle(self._title)

    def resetPlotTitle(self) -> None:
        self._title = None
        self.setTitle(self._title)

    title = Property(str, getPlotTitle, setPlotTitle, resetPlotTitle)

    def getXLabels(self) -> List[str]:
        return self._x_labels

    def setXLabels(self, labels: List[str]) -> None:
        if self._x_labels != labels:
            self._x_labels = labels
            label = ""
            if len(self._x_labels) > 0:
                # Hardcoded for now as we only have one axis
                label = self._x_labels[0]
            self.setLabel("bottom", text=label)

    def resetXLabels(self) -> None:
        self._x_labels = []
        self.setLabel("bottom", text="")

    xLabels = Property("QStringList", getXLabels, setXLabels, resetXLabels)

    def getYLabels(self):
        warnings.warn(
            "Y Labels should be retrieved from the AxisItem. See: AxisItem.label or AxisItem.labelText"
            "Example: self.getAxis('Axis Name').labelText",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._y_labels

    def setYLabels(self, labels):
        warnings.warn(
            "Y Labels should now be set on the AxisItem itself. See: AxisItem.setLabel() "
            "Example: self.getAxis('Axis Name').setLabel('Label Name')",
            DeprecationWarning,
            stacklevel=2,
        )
        if self._y_labels != labels:
            self._y_labels = labels
            label = ""
            if len(self._y_labels) > 0:
                # Hardcoded for now as we only have one axis
                label = self._y_labels[0]
            if "left" in self.plotItem.axes:
                self.setLabel("left", text=label)

    def resetYLabels(self):
        warnings.warn(
            "Y Labels should now be set on the AxisItem itself. See: AxisItem.setLabel() "
            "Example: self.getAxis('Axis Name').setLabel('')",
            DeprecationWarning,
            stacklevel=2,
        )
        self._y_labels = []
        self.setLabel("left", text="")

    def getShowLegend(self) -> bool:
        """
        Check if the legend is being shown.

        Returns
        -------
        bool
            True if the legend is displayed on the graph; False if not.
        """
        return self._show_legend

    def setShowLegend(self, value: bool) -> None:
        """
        Set to display the legend on the graph.

        Parameters
        ----------
        value : bool
            True to display the legend; False is not.
        """
        self._show_legend = value
        if self._show_legend:
            if self._legend is None:
                self._legend = self.addLegend()
            else:
                self._legend.show()
        else:
            if self._legend is not None:
                self._legend.hide()

    def resetShowLegend(self) -> None:
        """
        Reset the legend display status to hidden.
        """
        self.setShowLegend(False)

    showLegend = Property(bool, getShowLegend, setShowLegend, resetShowLegend)

    def getAutoRangeX(self) -> Union[bool, float]:
        """
        A return type of bool is a simple yes/no if the x-axis has auto range set. A float
        from 0.0 - 1.0 also means True, but only showing a percentage of the data corresponding to the value.
        """
        return self._auto_range_x

    def setAutoRangeX(self, value: Union[bool, float]) -> None:
        """
        Set the auto range property for the x-axis.

        Parameters
        ----------
        value : bool or float
            False means no autorange, True means show all data. A float between 0.0 and 1.0 means only
            show a percentage of the data (for example, 0.75 = 75% of data will be visible)
        """
        self._auto_range_x = value
        self.plotItem.updateXAutoRange(self._auto_range_x)

    def resetAutoRangeX(self) -> None:
        self.setAutoRangeX(True)

    def getAutoRangeY(self) -> Union[bool, float]:
        """
        A return type of bool is a simple yes/no if the y-axis has auto range set. A float
        from 0.0 - 1.0 also means True, but only showing a percentage of the data corresponding to the value.
        """
        return self._auto_range_y

    def setAutoRangeY(self, value: Union[bool, float]) -> None:
        """
        Set the auto range property for the y-axis.

        Parameters
        ----------
        value : bool or float
            False means no autorange, True means show all data. A float between 0.0 and 1.0 means only
            show a percentage of the data (for example, 0.75 = 75% of data will be visible)
        """
        self._auto_range_y = value
        self.plotItem.updateYAutoRange(self._auto_range_y)

    def resetAutoRangeY(self) -> None:
        self.setAutoRangeY(True)

    def getMinXRange(self) -> float:
        """
        Minimum X-axis value visible on the plot.

        Returns
        -------
        float
        """
        return self.plotItem.viewRange()[0][0]

    def setMinXRange(self, new_min_x_range: float) -> None:
        """
        Set the minimum X-axis value visible on the plot.

        Parameters
        -------
        new_min_x_range : float
        """
        if self._auto_range_x:
            return
        self._min_x = new_min_x_range
        self.plotItem.setXRange(self._min_x, self._max_x, padding=0)

    def getMaxXRange(self) -> float:
        """
        Maximum X-axis value visible on the plot.

        Returns
        -------
        float
        """
        return self.plotItem.viewRange()[0][1]

    def setMaxXRange(self, new_max_x_range: float) -> None:
        """
        Set the Maximum X-axis value visible on the plot.

        Parameters
        -------
        new_max_x_range : float
        """
        if self._auto_range_x:
            return

        self._max_x = new_max_x_range
        self.plotItem.setXRange(self._min_x, self._max_x, padding=0)

    def getMinYRange(self) -> float:
        """
        Minimum Y-axis value visible on the plot.

        Returns
        -------
        float
        """
        return self.plotItem.viewRange()[1][0]

    def setMinYRange(self, new_min_y_range: float) -> None:
        """
        Set the minimum Y-axis value visible on the plot.

        Parameters
        -------
        new_min_y_range : float
        """
        if self._auto_range_y:
            return

        self._min_y = new_min_y_range
        self.plotItem.setYRange(self._min_y, self._max_y, padding=0)

    def getMaxYRange(self) -> float:
        """
        Maximum Y-axis value visible on the plot.

        Returns
        -------
        float
        """
        return self.plotItem.viewRange()[1][1]

    def setMaxYRange(self, new_max_y_range: float) -> None:
        """
        Set the maximum Y-axis value visible on the plot.

        Parameters
        -------
        new_max_y_range : float
        """
        if self._auto_range_y:
            return

        self._max_y = new_max_y_range
        self.plotItem.setYRange(self._min_y, self._max_y, padding=0)

    @Property(bool)
    def mouseEnabledX(self) -> bool:
        """
        Whether or not mouse interactions are enabled for the X-axis.

        Returns
        -------
        bool
        """
        return self.plotItem.getViewBox().state["mouseEnabled"][0]

    @mouseEnabledX.setter
    def mouseEnabledX(self, x_enabled: bool) -> None:
        """
        Whether or not mouse interactions are enabled for the X-axis.

        Parameters
        -------
        x_enabled : bool
        """
        self.plotItem.setMouseEnabled(x=x_enabled)

    @Property(bool)
    def mouseEnabledY(self) -> bool:
        """
        Whether or not mouse interactions are enabled for the Y-axis.

        Returns
        -------
        bool
        """
        return self.plotItem.getViewBox().state["mouseEnabled"][1]

    @mouseEnabledY.setter
    def mouseEnabledY(self, y_enabled: bool) -> None:
        """
        Whether or not mouse interactions are enabled for the Y-axis.

        Parameters
        -------
        y_enabled : bool
        """
        self.plotItem.setMouseEnabled(y=y_enabled)

    @Property(int)
    def maxRedrawRate(self) -> int:
        """
        The maximum rate (in Hz) at which the plot will be redrawn.
        The plot will not be redrawn if there is not new data to draw.

        Returns
        -------
        int
        """
        return self._redraw_rate

    @maxRedrawRate.setter
    def maxRedrawRate(self, redraw_rate: int) -> None:
        """
        The maximum rate (in Hz) at which the plot will be redrawn.
        The plot will not be redrawn if there is not new data to draw.

        Parameters
        -------
        redraw_rate : int
        """
        self._redraw_rate = redraw_rate
        self.redraw_timer.setInterval(int((1.0 / self._redraw_rate) * 1000))

    def pausePlotting(self) -> bool:
        (self.redraw_timer.stop() if self.redraw_timer.isActive() else self.redraw_timer.start())
        return self.redraw_timer.isActive()

    def mouseMoved(self, evt: QMouseEvent) -> None:
        """
        A handler for the crosshair feature. Every time the mouse move, the mouse coordinates are updated, and the
        horizontal and vertical hairlines will be redrawn at the new coordinate. If a PyDMDisplay object is available,
        that display will also have the x- and y- values to update on the UI.

        Parameters
        -------
        evt: MouseEvent
            The mouse event type, from which the mouse coordinates are obtained.
        """
        pos = evt[0]
        if self.sceneBoundingRect().contains(pos):
            mouse_point = self.getViewBox().mapSceneToView(pos)
            self.vertical_crosshair_line.setPos(mouse_point.x())
            self.horizontal_crosshair_line.setPos(mouse_point.y())

            self.crosshair_position_updated.emit(mouse_point.x(), mouse_point.y())

    def enableCrosshair(
        self,
        is_enabled: bool,
        starting_x_pos: float,
        starting_y_pos: float,
        vertical_angle: Optional[float] = 90,
        horizontal_angle: Optional[float] = 0,
        vertical_movable: Optional[bool] = False,
        horizontal_movable: Optional[bool] = False,
    ) -> None:
        """
        Enable the crosshair to be drawn on the ViewBox.

        Parameters
        ----------
        is_enabled : bool
            True is to draw the crosshair, False is to not draw.
        starting_x_pos : float
            The x coordinate where to start the vertical crosshair line.
        starting_y_pos : float
            The y coordinate where to start the horizontal crosshair line.
        vertical_angle : float
            The angle to tilt the vertical crosshair line. Default at 90 degrees.
        horizontal_angle
            The angle to tilt the horizontal crosshair line. Default at 0 degrees.
        vertical_movable : bool
            True if the vertical line can be moved by the user; False is not.
        horizontal_movable
            False if the horizontal line can be moved by the user; False is not.
        """
        if is_enabled:
            self.vertical_crosshair_line = InfiniteLine(
                pos=starting_x_pos, angle=vertical_angle, movable=vertical_movable
            )
            self.horizontal_crosshair_line = InfiniteLine(
                pos=starting_y_pos, angle=horizontal_angle, movable=horizontal_movable
            )

            self.plotItem.addItem(self.vertical_crosshair_line)
            self.plotItem.addItem(self.horizontal_crosshair_line)
            self.crosshair_movement_proxy = SignalProxy(
                self.plotItem.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved
            )
        else:
            if self.vertical_crosshair_line:
                self.plotItem.removeItem(self.vertical_crosshair_line)
            if self.horizontal_crosshair_line:
                self.plotItem.removeItem(self.horizontal_crosshair_line)
            if self.crosshair_movement_proxy:
                # self.crosshair_movement_proxy.disconnect()
                proxy = self.crosshair_movement_proxy
                proxy.block = True
                try:
                    proxy.signal.disconnect(proxy.signalReceived)
                    proxy.sigDelayed.disconnect(proxy.slot)
                except Exception:
                    pass
