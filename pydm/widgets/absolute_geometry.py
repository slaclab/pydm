from qtpy.QtCore import QChildEvent, QEvent
from qtpy.QtWidgets import QWidget

from ..layouts.absolute_geometry_layout import AbsoluteGeometryLayout
from ..utilities import is_qt_designer
from .base import PyDMPrimitiveWidget


class PyDMAbsoluteGeometry(QWidget, PyDMPrimitiveWidget):
    """
    A QWidget with child widgets scaled when the window is stretched.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label

    Notes
    -----

    1. Having trouble with use of custom layout, skipping it for now.
    2. QWidget can have widget children but can only add them in Qt designer
       if the QWidget is the top-level widget.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # layout = AbsoluteGeometryLayout(self, margin=0, h_spacing=0, v_spacing=0)
        # self.setLayout(layout)

        self.original_size = None
        self.original_geometries = {}
        self.x_scale = None
        self.y_scale = None

    def computeScaleFactors(self, new_size):
        if self.original_size is None:
            raise ValueError("Must set 'original_sizes' first.")
        self.x_scale = new_size.width() / self.original_size.width()
        self.y_scale = new_size.height() / self.original_size.height()

    def setChildGeometry(self, child):
        original_geometry = self.original_geometries.get(child)
        if original_geometry is None:
            # return
            raise KeyError(f"No original geometry available for widget {child.__class__} .")
        x = int(self.x_scale * original_geometry.x())
        y = int(self.y_scale * original_geometry.y())
        width = int(self.x_scale * original_geometry.width())
        height = int(self.y_scale * original_geometry.height())
        child.setGeometry(x, y, width, height)

    def childEvent(self, event):
        if isinstance(event, QChildEvent):
            child = event.child()
            # print(f"DIAGNOSTIC ({__class__}.childEvent) {child.__class__=} {child.geometry()=}")
            if (
                event.type() in (QEvent.ChildAdded, QEvent.ChildPolished)
                and child not in self.original_geometries
            ):
                self.original_geometries[child] = child.geometry()
            elif (
                event.type() == QEvent.ChildRemoved
                and child in self.original_geometries
            ):
                self.original_geometries.pop(child)

    def resizeEvent(self, event):
        if is_qt_designer():
            return
        old_size = event.oldSize()
        new_size = event.size()

        # print(f"DIAGNOSTIC ({__class__}.resizeEvent) {new_size=} {event.oldSize()=}")
        # print(f"DIAGNOSTIC ({__class__}.resizeEvent) {len(self.children())=}")
        # for i, child in enumerate(self.children(), start=1):
        #     print(f"DIAGNOSTIC ({__class__}.resizeEvent) {i} {child.__class__=}  {child.geometry()}")
        # print(f"DIAGNOSTIC ({__class__}.resizeEvent) {len(self.children())=}")

        # fragile algorithm to discover when to set self.original_size & self.original_geometries
        if (
            self.original_size is None
            and (old_size.width(), old_size.height()) == (-1, -1)
            and (new_size != old_size)
        ):
            print("*"*20, "first time", "*"*20)
            self.original_size = new_size
            for child in self.children():
                if child not in self.original_geometries:
                    self.original_geometries[child] = child.geometry()

        self.computeScaleFactors(new_size)
        # print(f"DIAGNOSTIC ({__class__}.resizeEvent) {self.x_scale=} {self.y_scale=}")

        for i, child in enumerate(self.children(), start=1):
            # print(f"DIAGNOSTIC ({__class__}.resizeEvent) {i} {child.__class__=}  {child.geometry()}")
            self.setChildGeometry(child)
