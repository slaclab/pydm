"""
Layout Manager for MEDM widgets.

Widgets are placed on this layout in absolute coordinates.
When the layout is resized, the manager will resize each of the
widgets in the layout.
"""

import logging

from qtpy.QtCore import QPoint, QRect, QSize
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QLayout, QSizePolicy, QStyle

logger = logging.getLogger(__name__)


class AbsoluteGeometryLayout(QLayout):
    """
    Layout Manager for widgets laid out by absolute geometry (such as MEDM).

    Widgets are added to this layout with absolute geometry (x,y,height,width).
    When the layout is resized, the manager will resize each of the
    widgets in the layout.
    """

    def __init__(self, parent=None, margin=-1, h_spacing=-1, v_spacing=-1):
        QLayout.__init__(self, parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self.m_h_space = h_spacing
        self.m_v_space = v_spacing
        self.item_list = []

    def addItem(self, item):
        print(f"DIAGNOSTIC ({__class__}.addItem) {item=}")
        self.item_list.append(item)

    def horizontalSpacing(self):
        if self.m_h_space >= 0:
            return self.m_h_space
        else:
            return self.smart_spacing(QStyle.PM_LayoutHorizontalSpacing)

    def verticalSpacing(self):
        if self.m_v_space >= 0:
            return self.m_v_space
        else:
            return self.smart_spacing(QStyle.PM_LayoutVerticalSpacing)

    def count(self):
        print(f"DIAGNOSTIC ({__class__}.count) {self.item_list=}")
        return len(self.item_list)

    def itemAt(self, index):
        if index >= 0 and index < len(self.item_list):
            return self.item_list[index]
        else:
            return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.item_list):
            return self.item_list.pop(index)
        else:
            return None

    def expandingDirections(self):
        # return Qt.Orientations(0)
        return Qt.Horizontal | Qt.Vertical

    def hasHeightForWidth(self):
        return False

    def heightForWidth(self, width):
        return self.do_layout(QRect(0,0, width, 0), True)

    def setGeometry(self, rect):
        print(f"DIAGNOSTIC ({__class__}.setGeometry) {rect=}")
        super(AbsoluteGeometryLayout, self).setGeometry(rect)
        self.do_layout(rect, False)
        print(f"DIAGNOSTIC ({__class__}.setGeometry) {self.item_list=}")

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        #size += QSize(2*self.margin(), 2*self.margin())
        size += QSize(2*8, 2*8)
        return size

    def do_layout(self, rect, test_only):
        (left, top, right, bottom) = self.getContentsMargins()
        effective_rect = rect.adjusted(left, top, -right, -bottom)
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0
        for item in self.item_list:
            wid = item.widget()
            space_x = self.horizontalSpacing()
            if space_x == -1:
                space_x = wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            space_y = self.verticalSpacing()
            if space_y == -1:
                space_y = wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = next_x
            line_height = max(line_height, item.sizeHint().height())
        return y + line_height - rect.y() + bottom

    def smart_spacing(self, pm):
        parent = self.parent()
        if not parent:
            return -1
        elif parent.isWidgetType():
            return parent.style().pixelMetric(pm, None, parent)
        else:
            return parent.spacing()
