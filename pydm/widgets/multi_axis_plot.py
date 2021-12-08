import weakref
try:
    from html import escape  # Python 3
except ImportError:
    from cgi import escape  # Can't only use this since it was removed in Python 3.8 and up
from collections import Counter
from pyqtgraph import GraphicsWidget, PlotItem, ViewBox
from .multi_axis_viewbox import MultiAxisViewBox
from .multi_axis_viewbox_menu import MultiAxisViewBoxMenu


class MultiAxisPlot(PlotItem):
    """
    MultiAxisPlot is a PyQtGraph PlotItem subclass that has support for adding multiple y axes for
    PyDM's use cases. Currently PyQtGraph does not support this functionality natively, so we do it here by
    assigning a ViewBox to each new axis and any curves associated with that axis.

    Parameters
    ----------
    parent: QGraphicsWidget, optional
        The parent widget for this plot
    axisItems: Dict[str, AxisItem]
        Dictionary instructing the PlotItem to use pre-constructed items for its axes
    **kargs: optional
        PlotItem keyword arguments
    """

    def __init__(self, parent=None, axisItems=None, **kargs):
        # Create a view box that will support multiple axes to pass to the PyQtGraph PlotItem
        viewBox = MultiAxisViewBox()
        viewBox.menu = MultiAxisViewBoxMenu(viewBox)
        super(MultiAxisPlot, self).__init__(viewBox=viewBox, axisItems=axisItems, **kargs)

        self.curvesPerAxis = Counter()  # A simple mapping of AxisName to a count of curves that using that axis

        # A set containing view boxes which are stacked underneath the top level view. These views will be needed
        # in order to support multiple axes on the same plot. This set will remain empty if the plot has only one set of axes
        self.stackedViews = weakref.WeakSet()
        viewBox.sigResized.connect(self.updateStackedViews)

        # Signals that will be emitted when mouse wheel or mouse drag events happen
        self.vb.sigMouseDragged.connect(self.handleMouseDragEvent)
        self.vb.sigMouseWheelZoomed.connect(self.handleWheelEvent)
        if self.vb.menuEnabled():
            self.vb.menu.sigMouseModeChanged.connect(self.changeMouseMode)

    def addAxis(self, axis, name, plotDataItem=None, setXLink=False, enableAutoRangeX=True, enableAutoRangeY=True,
                minRange=-1.0, maxRange=1.0):
        """
        Add an axis to this plot by creating a new view box to link it with. Links the PlotDataItem
        with this axis if provided
        Parameters
        ----------
        axis: AxisItem
            The axis to be added to this PlotItem. A new view box will be created and linked with this axis
        name: str
            The names associated with this axis item. Will be used by this PlotItem to refer to this axis
        plotDataItem : PlotDataItem, optional
            The plot data that will be linked with the created axis. If None, then no plot data will be linked
            with this axis to start with
        setXLink: bool
            Whether or not to link the created view to the x axis of this plot item. Linking will disable
            autorange on the x axis for the view, so only do this if you do not want the view to update the x axis
        enableAutoRangeX: bool
            Whether or not the new view should automatically update its x range when receiving new data
        enableAutoRangeY: bool
            Whether or not the new view should automatically update its y range when receiving new data
        minRange: float
            The minimum range to display on this axis if not using autorange
        maxRange: float
            The maximum range to display on this axis if not using autorange
        """

        # Create a new view box to link this axis with
        self.axes[str(name)] = {'item': axis, 'pos': None}  # The None will become an actual position in rebuildLayout() below
        view = MultiAxisViewBox()
        view.setYRange(minRange, maxRange)
        view.enableAutoRange(axis=ViewBox.XAxis, enable=enableAutoRangeX)
        view.enableAutoRange(axis=ViewBox.YAxis, enable=enableAutoRangeY)
        if setXLink:
            view.setXLink(self)  # Link this view to the shared x-axis of this plot item
        else:
            self.axes['bottom']['item'].linkToView(view)  # Ensure the x axis will update when the view does

        view.setMouseMode(self.vb.state['mouseMode'])  # Ensure that mouse behavior is consistent between stacked views
        axis.linkToView(view)

        if plotDataItem is not None:
            self.linkDataToAxis(plotDataItem, name)

        self.scene().addItem(view)
        self.addStackedView(view)

        # Rebuilding the layout of the plot item will put the new axis in the correct place
        self.rebuildLayout()
        self.updateStackedViews()

    def addStackedView(self, view):
        """
        Add a view that will be stacked underneath the top level view box. Any mouse or key events handled by any of the
        view boxes will be propagated through all the stacked views added here
        Parameters
        ----------
        view: ViewBox
            The view to be added.
        """

        self.stackedViews.add(view)

        # These signals will be emitted when the view handles these events, and will be connected
        # to the event handling code of the stacked views
        view.sigMouseDragged.connect(self.handleMouseDragEvent)
        view.sigMouseWheelZoomed.connect(self.handleWheelEvent)
        self.vb.sigHistoryChanged.connect(view.scaleHistory)

    def updateStackedViews(self):
        """
        Callback for resizing stacked views when the geometry of their top level view changes
        """
        for view in self.stackedViews:
            view.setGeometry(self.vb.sceneBoundingRect())

    def linkDataToAxis(self, plotDataItem, axisName):
        """
        Links the input PlotDataItem to the axis with the given name. Raises an exception if that axis does not exist.
        Unlinks the data from any view it was previously linked to.
        Parameters
        ----------
        plotDataIem: PlotDataItem
            The data to link with the input axis
        axisName: str
            The name of the axis to link the data with

        Raises
        ------
        KeyError
            If the input axis name is not actually the name of an axis on this plot
        """

        if plotDataItem is None:
            return

        axisToLink = self.axes.get(axisName)['item']

        # If this data is being moved from an existing view box, unlink that view box first
        currentView = plotDataItem.getViewBox()
        if currentView is not None:
            currentView.removeItem(plotDataItem)
            plotDataItem.forgetViewBox()

        axisToLink.linkedView().addItem(plotDataItem)
        self.dataItems.append(plotDataItem)
        # Maintain all configurable options set by this plot
        (alpha, auto) = self.alphaState()
        plotDataItem.setAlpha(alpha, auto)
        plotDataItem.setFftMode(self.ctrl.fftCheck.isChecked())
        plotDataItem.setDownsampling(*self.downsampleMode())
        plotDataItem.setClipToView(self.clipToViewMode())
        plotDataItem.setPointMode(self.pointMode())

        # Add to average if needed
        self.updateParamList()
        if self.ctrl.averageGroup.isChecked():
            self.addAvgCurve(plotDataItem)

        if plotDataItem.name():
            if axisToLink.labelText:
                # Joins together the labels from the curves for display on their shared axis. The label
                # text expects html, so this will set it to be, for example, "label 1  &  label 2"
                axisToLink.setLabel(escape(axisToLink.labelText + ' & ' + plotDataItem.name()),
                                    color=plotDataItem.color_string)
            else:
                axisToLink.setLabel(plotDataItem.name(), color=plotDataItem.color_string)
        if self.legend is not None and plotDataItem.name():
            self.legend.addItem(plotDataItem, name=plotDataItem.name())

        self.curvesPerAxis[axisName] += 1

    def removeAxis(self, axisName):
        if axisName not in self.axes:
            return

        self.curvesPerAxis[axisName] = 0

        oldAxis = self.axes[axisName]['item']
        self.layout.removeItem(oldAxis)
        oldAxis.scene().removeItem(oldAxis)
        oldAxis.unlinkFromView()
        del self.axes[axisName]


    def unlinkDataFromAxis(self, axisName):
        """
        Lets the plot know that this axis is now associated with one less curve. If there are no
        longer any curves linked with this axis, then removes it from the scene and cleans it up.
        Parameters
        ----------
        axisName: str
            The name of the axis that a curve is being removed from
        """

        self.curvesPerAxis[axisName] -= 1
        if self.curvesPerAxis[axisName] == 0:
            self.removeAxis(axisName)

    def setXRange(self, minX, maxX, padding=0, update=True):
        """
        Set the x axis range of this plot item's view box, as well as all view boxes in its stack.
        Parameters
        ----------
        minX: float
            The minimum value for display on the x axis
        maxX: float
            The maximum value for display on the x axis
        padding: float
            Added on to the minimum and maximum values to display a little extra
        update: bool
            If True, update the range of the ViewBox immediately. Otherwise, the update
            is deferred until before the next render.
        """

        for view in self.stackedViews:
            view.setXRange(minX, maxX, padding=padding)
        super(MultiAxisPlot, self).setXRange(minX, maxX, padding=padding)

    def setYRange(self, minY, maxY, padding=0, update=True):
        """
        Set the y axis range of this plot item's view box, as well as all view boxes in its stack.
        Parameters
        ----------
        minY: float
            The minimum value for display on the y axis
        maxY: float
            The maximum value for display on the y axis
        padding: float
            Added on to the minimum and maximum values to display a little extra
        update: bool
            If True, update the range of the ViewBox immediately. Otherwise, the update
            is deferred until before the next render.
        """

        for view in self.stackedViews:
            view.setYRange(minY, maxY, padding=padding)
        super(MultiAxisPlot, self).setYRange(minY, maxY, padding=padding)

    def clearAxes(self):
        """
        Cleans up all axis related data from this plot.
        """

        for view in self.stackedViews:
            self.removeItem(view)
            self.scene().removeItem(view)
        self.stackedViews.clear()

        # Reset the axes associated with all y axis curves
        allAxes = [val['item'] for val in self.axes.values()]
        for oldAxis in allAxes:
            if oldAxis.orientation != 'bottom':   # Currently only multiple y axes are supported
                self.layout.removeItem(oldAxis)
                oldAxis.scene().removeItem(oldAxis)
                oldAxis.unlinkFromView()

        # Retain the x axis
        bottomAxis = self.axes['bottom']
        self.axes = {'bottom': bottomAxis}

    def clearLayout(self):
        """
        Remove all items from the layout, but leave them intact in the scene so that we can replace them in a new
        layout. See removeItem(), clearPlots(), or clear() if removing the items themselves is required.
        """
        while self.layout.count() > 0:
            self.layout.removeAt(0)

    def rebuildLayout(self):
        """
        Rebuilds the layout for this PlotItem. This allows users to dynamically add additional axes to existing
        plots and have the plot automatically rebuild its layout, without the user having to create
        a new plot from scratch
        """
        self.clearLayout()

        orientations = {"left": [], "right": [], "top": [], "bottom": []}

        allAxes = [val['item'] for val in self.axes.values()]
        for axis in allAxes:
            orientations[axis.orientation].append(axis)

        leftOffset = len(orientations["left"])
        topOffset = 1 + len(orientations["top"])

        self.layout.addItem(self.vb, topOffset, leftOffset)

        for x, axis in enumerate(orientations["left"] + [None] + orientations["right"]):
            if axis is not None:
                self.layout.addItem(axis, topOffset, x)
        for y, axis in enumerate([None] + orientations["top"] + [None] + orientations["bottom"]):
            if axis is not None:
                self.layout.addItem(axis, y, leftOffset)

    def handleWheelEvent(self, view, ev, axis):
        """
        A simple slot for propagating a mouse wheel event to all the stacked view boxes (except for the one
        one emitting the signal)
        Parameters
        ----------
        view: ViewBox
            The view which emitted the signal that went to this slot
        ev:   QEvent
            The event to propagate
        axis: int
            The axis (or None) that the event happened on
        """
        for stackedView in self.stackedViews:
            if stackedView is not view:
                stackedView.wheelEvent(ev, axis, fromSignal=True)

    def handleMouseDragEvent(self, view, ev, axis):
        """
        A simple slot for propagating a mouse drag event to all the stacked view boxes (except for the one
        one emitting the signal)
        Parameters
        ----------
        view: ViewBox
            The view which emitted the signal that went to this slot
        ev:   QEvent
            The event to propagate
        axis: int
            The axis (or None) that the event happened on
        """
        for stackedView in self.stackedViews:
            if stackedView is not view:
                stackedView.mouseDragEvent(ev, axis, fromSignal=True)

    def changeMouseMode(self, mode):
        """
        Propagate a change of mouse mode through each stacked view box
        Parameters
        ----------
        mode: str
            Either "pan" or "rect". Pan makes the left click pan the plot, rect makes it draw a zooming box.

        Raises
        ------
        Exception
            Raised by PyQtGraph if the mode is not "pan" or "rect"
        """
        for stackedView in self.stackedViews:
            stackedView.setLeftButtonAction(mode)
