import datetime
import json
from collections import OrderedDict
import numpy as np
from PyQt5.QtWidgets import QAction, QMenu
from pyqtgraph import AxisItem
from qtpy import QtGui
from qtpy.QtGui import QColor
from qtpy.QtCore import Slot, Property, Qt
from .baseplot import BasePlot, NoDataError, BasePlotCurveItem
from .timeplot import TimeAxisItem
from .. import utilities
import urllib.request

DEFAULT_TIME_SPAN = 60         #minutes


class ArchiverPlotCurveItem(BasePlotCurveItem):
    """
        ArchiverPlotCurveItem represents a single curve in an archiver appliance plot.

        It is used to plot a scalar value vs. time.  In addition to the parameters
        listed below, ArchiverPlotCurveItem accepts keyword arguments for all plot
        options that pyqtgraph.PlotDataItem accepts.

        Parameters
        ----------
        channel_name : str
            The channel name to of the scalar data to plot.
        color : QColor, optional
            The color used to draw the curve line and the symbols.
        lineStyle: int, optional
            Style of the line connecting the data points.
            Must be a value from the Qt::PenStyle enum
            (see http://doc.qt.io/qt-5/qt.html#PenStyle-enum).
        lineWidth: int, optional
            Width of the line connecting the data points.
        **kws : dict
            Additional parameters supported by pyqtgraph.PlotDataItem,
            like 'symbol' and 'symbolSize'.
        """

    def __init__(self, channel_name=None, **kws):
        """
        Parameters
        ----------
        channel_name : str
            The PV name
        kws : dict
            Additional parameters supported by pyqtgraph.PlotDataItem,
            like 'symbol' and 'symbolSize'.
        """
        self._channelName = channel_name

        if "name" not in kws or not kws["name"]:
            kws["name"] = channel_name
        if 'symbol' not in kws.keys():
            kws['symbol'] = 'o'
        if 'lineStyle' not in kws.keys():
            kws['lineStyle'] = Qt.NoPen
        super(ArchiverPlotCurveItem, self).__init__(**kws)

    def to_dict(self):
        """
        Serialize this curve into a dictionary.

        Returns
    -------
        OrderedDict
            Representation with values for all properties
            needed to recreate this curve.
        """
        dic_ = OrderedDict([("channelName", self.channelName), ])
        dic_.update(super(ArchiverPlotCurveItem, self).to_dict())
        return dic_

    @property
    def channelName(self):
        if self._channelName is None:
            return None
        return self._channelName

    @channelName.setter
    def channelName(self, new_channel_name):
        if str(new_channel_name) != self._channelName:
            self._channelName = str(new_channel_name)

    def redrawCurve(self, base_url, time_span):
        """
        Called by the curve's parent plot whenever the curve needs to be
        re-drawn with new data.
        """
        #base_url = "http://10.50.10.3:17668"
        from_dt = datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(minutes=time_span)
        to_dt = datetime.datetime.now(datetime.timezone.utc)
        from_dt_str = from_dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
        to_dt_str = to_dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
        url_string = f"{base_url}/retrieval/data/getData.json?pv={self._channelName}&from={from_dt_str}&to={to_dt_str}"
        req=urllib.request.urlopen(url_string)
        data = json.load(req)
        secs = [x['secs'] for x in data[0]['data']]
        vals = [x['val'] for x in data[0]['data']]
        self.setData(x=secs, y=vals)


class ArchiverPlot(BasePlot):
    """
        ArchiverPlot is a widget to plot the pv data from archiver appliance.
        Each curve can plot a PV data.

        Parameters
        ----------
        parent : optional
            The parent of this widget.
        init_y_channels : list
            A list of scalar channels to plot vs time.
        background: optional
            The background color for the plot.  Accepts any arguments that
            pyqtgraph.mkColor will accept.
        """

    def __init__(self, parent=None, init_y_channels=[], background='default'):
        """
        Parameters
        ----------

        parent : Widget
            The parent widget of the chart.
        init_y_channels : list
            A list of scalar channels to plot vs time.
        background : str, optional
            The background color for the plot.  Accepts any arguments that
            pyqtgraph.mkColor will accept.
        """

        self.refresh_action = None
        self.popmenu = None

        self._left_axis = AxisItem("left")
        self._bottom_axis = TimeAxisItem('bottom')

        # If the user supplies a single string instead of a list,
        # wrap it in a list.
        if isinstance(init_y_channels, str):
            init_y_channels = [init_y_channels]

        for channel in init_y_channels:
            self.addYChannel(channel)

        self._needs_redraw = True

        super(ArchiverPlot, self).__init__(parent, background=background,
                                           axisItems={"bottom": self._bottom_axis, "left": self._left_axis})
        self._base_url = "http://ip:port"
        self._time_span = DEFAULT_TIME_SPAN  # in minutes

    def getBaseURL(self):
        """
        The url of the archiver server. Port should be included. For example, http://10.30.1.130:17668

        Returns
        -------
        base_url : string
        """
        return self._base_url

    def setBaseURL(self, value):
        """
        Set the base_url of archiver server.
        Parameters
        ----------
        value : string
        """
        self._base_url = value

    def resetBaseURL(self):
        """
        Reset the timespan to the default value.
        """
        self._base_url = "http://ip:port"

    baseURL = Property(str, getBaseURL, setBaseURL, resetBaseURL)

    def getTimeSpan(self):
        """
        The extent of the x-axis of the chart, in minutes.  In other words,
        how long a data point stays on the plot before falling off the left
        edge.

        Returns
        -------
        time_span : float
            The extent of the x-axis of the chart, in minutes.
        """
        return float(self._time_span)

    def setTimeSpan(self, value):
        """
        Set the extent of the x-axis of the chart, in minutes.
        """
        value = float(value)
        if self._time_span != value:
            self._time_span = value

    def resetTimeSpan(self):
        """
        Reset the timespan to the default value.
        """
        if self._time_span != DEFAULT_TIME_SPAN:
            self._time_span = DEFAULT_TIME_SPAN

    timeSpan = Property(float, getTimeSpan, setTimeSpan, resetTimeSpan)

    def mousePressEvent(self, ev):
        """
        Use the middle mouse event to refresh data from archiver appliance.
        Every time we press the 'Refresh' menu popping from the middle mouse event,
        the data will be refreshed.
        """
        super().mousePressEvent(ev)
        if ev.buttons() == Qt.MiddleButton:
            self.popmenu = QMenu(self)
            self.refresh_action = QAction(self.popmenu)
            self.refresh_action.setText("Refresh")
            self.refresh_action.triggered.connect(lambda: self.redrawPlot())
            self.popmenu.addAction(self.refresh_action)

            self.popmenu.move(QtGui.QCursor.pos())
            self.popmenu.show()

    def initialize_for_designer(self):
        # If we are in Qt Designer, don't update the plot continuously.
        # This function gets called by PyDMTimePlot's designer plugin.
        pass

    def addCurve(self, plot_data_item, curve_color=None, y_axis_name=None):
        """
        Adds a curve to this plot. If the y axis parameters are specified, either link this curve to an existing
        axis if that axis is already part of this plot, or create a new one and link the curve to it.
        Parameters
        ----------
        plot_data_item: BasePlotCurveItem
            The curve to add to this plot
        curve_color: QColor, optional
            The color to draw the curve and axis
        y_axis_name: str, optional
            The name of the axis to link the curve with. If this is the first time seeing this name,
            then a new axis will be created for it.
        """

        if curve_color is None:
            curve_color = utilities.colors.default_colors[
                len(self._curves) % len(utilities.colors.default_colors)]
            plot_data_item.color_string = curve_color

        self._curves.append(plot_data_item)

        if y_axis_name is None:
            # If the user did not name the axis, use the default ones. Note: multiple calls to setAxisItems() are ok
            self.plotItem.setAxisItems()
            self.addItem(plot_data_item)
        elif y_axis_name in self.plotItem.axes:
            # If the user has chosen an axis that already exists for this curve, simply link the data to that axis
            self.plotItem.linkDataToAxis(plot_data_item, y_axis_name)
        else:
            # Otherwise we create a brand new axis for this data
            self.addAxis(plot_data_item, y_axis_name, 'left')

    def addYChannel(self, channelName=None, name=None, color=None,
                    lineStyle=None, lineWidth=None, symbol=None,
                    symbolSize=None, yAxisName=None):
        """
        Add a new curve to the plot.  In addition to the arguments below,
        all other keyword arguments are passed to the underlying
        pyqtgraph.PlotDataItem used to draw the curve.

        Parameters
        ----------
        channelName: str
            The name for the channel for the curve.
        name: str, optional
            A name for this curve.  The name will be used in the plot legend.
        color: str or QColor, optional
            A color for the line of the curve.  If not specified, the plot will
            automatically assign a unique color from a set of default colors.
        lineStyle: int, optional
            Style of the line connecting the data points.
            0 means no line (scatter plot).
        lineWidth: int, optional
            Width of the line connecting the data points.
        symbol: str or None, optional
            Which symbol to use to represent the data.
        symbolSize: int, optional
            Size of the symbol.
        yAxisName : str, optional
            The name of the y axis to associate with this curve. Will be created if it
            doesn't yet exist
        """
        plot_opts = {}
        plot_opts['symbol'] = symbol
        if symbolSize is not None:
            plot_opts['symbolSize'] = symbolSize
        if lineStyle is not None:
            plot_opts['lineStyle'] = lineStyle
        if lineWidth is not None:
            plot_opts['lineWidth'] = lineWidth
        if channelName is not None:
            plot_opts['channelName'] = channelName

        curve = ArchiverPlotCurveItem(channel_name=channelName, name=name, color=color,
                                      yAxisName=yAxisName, **plot_opts)
        self.addCurve(curve, curve_color=color, y_axis_name=yAxisName)

    def removeCurve(self, plot_item):
        """
        Remove a curve from the plot.

        Parameters
        ----------
        curve: ArchiverPlotCurveItem
            The curve to remove.
        """
        if plot_item.y_axis_name in self.plotItem.axes:
            self.plotItem.unlinkDataFromAxis(plot_item.y_axis_name)

        self.removeItem(plot_item)
        self._curves.remove(plot_item)

    def removeChannel(self, curve):
        """
        Remove a curve from the plot.

        Parameters
        ----------
        curve: ArchiverPlotCurveItem
            The curve to remove.
        """
        self.removeCurve(curve)

    def removeChannelAtIndex(self, index):
        """
        Remove a curve from the plot, given an index
        for a curve.

        Parameters
        ----------
        index: int
            Index for the curve to remove.
        """
        curve = self._curves[index]
        self.removeChannel(curve)

    @Slot()
    def set_needs_redraw(self):
        self._needs_redraw = True

    @Slot()
    def redrawPlot(self):
        """
        Request a redraw from each curve in the plot.
        Called by curves.
        """

        for curve in self._curves:
            curve.redrawCurve(self._base_url, self._time_span)

    def clearCurves(self):
        """
        Remove all curves from the plot.
        """
        super(ArchiverPlot, self).clear()

    def getCurves(self):
        """
        Get a list of json representations for each curve.
        """
        return [json.dumps(curve.to_dict()) for curve in self._curves]

    def setCurves(self, new_list):
        """
        Replace all existing curves with new ones.  This function
        is mostly used as a way to load curves from a .ui file, and
        almost all users will want to add curves through addChannel,
        not this method.

        Parameters
        ----------
        new_list: list
            A list of json strings representing each curve in the plot.
        """
        try:
            new_list = [json.loads(str(i)) for i in new_list]
        except ValueError as e:
            print("Error parsing curve json data: {}".format(e))
            return
        self.clearCurves()
        for d in new_list:
            color = d.get('color')
            if color:
                color = QColor(color)
            self.addYChannel(channelName=d.get('channelName'),
                             name=d.get('name'),
                             color=color,
                             lineStyle=d.get('lineStyle'),
                             lineWidth=d.get('lineWidth'),
                             symbol=d.get('symbol'),
                             symbolSize=d.get('symbolSize'),
                             yAxisName=d.get('yAxisName'))

    curves = Property("QStringList", getCurves, setCurves, designable=False)

    autoRangeX = Property(bool, BasePlot.getAutoRangeX,
                          BasePlot.setAutoRangeX, BasePlot.resetAutoRangeX,
                          doc="""
Whether or not the X-axis automatically rescales to fit the data.
If true, the values in minXRange and maxXRange are ignored.""")

    minXRange = Property(float, BasePlot.getMinXRange,
                         BasePlot.setMinXRange, doc="""
Minimum X-axis value visible on the plot.""")

    maxXRange = Property(float, BasePlot.getMaxXRange,
                         BasePlot.setMaxXRange, doc="""
Maximum X-axis value visible on the plot.""")

    autoRangeY = Property(bool, BasePlot.getAutoRangeY,
                          BasePlot.setAutoRangeY, BasePlot.resetAutoRangeY,
                          doc="""
Whether or not the Y-axis automatically rescales to fit the data.
If true, the values in minYRange and maxYRange are ignored.""")

    minYRange = Property(float, BasePlot.getMinYRange,
                         BasePlot.setMinYRange, doc="""
Minimum Y-axis value visible on the plot.""")

    maxYRange = Property(float, BasePlot.getMaxYRange,
                         BasePlot.setMaxYRange, doc="""
Maximum Y-axis value visible on the plot.""")
