import functools
from qtpy.QtGui import QColor, QBrush
from qtpy.QtCore import Signal, Slot, Property, QTimer, Qt
from .. import utilities
from pyqtgraph import PlotWidget, PlotDataItem, mkPen, ViewBox, InfiniteLine, SignalProxy, CurvePoint, TextItem
from collections import OrderedDict
from .base import PyDMPrimitiveWidget, widget_destroyed


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
    lineStyle: int, optional
        Style of the line connecting the data points.
        Must be a value from the Qt::PenStyle enum
        (see http://doc.qt.io/qt-5/qt.html#PenStyle-enum).
    lineWidth: int, optional
        Width of the line connecting the data points.
    **kargs: optional
        PlotDataItem keyword arguments, such as symbol and symbolSize.
    """

    REDRAW_ON_X, REDRAW_ON_Y, REDRAW_ON_EITHER, REDRAW_ON_BOTH = range(4)
    symbols = OrderedDict([('None', None),
                           ('Circle', 'o'),
                           ('Square', 's'),
                           ('Triangle', 't'),
                           ('Star', 'star'),
                           ('Pentagon', 'p'),
                           ('Hexagon', 'h'),
                           ('X', 'x'),
                           ('Diamond', 'd'),
                           ('Plus', '+')])
    lines = OrderedDict([('NoLine', Qt.NoPen),
                         ('Solid', Qt.SolidLine),
                         ('Dash', Qt.DashLine),
                         ('Dot', Qt.DotLine),
                         ('DashDot', Qt.DashDotLine),
                         ('DashDotDot', Qt.DashDotDotLine)])
    data_changed = Signal()

    def __init__(self, color=None, lineStyle=None, lineWidth=None, **kws):
        self._color = QColor('white')
        self._pen = mkPen(self._color)
        if lineWidth is not None:
            self._pen.setWidth(lineWidth)
        if lineStyle is not None:
            self._pen.setStyle(lineStyle)
        kws['pen'] = self._pen
        super(BasePlotCurveItem, self).__init__(**kws)
        self.setSymbolBrush(None)
        if color is not None:
            self.color = color

        if hasattr(self, "channels"):
            self.destroyed.connect(functools.partial(widget_destroyed,
                                                     self.channels))

    @property
    def color_string(self):
        """
        A string representation of the color used for the curve.  This string
        will be a hex color code, like #FF00FF, or an SVG spec color name, if
        a name exists for the color.

        Returns
        -------
        str
        """
        return str(utilities.colors.svg_color_from_hex(self.color.name(),
                                                       hex_on_fail=True))

    @color_string.setter
    def color_string(self, new_color_string):
        """
        A string representation of the color used for the curve.  This string
        will be a hex color code, like #FF00FF, or an SVG spec color name, if
        a name exists for the color.

        Parameters
        -------
        new_color_string: int
            The new string to use for the curve color.
        """
        self.color = QColor(str(new_color_string))

    @property
    def color(self):
        """
        The color used for the curve.

        Returns
        -------
        QColor
        """
        return self._color

    @color.setter
    def color(self, new_color):
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
    def lineStyle(self):
        """
        Return the style of the line connecting the data points.
        Must be a value from the Qt::PenStyle enum
        (see http://doc.qt.io/qt-5/qt.html#PenStyle-enum).

        Returns
        -------
        int
        """
        return self._pen.style()

    @lineStyle.setter
    def lineStyle(self, new_style):
        """
        Set the style of the line connecting the data points.
        Must be a value from the Qt::PenStyle enum
        (see http://doc.qt.io/qt-5/qt.html#PenStyle-enum).

        Parameters
        -------
        new_style: int
        """
        if new_style in self.lines.values():
            self._pen.setStyle(new_style)
            self.setPen(self._pen)

    @property
    def lineWidth(self):
        """
        Return the width of the line connecting the data points.

        Returns
        -------
        int
        """
        return self._pen.width()

    @lineWidth.setter
    def lineWidth(self, new_width):
        """
        Set the width of the line connecting the data points.

        Parameters
        -------
        new_width: int
        """
        self._pen.setWidth(int(new_width))
        self.setPen(self._pen)

    @property
    def symbol(self):
        """
        The single-character code for the symbol drawn at each datapoint.

        See the documentation for pyqtgraph.PlotDataItem for possible values.

        Returns
        -------
        str or None
        """
        return self.opts['symbol']

    @symbol.setter
    def symbol(self, new_symbol):
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
    def symbolSize(self):
        """
        Return the size of the symbol to represent the data.

        Returns
        -------
        int
        """
        return self.opts['symbolSize']

    @symbolSize.setter
    def symbolSize(self, new_size):
        """
        Set the size of the symbol to represent the data.

        Parameters
        -------
        new_size: int
        """
        self.setSymbolSize(int(new_size))

    def to_dict(self):
        """
        Returns an OrderedDict representation with values for all properties
        needed to recreate this curve.

        Returns
        -------
        OrderedDict
        """
        return OrderedDict([("name", self.name()),
                            ("color", self.color_string),
                            ("lineStyle", self.lineStyle),
                            ("lineWidth", self.lineWidth),
                            ("symbol", self.symbol),
                            ("symbolSize", self.symbolSize)])

    def close(self):
        pass


class BasePlot(PlotWidget, PyDMPrimitiveWidget):
    crosshair_position_updated = Signal(float, float)

    def __init__(self, parent=None, background='default', axisItems=None):
        PlotWidget.__init__(self, parent=parent, background=background,
                            axisItems=axisItems)
        PyDMPrimitiveWidget.__init__(self)

        self.plotItem = self.getPlotItem()
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

        self._redraw_rate = 30 # Redraw at 30 Hz by default.
        self.maxRedrawRate = self._redraw_rate
        self._curves = []
        self._title = None
        self._show_legend = False
        self._legend = self.addLegend()
        self._legend.hide()

        # Drawing crosshair on the ViewBox
        self.vertical_crosshair_line = None
        self.horizontal_crosshair_line = None
        self.crosshair_movement_proxy = None

    def addCurve(self, plot_item, curve_color=None):
        if curve_color is None:
            curve_color = utilities.colors.default_colors[
                    len(self._curves) % len(utilities.colors.default_colors)]
            plot_item.color_string = curve_color
        self._curves.append(plot_item)
        self.addItem(plot_item)
        self.redraw_timer.start()
        # Connect channels
        for chan in plot_item.channels():
            if chan:
                chan.connect()
        # self._legend.addItem(plot_item, plot_item.curve_name)

    def removeCurve(self, plot_item):
        self.removeItem(plot_item)
        self._curves.remove(plot_item)
        if len(self._curves) < 1:
            self.redraw_timer.stop()
        # Disconnect channels
        for chan in plot_item.channels():
            if chan:
                chan.disconnect()

    def removeCurveWithName(self, name):
        for curve in self._curves:
            if curve.name() == name:
                self.removeCurve(curve)

    def removeCurveAtIndex(self, index):
        curve_to_remove = self._curves[index]
        self.removeCurve(curve_to_remove)

    def setCurveAtIndex(self, index, new_curve):
        old_curve = self._curves[index]
        self._curves[index] = new_curve
        # self._legend.addItem(new_curve, new_curve.name())
        self.removeCurve(old_curve)

    def curveAtIndex(self, index):
        return self._curves[index]

    def curves(self):
        return self._curves

    def clear(self):
        legend_items = [label.text for (sample, label) in self._legend.items]
        for item in legend_items:
            self._legend.removeItem(item)
        self.plotItem.clear()
        self._curves = []

    @Slot()
    def redrawPlot(self):
        pass

    def getShowXGrid(self):
        return self._show_x_grid

    def setShowXGrid(self, value, alpha=None):
        self._show_x_grid = value
        self.showGrid(x=self._show_x_grid, alpha=alpha)

    def resetShowXGrid(self):
        self.setShowXGrid(False)

    showXGrid = Property("bool", getShowXGrid, setShowXGrid, resetShowXGrid)

    def getShowYGrid(self):
        return self._show_y_grid

    def setShowYGrid(self, value, alpha=None):
        self._show_y_grid = value
        self.showGrid(y=self._show_y_grid, alpha=alpha)

    def resetShowYGrid(self):
        self.setShowYGrid(False)

    showYGrid = Property("bool", getShowYGrid, setShowYGrid, resetShowYGrid)

    def getBackgroundColor(self):
        return self.backgroundBrush().color()

    def setBackgroundColor(self, color):
        if self.backgroundBrush().color() != color:
            self.setBackgroundBrush(QBrush(color))

    backgroundColor = Property(QColor, getBackgroundColor, setBackgroundColor)

    def getAxisColor(self):
        return self.getAxis('bottom')._pen.color()

    def setAxisColor(self, color):
        if self.getAxis('bottom')._pen.color() != color:
            self.getAxis('bottom').setPen(color)
            self.getAxis('left').setPen(color)
            self.getAxis('top').setPen(color)
            self.getAxis('right').setPen(color)

    axisColor = Property(QColor, getAxisColor, setAxisColor)

    def getBottomAxisLabel(self):
        return self.getAxis('bottom').labelText

    def getShowRightAxis(self):
        """
        Provide whether the right y-axis is being shown.

        Returns : bool
        -------
        True if the graph shows the right y-axis. False if not.

        """
        return self._show_right_axis

    def setShowRightAxis(self, show):
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

    def getPlotTitle(self):
        if self._title is None:
            return ""
        return str(self._title)

    def setPlotTitle(self, value):
        self._title = str(value)
        if len(self._title) < 1:
            self._title = None
        self.setTitle(self._title)

    def resetPlotTitle(self):
        self._title = None
        self.setTitle(self._title)

    title = Property(str, getPlotTitle, setPlotTitle, resetPlotTitle)

    def getShowLegend(self):
        """
        Check if the legend is being shown.

        Returns : bool
        -------
            True if the legend is displayed on the graph; False if not.
        """
        return self._show_legend

    def setShowLegend(self, value):
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

    def resetShowLegend(self):
        """
        Reset the legend display status to hidden.
        """
        self.setShowLegend(False)

    showLegend = Property(bool, getShowLegend, setShowLegend, resetShowLegend)

    def getAutoRangeX(self):
        return self._auto_range_x

    def setAutoRangeX(self, value):
        self._auto_range_x = value
        if self._auto_range_x:
            self.plotItem.enableAutoRange(ViewBox.XAxis, enable=self._auto_range_x)

    def resetAutoRangeX(self):
        self.setAutoRangeX(True)

    def getAutoRangeY(self):
        return self._auto_range_y

    def setAutoRangeY(self, value):
        self._auto_range_y = value
        if self._auto_range_y:
            self.plotItem.enableAutoRange(ViewBox.YAxis, enable=self._auto_range_y)

    def resetAutoRangeY(self):
        self.setAutoRangeY(True)

    def getMinXRange(self):
        """
        Minimum X-axis value visible on the plot.

        Returns
        -------
        float
        """
        return self.plotItem.viewRange()[0][0]

    def setMinXRange(self, new_min_x_range):
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

    def getMaxXRange(self):
        """
        Maximum X-axis value visible on the plot.

        Returns
        -------
        float
        """
        return self.plotItem.viewRange()[0][1]

    def setMaxXRange(self, new_max_x_range):
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

    def getMinYRange(self):
        """
        Minimum Y-axis value visible on the plot.

        Returns
        -------
        float
        """
        return self.plotItem.viewRange()[1][0]

    def setMinYRange(self, new_min_y_range):
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


    def getMaxYRange(self):
        """
        Maximum Y-axis value visible on the plot.

        Returns
        -------
        float
        """
        return self.plotItem.viewRange()[1][1]

    def setMaxYRange(self, new_max_y_range):
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
    def mouseEnabledX(self):
        """
        Whether or not mouse interactions are enabled for the X-axis.

        Returns
        -------
        bool
        """
        return self.plotItem.getViewBox().state['mouseEnabled'][0]

    @mouseEnabledX.setter
    def mouseEnabledX(self, x_enabled):
        """
        Whether or not mouse interactions are enabled for the X-axis.

        Parameters
        -------
        x_enabled : bool
        """
        self.plotItem.setMouseEnabled(x=x_enabled)

    @Property(bool)
    def mouseEnabledY(self):
        """
        Whether or not mouse interactions are enabled for the Y-axis.

        Returns
        -------
        bool
        """
        return self.plotItem.getViewBox().state['mouseEnabled'][1]

    @mouseEnabledY.setter
    def mouseEnabledY(self, y_enabled):
        """
        Whether or not mouse interactions are enabled for the Y-axis.

        Parameters
        -------
        y_enabled : bool
        """
        self.plotItem.setMouseEnabled(y=y_enabled)

    @Property(int)
    def maxRedrawRate(self):
        """
        The maximum rate (in Hz) at which the plot will be redrawn.
        The plot will not be redrawn if there is not new data to draw.

        Returns
        -------
        int
        """
        return self._redraw_rate

    @maxRedrawRate.setter
    def maxRedrawRate(self, redraw_rate):
        """
        The maximum rate (in Hz) at which the plot will be redrawn.
        The plot will not be redrawn if there is not new data to draw.

        Parameters
        -------
        redraw_rate : int
        """
        self._redraw_rate = redraw_rate
        self.redraw_timer.setInterval(int((1.0/self._redraw_rate)*1000))

    def pausePlotting(self):
        self.redraw_timer.stop() if self.redraw_timer.isActive() else self.redraw_timer.start()
        return self.redraw_timer.isActive()

    def mouseMoved(self, evt):
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

    def enableCrosshair(self, is_enabled, starting_x_pos, starting_y_pos,  vertical_angle=90, horizontal_angle=0,
                        vertical_movable=False, horizontal_movable=False):
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
            self.vertical_crosshair_line = InfiniteLine(pos=starting_x_pos, angle=vertical_angle,
                                                        movable=vertical_movable)
            self.horizontal_crosshair_line = InfiniteLine(pos=starting_y_pos, angle=horizontal_angle,
                                                          movable=horizontal_movable)

            self.plotItem.addItem(self.vertical_crosshair_line)
            self.plotItem.addItem(self.horizontal_crosshair_line)
            self.crosshair_movement_proxy = SignalProxy(self.plotItem.scene().sigMouseMoved, rateLimit=60,
                                                        slot=self.mouseMoved)
        else:
            if self.vertical_crosshair_line:
                self.plotItem.removeItem(self.vertical_crosshair_line)
            if self.horizontal_crosshair_line:
                self.plotItem.removeItem(self.horizontal_crosshair_line)
            if self.crosshair_movement_proxy:
                self.crosshair_movement_proxy.disconnect()
