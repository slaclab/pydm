"""
Layout Manager for MEDM widgets.

Widgets are placed on this layout in absolute coordinates.
When the layout is resized, the manager will resize each of the
widgets in the layout.
"""

import logging

from qtpy.QtWidgets import QLayout, QVBoxLayout
from qtpy import QtDesigner

logger = logging.getLogger(__name__)


class AbsoluteGeometryLayout(QLayout):
    """
    Layout Manager for widgets laid out by absolute geometry (such as MEDM).

    Widgets are added to this layout with absolute geometry (x,y,height,width).
    When the layout is resized, the manager will resize each of the
    widgets in the layout.
    """
