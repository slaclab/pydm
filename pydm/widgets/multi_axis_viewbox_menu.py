from pyqtgraph.graphicsItems.ViewBox import ViewBox
from pyqtgraph.graphicsItems.ViewBox.ViewBoxMenu import ViewBoxMenu
from qtpy.QtCore import QCoreApplication, Signal
from qtpy.QtWidgets import QAction


class MultiAxisViewBoxMenu(ViewBoxMenu):
    """
    MultiAxisViewBoxMenu is a PyQtGraph ViewBoxMenu subclass to be used with MultiAxisViewBox. It can override
    the menu functionality to ensure that any selected option propagates through to each ViewBox in the plot.

    Parameters
    ----------
    view: ViewBox
        The view box this menu is associated with
    """

    # A signal indicating that the user has changed the mouse mode (left click panning vs. zooming)
    sigMouseModeChanged = Signal(object)
    # A signal indicating the user wants the default x and y axis ranges restored on this plot
    sigRestoreRanges = Signal()
    # A signal to set autorange for every view box on the plot
    sigSetAutorange = Signal(bool, bool)
    # A signal for updating the x autorange value
    sigXAutoRangeChanged = Signal(object)
    # A signal for updating the y autorange value
    sigYAutoRangeChanged = Signal(object)
    # A signal for inverting the x or y axis
    sigInvertAxis = Signal(int, bool)
    # Only panning when auto range is enabled (no scaling)
    sigAutoPan = Signal(object, object)
    # Auto range using only the visible portion of the plot when checked
    sigVisibleOnly = Signal(object, object)
    # Set the x range manually
    sigXManualRange = Signal(float, float)
    # Set the y range manually
    sigYManualRange = Signal(float, float)

    def __init__(self, view):
        super().__init__(view)
        self.restoreRangesAction = QAction(QCoreApplication.translate("ViewBox", "Restore default X/Y ranges"), self)
        self.restoreRangesAction.triggered.connect(self.restoreRanges)

        # Insert/remove/insert because there is no QMenu function for inserting based on index
        self.insertAction(self.viewAll, self.restoreRangesAction)
        self.removeAction(self.viewAll)
        self.insertAction(self.restoreRangesAction, self.viewAll)

    def set3ButtonMode(self):
        """Change the mouse left-click functionality to pan the plot"""
        super().set3ButtonMode()
        self.sigMouseModeChanged.emit("pan")

    def set1ButtonMode(self):
        """Change the mouse left-click functionality to zoom in on the plot"""
        super().set1ButtonMode()
        self.sigMouseModeChanged.emit("rect")

    def xAutoClicked(self):
        """Update the auto-range value for each view box"""
        super().xAutoClicked()
        val = self.ctrl[0].autoPercentSpin.value() * 0.01
        self.sigXAutoRangeChanged.emit(val)

    def xManualClicked(self):
        """Disable x auto-range for each view box"""
        super().xManualClicked()
        self.sigXAutoRangeChanged.emit(False)

    def xRangeTextChanged(self):
        """Manually set the x-axis range to the user's input. Range will be unchanged if input was invalid"""
        super().xRangeTextChanged()
        updated_values = self._validateRangeText(ViewBox.XAxis)
        self.sigXManualRange.emit(*updated_values)

    def yAutoClicked(self):
        """Update the y auto-range value for each view box"""
        super().yAutoClicked()
        val = self.ctrl[1].autoPercentSpin.value() * 0.01
        self.sigYAutoRangeChanged.emit(val)

    def yManualClicked(self):
        """Disable y auto-range for each view box"""
        super().yManualClicked()
        self.sigYAutoRangeChanged.emit(False)

    def yRangeTextChanged(self):
        """Manually set the y-axis range to the user's input. Range will be unchanged if input was invalid"""
        super().yRangeTextChanged()
        updated_values = self._validateRangeText(ViewBox.YAxis)
        self.sigYManualRange.emit(*updated_values)

    def xAutoPanToggled(self, autoPan: bool):
        """Toggle the auto pan status of the x-axis"""
        super().xAutoPanToggled(autoPan)
        self.sigAutoPan.emit(autoPan, None)

    def xVisibleOnlyToggled(self, autoVisible: bool):
        """Toggle the visible only status of autorange for the x-axis"""
        super().xVisibleOnlyToggled(autoVisible)
        self.sigVisibleOnly.emit(autoVisible, None)

    def yAutoPanToggled(self, autoPan: bool):
        """Toggle the auto pan status of the y-axis"""
        super().yAutoPanToggled(autoPan)
        self.sigAutoPan.emit(None, autoPan)

    def yVisibleOnlyToggled(self, autoVisible: bool):
        """Toggle the visible only status of autorange for the y-axis"""
        super().yVisibleOnlyToggled(autoVisible)
        self.sigVisibleOnly.emit(None, autoVisible)

    def yInvertToggled(self, inverted: bool):
        """Toggle the inverted status of the y-axis."""
        super().yInvertToggled(inverted)
        self.sigInvertAxis.emit(ViewBox.YAxis, inverted)

    def xInvertToggled(self, inverted: bool):
        """Toggle the inverted status of the x-axis"""
        super().xInvertToggled(inverted)
        self.sigInvertAxis.emit(ViewBox.XAxis, inverted)

    def autoRange(self):
        """Sets autorange to True for all elements on the plot"""
        self.sigSetAutorange.emit(True, True)

    def restoreRanges(self):
        """Restore the original x and y axis ranges for this plot"""
        self.sigRestoreRanges.emit()
