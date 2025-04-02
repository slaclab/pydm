import weakref
from pyqtgraph import AxisItem, PlotDataItem, PlotItem, ViewBox
from typing import List, Optional
from qtpy.QtCore import Qt, Signal
from .multi_axis_viewbox import MultiAxisViewBox
from .multi_axis_viewbox_menu import MultiAxisViewBoxMenu
from pydm.utilities import is_qt_designer


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

    sigXRangeChangedManually = Signal()

    def __init__(self, parent=None, axisItems=None, **kargs):
        # Create a view box that will support multiple axes to pass to the PyQtGraph PlotItem
        viewBox = MultiAxisViewBox()
        viewBox.menu = MultiAxisViewBoxMenu(viewBox)
        super().__init__(viewBox=viewBox, axisItems=axisItems, **kargs)

        self.axesOriginalRanges = {}  # Dict from axis name to floats (x, y) representing original range of the axis

        # A set containing view boxes which are stacked underneath the top level view. These views will be needed
        # in order to support multiple axes on the same plot. This set will remain empty if the plot has only
        # one set of axes
        self.stackedViews = weakref.WeakSet()
        viewBox.sigResized.connect(self.updateStackedViews, Qt.QueuedConnection)

        # Signals that will be emitted when mouse wheel or mouse drag events happen
        self.vb.sigMouseDragged.connect(self.handleMouseDragEvent)
        self.vb.sigMouseWheelZoomed.connect(self.handleWheelEvent)
        self.vb.setZValue(100)  # Keep this view box on top
        if self.vb.menuEnabled():
            self.connectMenuSignals(self.vb.menu)
        self.stackedViews.add(self.vb)

    def addAxis(
        self,
        axis,
        name,
        plotDataItem=None,
        setXLink=False,
        enableAutoRangeX=True,
        enableAutoRangeY=True,
        minRange=-1.0,
        maxRange=1.0,
    ):
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
        self.axes[str(name)] = {
            "item": axis,
            "pos": None,
        }  # The None will become an actual position in rebuildLayout() below
        view = MultiAxisViewBox()
        view.setYRange(minRange, maxRange)
        view.enableAutoRange(axis=ViewBox.XAxis, enable=enableAutoRangeX)
        view.enableAutoRange(axis=ViewBox.YAxis, enable=enableAutoRangeY)
        self.axes["bottom"]["item"].linkToView(view)  # Ensure the x axis will update when the view does

        view.setMouseMode(self.vb.state["mouseMode"])  # Ensure that mouse behavior is consistent between stacked views
        axis.linkToView(view)

        if plotDataItem is not None:
            self.linkDataToAxis(plotDataItem, name)

        if enableAutoRangeY:
            self.axesOriginalRanges[name] = (None, None)
        else:
            self.axesOriginalRanges[name] = (minRange, maxRange)

        self.scene().addItem(view)
        self.addStackedView(view)

        # Rebuilding the layout of the plot item will put the new axis in the correct place
        self.rebuildLayout()

    def change_axis_name(self, old_name: str, new_name: str):
        """Change the name of the axis by changing the item's key in the axes dictionary."""
        axis = self.axes[old_name]["item"]
        self.axes[new_name] = self.axes[old_name]
        if hasattr(axis, "_curves"):
            for curve in axis._curves:
                curve.y_axis_name = new_name
        del self.axes[old_name]

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

    def connectMenuSignals(self, view_box_menu: MultiAxisViewBoxMenu) -> None:
        """
        Connect the signals of a view box menu to the appropriate slots.

        Parameters
        ----------
        view_box_menu : MultiAxisViewBoxMenu
            The menu to connect actions to the correct slots.
        """
        view_box_menu.sigMouseModeChanged.connect(self.changeMouseMode)
        view_box_menu.sigXAutoRangeChanged.connect(self.updateXAutoRange)
        view_box_menu.sigYAutoRangeChanged.connect(self.updateYAutoRange)
        view_box_menu.sigRestoreRanges.connect(self.restoreAxisRanges)
        view_box_menu.sigSetAutorange.connect(self.setPlotAutoRange)
        view_box_menu.sigInvertAxis.connect(self.invertAxis)
        view_box_menu.sigVisibleOnly.connect(self.setPlotAutoRangeVisibleOnly)
        view_box_menu.sigAutoPan.connect(self.setPlotAutoPan)
        view_box_menu.sigXManualRange.connect(self.setXRange)
        view_box_menu.sigYManualRange.connect(self.setYRange)

    def updateStackedViews(self):
        """
        Callback for resizing stacked views when the geometry of their top level view changes
        """
        for view in self.stackedViews:
            view.setGeometry(self.vb.sceneBoundingRect())

    def linkDataToAxis(self, plotDataItem: PlotDataItem, axisName: str) -> None:
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

        if axisName not in self.axes:
            return
        axisToLink = self.axes.get(axisName)["item"]

        # If this data is being moved from an existing view box, unlink that view box first
        currentView = plotDataItem.getViewBox()
        if currentView is not None:
            currentView.removeItem(plotDataItem)
            plotDataItem.forgetViewBox()

        # Match the curve's logMode to its new axis' logMode
        plotDataItem.setLogMode(False, axisToLink.logMode)

        axisToLink.linkedView().addItem(plotDataItem)
        self.dataItems.append(plotDataItem)
        # Maintain all configurable options set by this plot
        (alpha, auto) = self.alphaState()
        plotDataItem.setAlpha(alpha, auto)
        plotDataItem.setFftMode(self.ctrl.fftCheck.isChecked())
        plotDataItem.setDownsampling(*self.downsampleMode())
        plotDataItem.setClipToView(self.clipToViewMode())

        # Add to average if needed
        self.updateParamList()
        if self.ctrl.averageGroup.isChecked():
            self.addAvgCurve(plotDataItem)

        if plotDataItem.name() and not axisToLink.labelText:
            axisToLink.setLabel(plotDataItem.name(), color=plotDataItem.color_string)
        elif axisToLink.labelText and plotDataItem.color_string and axisToLink.labelStyle["color"] == "#969696":
            # The color for the axis was not specified by the user (#969696 is default) so set it appropriately
            axisToLink.labelStyle["color"] = plotDataItem.color_string
            axisToLink._updateLabel()
        if self.legend is not None and plotDataItem.name():
            self.legend.addItem(plotDataItem, name=plotDataItem.name())

        # pyqtgraph expects data items on plots to be added to both the list of curves and items to function properly
        self.curves.append(plotDataItem)
        self.items.append(plotDataItem)
        if hasattr(axisToLink, "_curves"):
            axisToLink._curves.append(plotDataItem)
        axisToLink.show()
        for otherAxisName in self.axes.keys():
            self.autoVisible(otherAxisName)

    def removeAxis(self, axisName):
        if axisName not in self.axes:
            return

        oldAxis = self.axes[axisName]["item"]
        self.layout.removeItem(oldAxis)
        if oldAxis.scene() is not None:
            oldAxis.scene().removeItem(oldAxis)
        stackedView = oldAxis.linkedView()
        oldAxis.unlinkFromView()
        if stackedView and stackedView is not self.vb:
            self.stackedViews.remove(stackedView)
        del self.axes[axisName]

    def unlinkDataFromAxis(self, curve: PlotDataItem):
        """
        Lets the plot know that this axis is now associated with one less curve. If there are no
        longer any curves linked with this axis, then removes it from the scene and cleans it up.
        Parameters
        ----------
        axisName: str
            The name of the axis that a curve is being removed from
        """
        if (
            hasattr(curve, "y_axis_name")
            and curve.y_axis_name in self.axes
            and curve in self.axes[curve.y_axis_name]["item"]._curves
        ):
            self.legend.removeItem(curve.name())
            self.axes[curve.y_axis_name]["item"]._curves.remove(curve)
            self.autoVisible(curve.y_axis_name)

    def autoVisible(self, axisName):
        """Handle automatically hiding or showing an axis based on whether it has
        visible curves attached and/or if it's the last visible axis
        (don't automatically hide the last axis, even if all of it's curves are hidden)

        Parameters
        -------------
        axisName: str
            The name of the axis we are going to try to hide if possible, or show if not"""
        # Do we have any visible curves?
        axis = self.axes[axisName]["item"]
        if hasattr(axis, "_curves"):
            for curve in axis._curves:
                if curve.isVisible():
                    axis.show()
                    return

            # We don't have any visible curves, but are we the only curve being shown?
            for otherAxis in self.axes.keys():
                otherItem = self.axes[otherAxis]["item"]
                if otherItem is not axis and otherAxis not in ["bottom", "top"] and otherItem.isVisible():
                    axis.hide()
                    return
            # No other axis is visible.
            axis.show()

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
        if "bottom" not in self.axesOriginalRanges:
            self.axesOriginalRanges["bottom"] = (minX, maxX)
        super().setXRange(minX, maxX, padding=padding)

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
        super().setYRange(minY, maxY, padding=padding)

    def isAnyXAutoRange(self) -> bool:
        """Return true if any view boxes are set to autorange on the x-axis, false otherwise"""
        for view in self.stackedViews:
            if view.state["autoRange"][0]:
                return True
        return False

    def disableXAutoRange(self):
        """Disable x-axis autorange for all views in the plot."""
        for view in self.stackedViews:
            view.enableAutoRange(x=False)

    def getAxes(self) -> List[AxisItem]:
        """Returns all axes that have been added to this plot"""
        return [val["item"] for val in self.axes.values()]

    def clearAxes(self):
        """
        Cleans up all axis related data from this plot.
        """

        for view in self.stackedViews:
            self.removeItem(view)
            self.scene().removeItem(view)
        self.stackedViews.clear()

        # Reset the axes associated with all y axis curves
        allAxes = [val["item"] for val in self.axes.values()]
        for oldAxis in allAxes:
            if oldAxis.orientation != "bottom":  # Currently only multiple y axes are supported
                self.layout.removeItem(oldAxis)
                if oldAxis.scene() is not None:
                    oldAxis.scene().removeItem(oldAxis)
                oldAxis.unlinkFromView()

        # Retain the x axis
        bottomAxis = self.axes["bottom"]
        self.axes = {"bottom": bottomAxis}

    def restoreAxisRanges(self):
        """Restore the min and max range of all axes on the plot to their original values"""
        if len(self.axes) == 0 or len(self.axesOriginalRanges) == 0:
            return

        # First restore the range for all y-axis items added to this plot
        for axisName, axisValue in self.axes.items():
            axisItem = axisValue["item"]
            linkedView = axisItem.linkedView()
            if (
                linkedView is None
                or axisItem.orientation not in ("left", "right")
                or axisName not in self.axesOriginalRanges
            ):
                continue

            original_ranges = self.axesOriginalRanges[axisName]
            if original_ranges[0] is None:  # If set to None, then autorange was enabled
                linkedView.enableAutoRange(axis=ViewBox.YAxis, enable=True)
            else:
                linkedView.setYRange(original_ranges[0], original_ranges[1])

        # Now restore the x-axis range as well if needed
        if "bottom" in self.axesOriginalRanges and self.axesOriginalRanges["bottom"][0] is not None:
            self.setXRange(self.axesOriginalRanges["bottom"][0], self.axesOriginalRanges["bottom"][1])
        else:
            self.setPlotAutoRange(x=True)

    def setPlotAutoRange(self, x=None, y=None):
        """
        Set autorange for all views on the plot
        Parameters
        ----------
        x: bool, optional
            Set to true to enable x autorange or false to disable it. Defaults to None which will result in no change
        y: bool, optional
            Set to true to enable y autorange or false to disable it. Defaults to None which will result in no change
        """
        for stackedView in self.stackedViews:
            stackedView.enableAutoRange(x=x, y=y)
        self.getViewBox().enableAutoRange(x=x, y=y)

    def setPlotAutoPan(self, auto_pan_x: Optional[bool] = None, auto_pan_y: Optional[bool] = None) -> None:
        """
        Toggle pan only mode (no scaling) when auto range is enabled.

        Parameters
        ----------
        auto_pan_x : bool, optional
            Whether or not the x-axis should be set to auto pan. If omitted, will be unchanged from current value.
        auto_pan_y : bool, optional
            Whether or not the y-axis should be set to auto pan. If omitted, will be unchanged from current value.
        """
        for stackedView in self.stackedViews:
            stackedView.setAutoPan(x=auto_pan_x, y=auto_pan_y)

    def setPlotAutoRangeVisibleOnly(
        self, visible_only_x: Optional[bool] = None, visible_only_y: Optional[bool] = None
    ) -> None:
        """
        Toggle if auto range should use only visible data when calculating the range to show

        Parameters
        ----------
        visible_only_x : bool, optional
            Whether or not the x-axis should be set to visible only. If omitted, will be unchanged from current value.
        visible_only_y : bool, optional
            Whether or not the y-axis should be set to visible only. If omitted, will be unchanged from current value.
        """
        for stackedView in self.stackedViews:
            stackedView.setAutoVisible(x=visible_only_x, y=visible_only_y)

    def invertAxis(self, axis: int, inverted: bool) -> None:
        """
        Toggle whether or not the input axis should be inverted.

        Parameters
        ----------
        axis : int
            An int associated with the axis to modify. Must be either ViewBox.XAxis or ViewBox.YAxis from pyqtgraph
        inverted : bool
            True if we are inverting the axis, False if not
        """
        for stackedView in self.stackedViews:
            if axis == ViewBox.XAxis:
                stackedView.invertX(inverted)
            elif axis == ViewBox.YAxis:
                stackedView.invertY(inverted)

    def removeItem(self, item):
        """
        Remove an item from this plot. An override of the pyqtgraph implementation which assumes
        that there is only one view box and will delete items that do not exist on that view if called.
        """

        # First remove the item from all the lists on the plot itself
        if item not in self.items:
            return

        self.items.remove(item)
        if item in self.dataItems:
            self.dataItems.remove(item)

        if item in self.curves:
            self.curves.remove(item)
            self.updateDecimation()
            self.updateParamList()

        # Then let any view box it is associated with remove it from its internal lists as well
        if hasattr(item, "getViewBox"):
            linked_view = item.getViewBox()
            if linked_view is not None:
                linked_view.removeItem(item)

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

        allAxes = [val["item"] for val in self.axes.values()]
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

    def updateGrid(self, *args) -> None:
        """Show or hide the grid on a per-axis basis"""
        if is_qt_designer():
            return
        # Get the user-set value for the alpha used to draw the grid lines
        alpha = self.ctrl.gridAlphaSlider.value()
        x = alpha if self.ctrl.xGridCheck.isChecked() else False
        y = alpha if self.ctrl.yGridCheck.isChecked() else False
        all_axes = [val["item"] for val in self.axes.values()]
        for axis in all_axes:
            if axis.orientation in ("left", "right"):
                axis.setGrid(y)
            elif axis.orientation in ("top", "bottom"):
                axis.setGrid(x)

    def handleWheelEvent(self, view, ev, axis):
        """
        A simple slot for propagating a mouse wheel event to all the stacked view boxes (except for the one
        one emitting the signal). Only called once per X-Axis wheel event.
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

        # Manual changes to X-Axis signal. Function is called once per X-Axis wheel event
        self.sigXRangeChangedManually.emit()

    def handleMouseDragEvent(self, view, ev, axis):
        """
        A simple slot for propagating a mouse drag event to all the stacked view boxes (except for the one
        one emitting the signal). Only called once per X-Axis drag event.
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

        # Manual changes to X-Axis signal. Function is called once per X-Axis drag event
        self.sigXRangeChangedManually.emit()

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
        self.vb.setLeftButtonAction(mode)

    def updateXAutoRange(self, val):
        """Update the autorange values for the x-axis on all view boxes"""
        self.vb.enableAutoRange(ViewBox.XAxis, val)
        for stackedView in self.stackedViews:
            stackedView.enableAutoRange(ViewBox.XAxis, val)

    def updateYAutoRange(self, val):
        """Update the autorange values for the y-axis on all view boxes"""
        self.vb.enableAutoRange(ViewBox.YAxis, val)
        for stackedView in self.stackedViews:
            stackedView.enableAutoRange(ViewBox.YAxis, val)

    def updateLogMode(self) -> None:
        """Toggle log mode on or off for each item in the plot"""
        x = self.ctrl.logXCheck.isChecked()
        y = self.ctrl.logYCheck.isChecked()

        allAxes = self.getAxes()
        for axis in allAxes:
            if axis.orientation in ("bottom", "top"):
                axis.setLogMode(x)
            elif axis.orientation in ("left", "right"):
                axis.setLogMode(y)

        for i in self.items:
            if hasattr(i, "setLogMode"):
                i.setLogMode(x, y)

        for i in self.dataItems:
            if hasattr(i, "setLogMode"):
                i.setLogMode(x, y)

        self.enableAutoRange()
        self.recomputeAverages()

    def getViewBoxForAxis(self, axisName: str) -> ViewBox:
        """
        Retrieve the ViewBox associated with a given axis name.

        Parameters
        ----------
        axisName : str
            The name of the axis for which to obtain the linked ViewBox.

        Returns
        -------
        ViewBox
            The ViewBox linked to the axis specified by `axisName`. If the axis does not exist
            or it does not have a linked ViewBox, the main ViewBox is returned.

        Notes
        -----
        This method checks whether `axisName` exists in the `axes` dictionary. If it does, it retrieves
        the corresponding AxisItem and calls its `linkedView()` method. If a valid ViewBox is found,
        it is returned. Otherwise, the method falls back to returning the main ViewBox provided by `getViewBox()`.
        """
        if axisName in self.axes:
            axisItem = self.axes[axisName]["item"]
            viewBox = axisItem.linkedView()
            if viewBox is not None:
                return viewBox
        return self.getViewBox()
