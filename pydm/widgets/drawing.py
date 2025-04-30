import ast
import math
import os
import logging

from qtpy.QtWidgets import QWidget, QStyle, QStyleOption
from qtpy.QtGui import QColor, QPainter, QBrush, QPen, QPolygonF, QPixmap, QMovie
from qtpy.QtCore import Property, Qt, QPoint, QPointF, QSize, Slot, QTimer, QRectF
from qtpy.QtDesigner import QDesignerFormWindowInterface
from .base import PyDMWidget, PostParentClassInitSetup
from pydm.utilities import is_qt_designer, find_file
from typing import List, Optional

logger = logging.getLogger(__name__)

_penRuleProperties = {
    "Set Pen Color": ["penColor", QColor],
    "Set Pen Style": ["penStyle", int],
    "Set Pen Width": ["penWidth", float],
    "Set Brush Color": ["brush", QBrush],
}


def deg_to_qt(deg):
    """
    Converts from degrees to QT degrees.
    16 deg = 1 QTdeg

    Parameters
    ----------
    deg : float
        The value to convert.

    Returns
    -------
    float
        The value converted.
    """
    # Angles for Qt are in units of 1/16 of a degree
    return deg * 16


def qt_to_deg(deg):
    """
    Converts from QT degrees to degrees.
    16 deg = 1 QTdeg

    Parameters
    ----------
    deg : float
        The value to convert.

    Returns
    -------
    float
        The value converted.
    """
    # Angles for Qt are in units of 1/16 of a degree
    return deg / 16.0


class PyDMDrawing(QWidget, PyDMWidget):
    """
    Base class to be used for all PyDM Drawing Widgets.
    This class inherits from QWidget and PyDMWidget.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

    new_properties = _penRuleProperties

    def __init__(self, parent=None, init_channel=None):
        self._rotation = 0.0
        self._brush = QBrush(Qt.SolidPattern)
        self._original_brush = self._brush
        self._painter = QPainter()
        self._pen = QPen(Qt.NoPen)
        self._pen_style = Qt.NoPen
        self._pen_cap_style = Qt.SquareCap
        self._pen_join_style = Qt.MiterJoin
        self._pen_width = 0
        self._pen_color = QColor(0, 0, 0)
        self._pen.setCapStyle(self._pen_cap_style)
        self._pen.setJoinStyle(self._pen_join_style)
        self._original_pen_style = self._pen_style
        self._original_pen_color = self._pen_color
        QWidget.__init__(self, parent)
        PyDMWidget.__init__(self, init_channel=init_channel)
        self.alarmSensitiveBorder = False
        # Execute setup calls that must be done here in the widget class's __init__,
        # and after it's parent __init__ calls have completed.
        # (so we can avoid pyside6 throwing an error, see func def for more info)
        PostParentClassInitSetup(self)

    # On pyside6, we need to expilcity call pydm's base class's eventFilter() call or events
    # will not propagate to the parent classes properly.
    def eventFilter(self, obj, event):
        return PyDMWidget.eventFilter(self, obj, event)

    def sizeHint(self):
        return QSize(100, 100)

    def paintEvent(self, _):
        """
        Paint events are sent to widgets that need to update themselves,
        for instance when part of a widget is exposed because a covering
        widget was moved.

        At PyDMDrawing this method handles the alarm painting with parameters
        from the stylesheet, configures the brush, pen and calls ```draw_item```
        so the specifics can be performed for each of the drawing classes.

        Parameters
        ----------
        event : QPaintEvent
        """
        painter = QPainter(self)
        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setBrush(self._brush)
        painter.setPen(self._pen)

        self.draw_item(painter)

    def draw_item(self, painter):
        """
        The classes inheriting from PyDMDrawing must overwrite this method.
        This method translate the painter to the center point given by
        ```get_center``` and rotate the canvas by the given amount of
        degrees.
        """
        xc, yc = self.get_center()
        painter.translate(xc, yc)
        painter.rotate(-self._rotation)

    def get_center(self):
        """
        Simple calculation of the canvas' center point.

        Returns
        -------
        x, y : float
            Tuple with X and Y coordinates of the center.
        """
        return self.width() * 0.5, self.height() * 0.5

    def get_bounds(self, maxsize=False, force_no_pen=False):
        """
        Returns a tuple containing the useful area for the drawing.

        Parameters
        ----------
        maxsize : bool, default is False
            If True, width and height information are based on the
            maximum inner rectangle dimensions given by ```get_inner_max```,
            otherwise width and height will receive the widget size.

        force_no_pen : bool, default is False
            If True the pen width will not be considered when calculating
            the bounds.

        Returns
        -------
        x, y, w, h : tuple
            Tuple with X and Y coordinates followed by the maximum width
            and height.
        """
        w, h = self.width(), self.height()

        if maxsize:
            w, h = self.get_inner_max()

        xc, yc = w * 0.5, h * 0.5

        if self.has_border() and not force_no_pen:
            w = max(0, w - 2 * self._pen_width)
            h = max(0, h - 2 * self._pen_width)
            x = max(0, self._pen_width)
            y = max(0, self._pen_width)
        else:
            x = 0
            y = 0
        return x - xc, y - yc, w, h

    def has_border(self):
        """
        Check whether or not the drawing have a border based on the
        Pen Style and Pen width.

        Returns
        -------
        bool
            True if the drawing has a border, False otherwise.
        """
        if self._pen.style() != Qt.NoPen and self._pen_width > 0:
            return True
        else:
            return False

    def is_square(self):
        """
        Check if the widget has the same width and height values.

        Returns
        -------
        bool
            True in case the widget has a square shape, False otherwise.
        """
        return self.height() == self.width()

    def get_inner_max(self):
        """
        Calculates the largest inner rectangle in a rotated rectangle.
        This implementation was based on https://stackoverflow.com/a/18402507

        Returns
        -------
        w, h : tuple
            The width and height of the largest rectangle.
        """
        # Based on https://stackoverflow.com/a/18402507
        w0 = 0
        h0 = 0
        angle = math.radians(self._rotation)
        origWidth = self.width()
        origHeight = self.height()

        if origWidth == 0:
            logger.error("Invalid width. The value must be greater than {0}".format(origWidth))
            return

        if origHeight == 0:
            logger.error("Invalid height. The value must be greater than {0}".format(origHeight))
            return

        if origWidth <= origHeight:
            w0 = origWidth
            h0 = origHeight
        else:
            w0 = origHeight
            h0 = origWidth
        # Angle normalization in range [-PI..PI)
        ang = angle - math.floor((angle + math.pi) / (2 * math.pi)) * 2 * math.pi
        ang = math.fabs(ang)
        if ang > math.pi / 2:
            ang = math.pi - ang
        c = w0 / (h0 * math.sin(ang) + w0 * math.cos(ang))
        w = 0
        h = 0
        if origWidth <= origHeight:
            w = w0 * c
            h = h0 * c
        else:
            w = h0 * c
            h = w0 * c
        return w, h

    @Property(QBrush)
    def brush(self):
        """
        PyQT Property for the brush object to be used when coloring the
        drawing

        Returns
        -------
        QBrush
        """
        return self._brush

    @brush.setter
    def brush(self, new_brush):
        """
        PyQT Property for the brush object to be used when coloring the
        drawing

        Parameters
        ----------
        new_brush : QBrush
        """
        if new_brush != self._brush:
            if self._alarm_state == PyDMWidget.ALARM_NONE:
                self._original_brush = new_brush
            self._brush = new_brush
            self.update()

    @Property(Qt.PenStyle)
    def penStyle(self):
        """
        PyQT Property for the pen style to be used when drawing the border

        Returns
        -------
        Qt.PenStyle
            Index at Qt.PenStyle enum
        """
        return self._pen_style

    @penStyle.setter
    def penStyle(self, new_style):
        """
        PyQT Property for the pen style to be used when drawing the border

        Parameters
        ----------
        new_style : Qt.PenStyle
            Index at Qt.PenStyle enum
        """
        if self._alarm_state == PyDMWidget.ALARM_NONE:
            self._original_pen_style = new_style
        if new_style != self._pen_style:
            self._pen_style = new_style
            self._pen.setStyle(new_style)
            self.update()

    @Property(Qt.PenCapStyle)
    def penCapStyle(self):
        """
        PyQT Property for the pen cap to be used when drawing the border

        Returns
        -------
        int
            Index at Qt.PenCapStyle enum
        """
        return self._pen_cap_style

    @penCapStyle.setter
    def penCapStyle(self, new_style):
        """
        PyQT Property for the pen cap style to be used when drawing the border

        Parameters
        ----------
        new_style : int
            Index at Qt.PenStyle enum
        """
        if new_style != self._pen_cap_style:
            self._pen_cap_style = new_style
            self._pen.setCapStyle(new_style)
            self.update()

    @Property(Qt.PenJoinStyle)
    def penJoinStyle(self):
        """
        PyQT Property for the pen join style to be used when drawing the border

        Returns
        -------
        int
            Index at Qt.PenJoinStyle enum
        """
        return self._pen_join_style

    @penJoinStyle.setter
    def penJoinStyle(self, new_style):
        """
        PyQT Property for the pen join style to be used when drawing the border

        Parameters
        ----------
        new_style : int
            Index at Qt.PenStyle enum
        """
        if new_style != self._pen_join_style:
            self._pen_join_style = new_style
            self._pen.setJoinStyle(new_style)
            self.update()

    @Property(QColor)
    def penColor(self):
        """
        PyQT Property for the pen color to be used when drawing the border

        Returns
        -------
        QColor
        """
        return self._pen_color

    @penColor.setter
    def penColor(self, new_color):
        """
        PyQT Property for the pen color to be used when drawing the border

        Parameters
        ----------
        new_color : QColor
        """
        if self._alarm_state == PyDMWidget.ALARM_NONE:
            self._original_pen_color = new_color

        if new_color != self._pen_color:
            self._pen_color = new_color
            self._pen.setColor(new_color)
            self.update()

    @Property(float)
    def penWidth(self):
        """
        PyQT Property for the pen width to be used when drawing the border

        Returns
        -------
        float
        """
        return self._pen_width

    @penWidth.setter
    def penWidth(self, new_width):
        """
        PyQT Property for the pen width to be used when drawing the border

        Parameters
        ----------
        new_width : float
        """
        if new_width < 0:
            return
        if new_width != self._pen_width:
            self._pen_width = new_width
            self._pen.setWidthF(float(self._pen_width))
            self.update()

    @Property(float)
    def rotation(self):
        """
        PyQT Property for the counter-clockwise rotation in degrees
        to be applied to the drawing.

        Returns
        -------
        float
        """
        return self._rotation

    @rotation.setter
    def rotation(self, new_angle):
        """
        PyQT Property for the counter-clockwise rotation in degrees
        to be applied to the drawing.

        Parameters
        ----------
        new_angle : float
        """
        if new_angle != self._rotation:
            self._rotation = new_angle
            self.update()

    def alarm_severity_changed(self, new_alarm_severity):
        PyDMWidget.alarm_severity_changed(self, new_alarm_severity)
        if new_alarm_severity == PyDMWidget.ALARM_NONE:
            if self._original_brush is not None:
                self.brush = self._original_brush
            if self._original_pen_color is not None:
                self.penColor = self._original_pen_color
            if self._original_pen_style is not None:
                self.penStyle = self._original_pen_style


class PyDMDrawingLineBase(PyDMDrawing):
    """
    A base class for single and poly line widgets.
    This class inherits from PyDMDrawing.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

    def __init__(self, parent=None, init_channel=None):
        super().__init__(parent, init_channel)
        self.penStyle = Qt.SolidLine
        self.penWidth = 1
        self._arrow_size = 6  # 6 is arbitrary size that looked good for default, not in any specific 'units'
        self._arrow_end_point_selection = False
        self._arrow_start_point_selection = False
        self._arrow_mid_point_selection = False
        self._arrow_mid_point_flipped = False

    @Property(int)
    def arrowSize(self) -> int:
        """
        Size to render line arrows.

        Returns
        -------
        bool
        """
        return self._arrow_size

    @arrowSize.setter
    def arrowSize(self, new_size) -> None:
        """
        Size to render line arrows.

        Parameters
        -------
        new_selection : bool
        """
        if self._arrow_size != new_size:
            self._arrow_size = new_size
            self.update()

    @Property(bool)
    def arrowEndPoint(self) -> bool:
        """
        If True, an arrow will be drawn at the end of the line.

        Returns
        -------
        bool
        """
        return self._arrow_end_point_selection

    @arrowEndPoint.setter
    def arrowEndPoint(self, new_selection) -> None:
        """
        If True, an arrow will be drawn at the end of the line.

        Parameters
        -------
        new_selection : bool
        """
        if self._arrow_end_point_selection != new_selection:
            self._arrow_end_point_selection = new_selection
            self.update()

    @Property(bool)
    def arrowStartPoint(self) -> bool:
        """
        If True, an arrow will be drawn at the start of the line.

        Returns
        -------
        bool
        """
        return self._arrow_start_point_selection

    @arrowStartPoint.setter
    def arrowStartPoint(self, new_selection) -> None:
        """
        If True, an arrow will be drawn at the start of the line.

        Parameters
        -------
        new_selection : bool
        """
        if self._arrow_start_point_selection != new_selection:
            self._arrow_start_point_selection = new_selection
            self.update()

    @Property(bool)
    def arrowMidPoint(self) -> bool:
        """
        If True, an arrow will be drawn at the midpoint of the line.
        Returns
        -------
        bool
        """
        return self._arrow_mid_point_selection

    @arrowMidPoint.setter
    def arrowMidPoint(self, new_selection) -> None:
        """
        If True, an arrow will be drawn at the midpoint of the line.
        Parameters
        -------
        new_selection : bool
        """
        if self._arrow_mid_point_selection != new_selection:
            self._arrow_mid_point_selection = new_selection
            self.update()

    @Property(bool)
    def flipMidPointArrow(self) -> bool:
        """
        Flips the direction of the midpoint arrow.

        Returns
        -------
        bool
        """
        return self._arrow_mid_point_flipped

    @flipMidPointArrow.setter
    def flipMidPointArrow(self, new_selection) -> None:
        """
        Flips the direction of the midpoint arrow.

        Parameters
        -------
        new_selection : bool
        """
        if self._arrow_mid_point_flipped != new_selection:
            self._arrow_mid_point_flipped = new_selection
            self.update()

    @staticmethod
    def _arrow_points(startpoint, endpoint, height, width) -> QPolygonF:
        """
        Returns the three points needed to make a triangle with .drawPolygon
        """
        diff_x = startpoint.x() - endpoint.x()
        diff_y = startpoint.y() - endpoint.y()

        length = max(math.sqrt(diff_x**2 + diff_y**2), 1.0)

        norm_x = diff_x / length
        norm_y = diff_y / length

        perp_x = -norm_y
        perp_y = norm_x

        left_x = endpoint.x() + height * norm_x + width * perp_x
        left_y = endpoint.y() + height * norm_y + width * perp_y
        right_x = endpoint.x() + height * norm_x - width * perp_x
        right_y = endpoint.y() + height * norm_y - width * perp_y

        left = QPointF(left_x, left_y)
        right = QPointF(right_x, right_y)

        return QPolygonF([left, endpoint, right])


class PyDMDrawingLine(PyDMDrawingLineBase):
    """
    A widget with a line drawn in it.
    This class inherits from PyDMDrawingLineBase.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

    new_properties = _penRuleProperties

    def __init__(self, parent=None, init_channel=None):
        super().__init__(parent, init_channel)

    def draw_item(self, painter) -> None:
        """
        Draws the line after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super().draw_item(painter)
        x, y, w, h = self.get_bounds()

        # Figure out how long to make the line to touch the bounding box
        # Length varies depending on rotation

        # Find the quadrant 1 angle equivalent
        angle = self._rotation % 360
        if 90 < angle <= 180:
            angle = 180 - angle
        elif 180 < angle <= 270:
            angle = angle - 180
        elif 270 < angle <= 360:
            angle = 360 - angle
        angle_rad = math.radians(angle)

        # Find the angle of the rop right corner of the bounding box
        try:
            critical_angle = math.atan(h / w)
        except ZeroDivisionError:
            critical_angle = math.pi / 2

        # Pick a length based on which side we intersect with
        if angle_rad > critical_angle:
            try:
                length = h / math.sin(angle_rad)
            except ZeroDivisionError:
                length = w
        else:
            try:
                length = w / math.cos(angle_rad)
            except ZeroDivisionError:
                length = h

        # Define endpoints potentially outside the bounding box
        # Will land on the bounding box after rotation
        midpoint = x + w / 2
        start_point = QPointF(midpoint - length / 2, 0)
        end_point = QPointF(midpoint + length / 2, 0)
        mid_point = QPointF(midpoint, 0)

        # Draw the line
        painter.drawLine(start_point, end_point)

        # Draw the arrows
        if self._arrow_end_point_selection:
            points = self._arrow_points(start_point, end_point, self._arrow_size, self._arrow_size)
            painter.drawPolygon(points)

        if self._arrow_start_point_selection:
            points = self._arrow_points(end_point, start_point, self._arrow_size, self._arrow_size)
            painter.drawPolygon(points)

        if self._arrow_mid_point_selection:
            if self._arrow_mid_point_flipped:
                points = self._arrow_points(start_point, mid_point, self._arrow_size, self._arrow_size)
            else:
                points = self._arrow_points(end_point, mid_point, self._arrow_size, self._arrow_size)
            painter.drawPolygon(points)


class PyDMDrawingPolyline(PyDMDrawingLineBase):
    """
    A widget with a multi-segment, piecewise-linear line drawn in it.
    This class inherits from PyDMDrawingLineBase.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

    def __init__(self, parent=None, init_channel=None):
        super().__init__(parent, init_channel)
        self._points = []

    def draw_item(self, painter) -> None:
        """
        Draws the segmented line after setting up the canvas with a call to
        ``PyDMDrawing.draw_item``.
        """
        super().draw_item(painter)
        x, y, w, h = self.get_bounds()

        def p2d(pt):
            "convert point to drawing coordinates"
            # drawing coordinates are centered: (0,0) is in center
            # our points are absolute: (0,0) is upper-left corner
            if isinstance(pt, str):
                # 2022-05-11: needed for backwards compatibility support
                # PyDM releases up to v1.15.1
                # adl2pydm tags up to 0.0.2
                pt = tuple(map(int, pt.split(",")))
            u, v = pt
            return QPointF(u + x, v + y)

        if len(self._points) > 1:
            for i, p1 in enumerate(self._points[:-1]):
                painter.drawLine(p2d(p1), p2d(self._points[i + 1]))
                if self._arrow_mid_point_selection:
                    point1 = p2d(p1)
                    point2 = p2d(self._points[i + 1])
                    if self._arrow_mid_point_flipped:
                        point1, point2 = point2, point1  # swap values

                    # arrow points at midpoint of line
                    midpoint_x = (point1.x() + point2.x()) / 2
                    midpoint_y = (point1.y() + point2.y()) / 2
                    midpoint = QPointF(midpoint_x, midpoint_y)
                    points = self._arrow_points(
                        point1, midpoint, self._arrow_size, self._arrow_size
                    )  # 6 = arbitrary arrow size
                    painter.drawPolygon(points)

        # Draw the arrows
        # While we enforce >=2 points when user adds points, we need to check '(len(self._points) > 0)' here so we
        # don't break trying to add arrows to new polyline with no points yet.
        if self._arrow_end_point_selection and (len(self._points) > 0) and (len(self._points[1]) >= 2):
            points = self._arrow_points(p2d(self._points[1]), p2d(self._points[0]), self._arrow_size, self._arrow_size)
            painter.drawPolygon(points)

        if self._arrow_start_point_selection and (len(self._points) > 0) and (len(self._points[1]) >= 2):
            points = self._arrow_points(
                p2d(self._points[len(self._points) - 2]),
                p2d(self._points[len(self._points) - 1]),
                self._arrow_size,
                self._arrow_size,
            )
            painter.drawPolygon(points)

    def getPoints(self) -> List[str]:
        """Convert internal points representation for use as QStringList."""
        points = [f"{pt[0]}, {pt[1]}" for pt in self._points]
        return points

    def _validator(self, value) -> bool:
        """
        ensure that `value` has correct form

        Parameters
        ----------
        value : [ordered pairs]
            List of strings representing ordered pairs
            of integer coordinates.  Each ordered pair
            is a tuple or list.

        Returns
        ----------
        verified : [ordered pairs]
            List of `tuple(number, number)`.

        """

        def isfloat(value) -> bool:
            if isinstance(value, str):
                value = value.strip()
            try:
                float(value)
                return True
            except Exception:
                return False

        def validate_point(i, point) -> Optional[List[float]]:
            """Ignore (instead of fail on) any of these pathologies."""
            if isinstance(point, str):
                try:
                    point = ast.literal_eval(point)
                except SyntaxError:
                    logger.error(
                        "point %d must be two numbers, comma-separated, received '%s'",
                        i,
                        pt,
                    )
                    return
            if not isinstance(point, (list, tuple)) or len(point) != 2:
                logger.error(
                    "point %d must be two numbers, comma-separated, received '%s'",
                    i,
                    pt,
                )
                return
            try:
                point = list(map(float, point))  # ensure all values are float
            except ValueError:
                logger.error("point %d content must be numeric, received '%s'", i, pt)
                return

            return point

        verified = []
        for i, pt in enumerate(value, start=1):
            point = validate_point(i, pt)
            if point is not None:
                verified.append(point)

        return verified

    def setPoints(self, value) -> None:
        verified = self._validator(value)
        if verified is not None:
            if len(verified) < 2:
                logger.error("Must have two or more points")
                return

            self._points = verified
            self.update()

    def resetPoints(self) -> None:
        self._points = []
        self.update()

    points = Property("QStringList", getPoints, setPoints, resetPoints)


class PyDMDrawingImage(PyDMDrawing):
    """
    Renders an image given by the ``filename`` property.
    This class inherits from PyDMDrawing.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.

    Attributes
    ----------
    null_color : Qt.Color
        QColor to fill the image if the filename is not found.
    """

    null_color = Qt.gray

    def __init__(self, parent=None, init_channel=None, filename=""):
        super().__init__(parent, init_channel)
        hint = super().sizeHint()
        self._pixmap = QPixmap(hint)
        self._pixmap.fill(self.null_color)
        self._aspect_ratio_mode = Qt.KeepAspectRatio
        self._movie = None
        self._recursive_image_search = False
        self._file = None
        # Make sure we don't set a non-existent file
        if filename:
            self.filename = filename
        # But we always have an internal value to reference
        else:
            self._file = filename
        if is_qt_designer():  # pragma: no cover
            designer_window = self.get_designer_window()
            if designer_window is not None:
                designer_window.fileNameChanged.connect(self.designer_form_saved)
                QTimer.singleShot(200, self.reload_image)

    def get_designer_window(self):  # pragma: no cover
        # Internal function to find the designer window that owns this widget.
        p = self.parent()
        while p is not None:
            if isinstance(p, QDesignerFormWindowInterface):
                return p
            p = p.parent()
        return None

    @Slot(str)
    def designer_form_saved(self, filename):  # pragma: no cover
        self.filename = self._file

    def reload_image(self) -> None:
        self.filename = self._file

    @Property(bool)
    def recursiveImageSearch(self) -> bool:
        """
        Whether or not to search for a provided image file recursively
        in subfolders relative to the location of this display.

        Returns
        -------
        bool
            If recursive search is enabled.
        """
        return self._recursive_image_search

    @recursiveImageSearch.setter
    def recursiveImageSearch(self, new_value) -> None:
        """
        Set whether or not to search for a provided image file recursively
        in subfolders relative to the location of this image.

        Parameters
        ----------
        new_value
            If recursive search should be enabled.
        """
        self._recursive_image_search = new_value

    @Property(str)
    def filename(self) -> str:
        """
        The filename of the image to be displayed.
        This can be an absolute or relative path to the image file.

        Returns
        -------
        str
            The filename configured.
        """
        return self._file

    @filename.setter
    def filename(self, new_file) -> None:
        """
        The filename of the image to be displayed.

        This file can be either relative to the ``.ui`` file or absolute. If
        the path does not exist, a shape of ``.null_color`` will be displayed
        instead.

        Parameters
        -------
        new_file : str
            The filename to be used
        """
        # Expand user (~ or ~user) and environment variables.
        pixmap = None
        self._file = new_file
        abs_path = os.path.expanduser(os.path.expandvars(self._file))
        # Find the absolute path relative to UI
        if not os.path.isabs(abs_path):
            parent_display = self.find_parent_display()
            base_path = None
            if parent_display:
                base_path = os.path.dirname(parent_display.loaded_file())
            abs_path = find_file(abs_path, base_path=base_path, subdir_scan_enabled=self._recursive_image_search)
            if not abs_path:
                logger.error("Unable to find full filepath for %s", self._file)
                return

        # Check that the path exists
        if os.path.isfile(abs_path):
            if self._movie is not None:
                self._movie.stop()
                self._movie.deleteLater()
                self._movie = None
            if not abs_path.endswith(".gif"):
                pixmap = QPixmap(abs_path)
            else:
                self._movie = QMovie(abs_path, parent=self)
                self._movie.setCacheMode(QMovie.CacheAll)
                self._movie.frameChanged.connect(self.movie_frame_changed)
                if self._movie.frameCount() > 1:
                    self._movie.finished.connect(self.movie_finished)
                self._movie.start()

        # Return a blank image if we don't have a valid path
        else:
            # Warn the user loudly if their file does not exist, but avoid
            # doing this in Designer as this spams the user as they are typing
            if not is_qt_designer():  # pragma: no cover
                logger.error("Image file  %r does not exist", abs_path)
            pixmap = QPixmap(self.sizeHint())
            pixmap.fill(self.null_color)
        # Update the display
        if pixmap is not None:
            self._pixmap = pixmap
            self.update()

    def sizeHint(self):
        if self._pixmap.size().isEmpty():
            return super().sizeHint()
        return self._pixmap.size()

    @Property(Qt.AspectRatioMode)
    def aspectRatioMode(self):
        """
        PyQT Property for aspect ratio mode to be used when rendering
        the image

        Returns
        -------
        int
            Index at Qt.AspectRatioMode enum
        """
        return self._aspect_ratio_mode

    @aspectRatioMode.setter
    def aspectRatioMode(self, new_mode):
        """
        PyQT Property for aspect ratio mode to be used when rendering
        the image

        Parameters
        ----------
        new_mode : int
            Index at Qt.AspectRatioMode enum
        """
        if new_mode != self._aspect_ratio_mode:
            self._aspect_ratio_mode = new_mode
            self.update()

    def draw_item(self, painter):
        """
        Draws the image after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super().draw_item(painter)
        x, y, w, h = self.get_bounds(maxsize=True, force_no_pen=True)
        if not isinstance(self._pixmap, QMovie):
            _scaled = self._pixmap.scaled(int(w), int(h), self._aspect_ratio_mode, Qt.SmoothTransformation)
            # Make sure the image is centered if smaller than the widget itself
            if w > _scaled.width():
                logger.debug("Centering image horizontally ...")
                x += (w - _scaled.width()) / 2
            if h > _scaled.height():
                logger.debug("Centering image vertically ...")
                y += (h - _scaled.height()) / 2
            painter.drawPixmap(QPointF(x, y), _scaled)

    def movie_frame_changed(self, frame_no):
        """
        Callback executed when a new frame is available at the QMovie.

        Parameters
        ----------
        frame_no : int
            The new frame index

        Returns
        -------
        None

        """
        if self._movie is None:
            return
        curr_pixmap = self._movie.currentPixmap()
        self._pixmap = curr_pixmap
        self.update()

    def movie_finished(self):
        """
        Callback executed when the movie is finished.

        Returns
        -------
        None
        """
        if self._movie is None:
            return

        self._movie.start()


class PyDMDrawingRectangle(PyDMDrawing):
    """
    A widget with a rectangle drawn in it.
    This class inherits from PyDMDrawing.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

    def __init__(self, parent=None, init_channel=None):
        super().__init__(parent, init_channel)

    def draw_item(self, painter):
        """
        Draws the rectangle after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super().draw_item(painter)
        x, y, w, h = self.get_bounds(maxsize=True)
        painter.drawRect(QRectF(x, y, w, h))


class PyDMDrawingTriangle(PyDMDrawing):
    """
    A widget with a triangle drawn in it.
    This class inherits from PyDMDrawing.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

    def __init__(self, parent=None, init_channel=None):
        super().__init__(parent, init_channel)

    def _calculate_drawing_points(self, x, y, w, h):
        return [QPointF(x, h / 2.0), QPointF(x, y), QPointF(w / 2.0, y)]

    def draw_item(self, painter):
        """
        Draws the triangle after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super().draw_item(painter)
        x, y, w, h = self.get_bounds(maxsize=True)
        points = self._calculate_drawing_points(x, y, w, h)

        painter.drawPolygon(QPolygonF(points))


class PyDMDrawingEllipse(PyDMDrawing):
    """
    A widget with an ellipse drawn in it.
    This class inherits from PyDMDrawing.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

    def __init__(self, parent=None, init_channel=None):
        super().__init__(parent, init_channel)

    def draw_item(self, painter):
        """
        Draws the ellipse after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super().draw_item(painter)
        maxsize = not self.is_square()
        _, _, w, h = self.get_bounds(maxsize=maxsize)
        painter.drawEllipse(QPoint(0, 0), w / 2.0, h / 2.0)


class PyDMDrawingCircle(PyDMDrawing):
    """
    A widget with a circle drawn in it.
    This class inherits from PyDMDrawing.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

    def __init__(self, parent=None, init_channel=None):
        super().__init__(parent, init_channel)

    def _calculate_radius(self, width, height):
        return min(width, height) / 2.0

    def draw_item(self, painter):
        """
        Draws the circle after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super().draw_item(painter)
        _, _, w, h = self.get_bounds()
        r = self._calculate_radius(w, h)
        painter.drawEllipse(QPoint(0, 0), r, r)


class PyDMDrawingArc(PyDMDrawing):
    """
    A widget with an arc drawn in it.
    This class inherits from PyDMDrawing.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

    new_properties = {"Start Angle": ["startAngle", float], "Span Angle": ["spanAngle", float]}

    def __init__(self, parent=None, init_channel=None):
        super().__init__(parent, init_channel)
        self.penStyle = Qt.SolidLine
        self.penWidth = 1.0
        self._start_angle = 0
        self._span_angle = deg_to_qt(90)

    @Property(float)
    def startAngle(self):
        """
        PyQT Property for the start angle in degrees

        Returns
        -------
        float
            Angle in degrees
        """
        return qt_to_deg(self._start_angle)

    @startAngle.setter
    def startAngle(self, new_angle):
        """
        PyQT Property for the start angle in degrees

        Parameters
        ----------
        new_angle : float
            Angle in degrees
        """
        if deg_to_qt(new_angle) != self._start_angle:
            self._start_angle = deg_to_qt(new_angle)
            self.update()

    @Property(float)
    def spanAngle(self):
        """
        PyQT Property for the span angle in degrees

        Returns
        -------
        float
            Angle in degrees
        """
        return qt_to_deg(self._span_angle)

    @spanAngle.setter
    def spanAngle(self, new_angle):
        """
        PyQT Property for the span angle in degrees

        Parameters
        ----------
        new_angle : float
            Angle in degrees
        """
        if deg_to_qt(new_angle) != self._span_angle:
            self._span_angle = deg_to_qt(new_angle)
            self.update()

    def draw_item(self, painter):
        """
        Draws the arc after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super().draw_item(painter)
        maxsize = not self.is_square()
        x, y, w, h = self.get_bounds(maxsize=maxsize)
        painter.drawArc(QRectF(x, y, w, h), int(self._start_angle), int(self._span_angle))


class PyDMDrawingPie(PyDMDrawingArc):
    """
    A widget with a pie drawn in it.
    This class inherits from PyDMDrawing.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

    def __init__(self, parent=None, init_channel=None):
        super().__init__(parent, init_channel)

    def draw_item(self, painter):
        """
        Draws the pie after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super().draw_item(painter)
        maxsize = not self.is_square()
        x, y, w, h = self.get_bounds(maxsize=maxsize)
        painter.drawPie(QRectF(x, y, w, h), int(self._start_angle), int(self._span_angle))


class PyDMDrawingChord(PyDMDrawingArc):
    """
    A widget with a chord drawn in it.
    This class inherits from PyDMDrawing.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

    def __init__(self, parent=None, init_channel=None):
        super().__init__(parent, init_channel)

    def draw_item(self, painter):
        """
        Draws the chord after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super().draw_item(painter)
        maxsize = not self.is_square()
        x, y, w, h = self.get_bounds(maxsize=maxsize)
        painter.drawChord(QRectF(x, y, w, h), int(self._start_angle), int(self._span_angle))


class PyDMDrawingPolygon(PyDMDrawing):
    """
    A widget with a polygon drawn in it.
    This class inherits from PyDMDrawing.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

    def __init__(self, parent=None, init_channel=None):
        super().__init__(parent, init_channel)
        self._num_points = 3

    @Property(int)
    def numberOfPoints(self):
        """
        PyQT Property for the number of points

        Returns
        -------
        int
            Number of Points
        """
        return self._num_points

    @numberOfPoints.setter
    def numberOfPoints(self, points):
        if points >= 3 and points != self._num_points:
            self._num_points = points
            self.update()

    def _calculate_drawing_points(self, x, y, w, h):
        # (x + r*cos(theta), y + r*sin(theta))
        r = min(w, h) / 2.0
        deg_step = 360.0 / self._num_points

        points = []
        for i in range(self._num_points):
            xp = r * math.cos(math.radians(deg_step * i))
            yp = r * math.sin(math.radians(deg_step * i))
            points.append(QPointF(xp, yp))

        return points

    def draw_item(self, painter):
        """
        Draws the Polygon after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super().draw_item(painter)
        not self.is_square()
        x, y, w, h = self.get_bounds(maxsize=not self.is_square())
        poly = self._calculate_drawing_points(x, y, w, h)
        painter.drawPolygon(QPolygonF(poly))


class PyDMDrawingIrregularPolygon(PyDMDrawingPolyline):
    """
    A widget contains an irregular polygon (arbitrary number of vertices, arbitrary lengths).

    This is a special case of the PyDMDrawingPolyline, adding the requirement that
    the last point is always identical to the first point.

    This widget is created for compatibility with MEDM's *polygon* widget.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

    def getPoints(self):
        return super().getPoints()

    def resetPoints(self):
        super().resetPoints()

    def setPoints(self, points):
        verified = self._validator(points)
        if verified is not None:
            if len(verified) > 1:
                if verified[0] != verified[-1]:
                    verified.append(verified[0])  # close the polygon

            if len(verified) < 3:
                logger.error("Must have three or more points")
                return

            self._points = verified
            self.update()

    points = Property("QStringList", getPoints, setPoints, resetPoints)
