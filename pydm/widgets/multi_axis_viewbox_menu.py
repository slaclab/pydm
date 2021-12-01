from pyqtgraph.graphicsItems.ViewBox.ViewBoxMenu import ViewBoxMenu
from qtpy.QtCore import Signal


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

    def __init__(self, view):
        super(MultiAxisViewBoxMenu, self).__init__(view)

    def set3ButtonMode(self):
        """ Change the mouse left-click functionality to pan the plot """
        super(MultiAxisViewBoxMenu, self).set3ButtonMode()
        self.sigMouseModeChanged.emit('pan')

    def set1ButtonMode(self):
        """ Change the mouse left-click functionality to zoom in on the plot """
        super(MultiAxisViewBoxMenu, self).set1ButtonMode()
        self.sigMouseModeChanged.emit('rect')
