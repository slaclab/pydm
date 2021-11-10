from pyqtgraph import GraphicsWidget, ViewBox
from qtpy.QtCore import Qt, Signal


class MultiAxisViewBox(ViewBox):
    """
    MultiAxisViewBox is a PyQtGraph ViewBox subclass that has support for adding multiple y axes for
    PyDM's use cases. Each unique axis will be assigned its own MultiAxisViewBox for managing its
    range and associated curves. Any events handled by the any view box will be propagated through
    to all views in the stack to ensure that the plot remains consistent with user input.

    Parameters
    ----------
    parent: QGraphicsWidget, optional
        The parent widget for this plot
    """

    # These signals will be emitted by the view when it handles these events, and will be connected
    # to the event handling code of the stacked views
    sigMouseDragged = Signal(object, object, object)
    sigMouseWheelZoomed = Signal(object, object, object)
    sigHistoryChanged = Signal(object)

    def __init__(self, parent=None):
        GraphicsWidget.__init__(self, parent)
        super(MultiAxisViewBox, self).__init__(parent=parent)

    def wheelEvent(self, ev, axis=None, fromSignal=False):
        """
        Handles user input from the mouse wheel. Propagates to any stacked views.

        Parameters
        ----------
        ev: QEvent
            The event that was generated
        axis: int
            Zero if the event happened on the x axis, one for any y axis, and None for no associated axis
        fromSignal: bool
            True if this event was generated from a signal rather than a user event. Used to ensure we only propagate
            the even once.
        """
        if axis != ViewBox.YAxis and not fromSignal:
            # This event happened within the view box area itself or the x axis so propagate to any stacked view boxes
            self.sigMouseWheelZoomed.emit(self, ev, axis)
        super(MultiAxisViewBox, self).wheelEvent(ev, axis)

    def mouseDragEvent(self, ev, axis=None, fromSignal=False):
        """
        Handles user input from a drag of the mouse. Propagates to any stacked views.

        Parameters
        ----------
        ev: QEvent
            The event that was generated
        axis: int
            Zero if the event happened on the x axis, one for any y axis, and None for no associated axis
        fromSignal: bool
            True if this event was generated from a signal rather than a user event. Used to ensure we only propagate
            the even once.
        """
        if axis != ViewBox.YAxis and not fromSignal:
            # This event happened within the view box area itself or the x axis so propagate to any stacked view boxes
            self.sigMouseDragged.emit(self, ev, axis)
        super(MultiAxisViewBox, self).mouseDragEvent(ev, axis)

    def keyPressEvent(self, ev):
        """
        Capture key presses in the current view box. Key presses are used only when mouse mode is RectMode
        The following events are implemented:
        + or = : moves forward in the zooming stack (if it exists)
        - : moves backward in the zooming stack (if it exists)
        Backspace : resets to the default auto-scale

        Parameters
        ----------
        ev: QEvent
            The key press event that was generated
        """

        ev.accept()
        if ev.text() == '-':
            self.scaleHistory(-1)
        elif ev.text() in ['+', '=']:
            self.scaleHistory(1)
        elif ev.key() == Qt.Key.Key_Backspace:
            self.scaleHistory(0)
        else:
            ev.ignore()

    def scaleHistory(self, d):
        """
        Go forwards or backwards in the stored history of zoom events in the graph. Has no effect if
        there is no history yet. Propagates to all stacked views
        Parameters
        ----------
        d: int
            1 to go forwards, -1 to go backwards, 0 to reset to the original auto-scale
        """

        self.sigHistoryChanged.emit(d)

        if len(self.axHistory) != 0:
            if d == -1 and self.axHistoryPointer != -1:
                self.axHistoryPointer -= 1
            elif d == 1 and self.axHistoryPointer != len(self.axHistory) - 1:
                self.axHistoryPointer += 1
            elif d == 0:
                self.axHistoryPointer = -1  # Reset to the beginning

            if self.axHistoryPointer == -1:
                self.enableAutoRange()
            else:
                self.showAxRect(self.axHistory[self.axHistoryPointer])
