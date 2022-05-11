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

    def __init__(self, view):
        super(MultiAxisViewBoxMenu, self).__init__(view)
        self.restoreRangesAction = QAction(QCoreApplication.translate("ViewBox", "Restore default X/Y ranges"), self)
        self.restoreRangesAction.triggered.connect(self.restoreRanges)

        # Insert/remove/insert because there is no QMenu function for inserting based on index
        self.insertAction(self.viewAll, self.restoreRangesAction)
        self.removeAction(self.viewAll)
        self.insertAction(self.restoreRangesAction, self.viewAll)

    def set3ButtonMode(self):
        """ Change the mouse left-click functionality to pan the plot """
        super(MultiAxisViewBoxMenu, self).set3ButtonMode()
        self.sigMouseModeChanged.emit('pan')

    def set1ButtonMode(self):
        """ Change the mouse left-click functionality to zoom in on the plot """
        super(MultiAxisViewBoxMenu, self).set1ButtonMode()
        self.sigMouseModeChanged.emit('rect')

    def xAutoClicked(self):
        """ Update the auto-range value for each view box """
        super().xAutoClicked()
        val = self.ctrl[0].autoPercentSpin.value() * 0.01
        self.sigXAutoRangeChanged.emit(val)

    def xManualClicked(self):
        """ Disable x auto-range for each view box """
        super().xManualClicked()
        self.sigXAutoRangeChanged.emit(False)

    def autoRange(self):
        """ Sets autorange to True for all elements on the plot """
        self.sigSetAutorange.emit(True, True)

    def restoreRanges(self):
        """ Restore the original x and y axis ranges for this plot """
        self.sigRestoreRanges.emit()
