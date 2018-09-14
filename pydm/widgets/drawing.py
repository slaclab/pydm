import math
import os
import logging

from qtpy.QtWidgets import (QApplication, QWidget,
                            QStyle, QStyleOption)
from qtpy.QtGui import (QColor, QPainter, QBrush, QPen, QPolygon, QPolygonF, QPixmap,
                            QMovie)
from qtpy.QtCore import Property, Qt, QPoint, QPointF, QSize, Slot
from qtpy.QtDesigner import QDesignerFormWindowInterface
from .base import PyDMWidget
from ..utilities import is_pydm_app

logger = logging.getLogger(__name__)


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
    def __init__(self, parent=None, init_channel=None):
        self._rotation = 0.0
        self._brush = QBrush(Qt.SolidPattern)
        self._original_brush = None
        self._painter = QPainter()
        self._pen = QPen(Qt.NoPen)
        self._pen_style = Qt.NoPen
        self._pen_width = 0
        self._pen_color = QColor(0, 0, 0)
        self._original_pen_style = self._pen_style
        self._original_pen_color = self._pen_color
        QWidget.__init__(self, parent)
        PyDMWidget.__init__(self, init_channel=init_channel)
        self.alarmSensitiveBorder = False

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
        self._painter.begin(self)
        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, self._painter, self)
        self._painter.setRenderHint(QPainter.Antialiasing)

        self._painter.setBrush(self._brush)
        self._painter.setPen(self._pen)

        self.draw_item()
        self._painter.end()

    def draw_item(self):
        """
        The classes inheriting from PyDMDrawing must overwrite this method.
        This method translate the painter to the center point given by
        ```get_center``` and rotate the canvas by the given amount of
        degrees.
        """
        xc, yc = self.get_center()
        self._painter.translate(xc, yc)
        self._painter.rotate(-self._rotation)

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

        if (origWidth <= origHeight):
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
        if (origWidth <= origHeight):
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
        int
            Index at Qt.PenStyle enum
        """
        return self._pen_style

    @penStyle.setter
    def penStyle(self, new_style):
        """
        PyQT Property for the pen style to be used when drawing the border

        Parameters
        ----------
        new_style : int
            Index at Qt.PenStyle enum
        """
        if self._alarm_state == PyDMWidget.ALARM_NONE:
            self._original_pen_style = new_style
        if new_style != self._pen_style:
            self._pen_style = new_style
            self._pen.setStyle(new_style)
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
            self._pen.setWidth(self._pen_width)
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

class PyDMDrawingLine(PyDMDrawing):
    """
    A widget with a line drawn in it.
    This class inherits from PyDMDrawing.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """
    def __init__(self, parent=None, init_channel=None):
        super(PyDMDrawingLine, self).__init__(parent, init_channel)

    def draw_item(self):
        """
        Draws the line after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super(PyDMDrawingLine, self).draw_item()
        x, _, w, _ = self.get_bounds()
        self._painter.drawRect(x, 0, w, 1)


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
        super(PyDMDrawingImage, self).__init__(parent, init_channel)
        hint = super(PyDMDrawingImage, self).sizeHint()
        self._pixmap = QPixmap(hint)
        self._pixmap.fill(self.null_color)
        self._aspect_ratio_mode = Qt.KeepAspectRatio
        self._movie = None
        # Make sure we don't set a non-existant file
        if filename:
            self.filename = filename
        # But we always have an internal value to reference
        else:
            self._file = filename
        if not is_pydm_app():
            designer_window = self.get_designer_window()
            if designer_window is not None:
                designer_window.fileNameChanged.connect(self.designer_form_saved)

    def get_designer_window(self):
        # Internal function to find the designer window that owns this widget.
        p = self.parent()
        while p is not None:
            if isinstance(p, QDesignerFormWindowInterface):
                return p
            p = p.parent()
        return None

    @Slot(str)
    def designer_form_saved(self, filename):
        self.filename = self._file

    @Property(str)
    def filename(self):
        """
        The filename of the image to be displayed.
        This can be an absolute or relative path to the display file.

        Returns
        -------
        str
            The filename configured.
        """
        return self._file

    @filename.setter
    def filename(self, new_file):
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
        is_app = is_pydm_app()
        # Find the absolute path relative to UI
        if not os.path.isabs(abs_path):
            try:
                # Based on the QApplication
                if is_app:
                    abs_path = QApplication.instance().get_path(abs_path)
                # Based on the QtDesigner
                else:
                    p = self.get_designer_window()
                    if p is not None:
                        ui_dir = p.absoluteDir().absolutePath()
                        abs_path = os.path.join(ui_dir, abs_path)
            except Exception:
                logger.exception("Unable to find full filepath for %s",
                                 self._file)
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
            if is_app:
                logger.error("Image file  %r does not exist", abs_path)
            pixmap = QPixmap(self.sizeHint())
            pixmap.fill(self.null_color)
        # Update the display
        if pixmap is not None:
            self._pixmap = pixmap
            self.update()

    def sizeHint(self):
        if self._pixmap.size().isEmpty():
            return super(PyDMDrawingImage, self).sizeHint()
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

    def draw_item(self):
        """
        Draws the image after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super(PyDMDrawingImage, self).draw_item()
        x, y, w, h = self.get_bounds(maxsize=True, force_no_pen=True)
        if not isinstance(self._pixmap, QMovie):
            _scaled = self._pixmap.scaled(w, h, self._aspect_ratio_mode,
                                          Qt.SmoothTransformation)
            # Make sure the image is centered if smaller than the widget itself
            if w > _scaled.width():
                logger.debug("Centering image horizontally ...")
                x += (w-_scaled.width())/2
            if h > _scaled.height():
                logger.debug("Centering image vertically ...")
                y += (h - _scaled.height())/2
            self._painter.drawPixmap(x, y, _scaled)

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
        super(PyDMDrawingRectangle, self).__init__(parent, init_channel)

    def draw_item(self):
        """
        Draws the rectangle after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super(PyDMDrawingRectangle, self).draw_item()
        x, y, w, h = self.get_bounds(maxsize=True)
        self._painter.drawRect(x, y, w, h)


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
        super(PyDMDrawingTriangle, self).__init__(parent, init_channel)

    def _calculate_drawing_points(self, x, y, w, h):
        return [
            QPoint(x, h / 2.0),
            QPoint(x, y),
            QPoint(w / 2.0, y)
        ]

    def draw_item(self):
        """
        Draws the triangle after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super(PyDMDrawingTriangle, self).draw_item()
        x, y, w, h = self.get_bounds(maxsize=True)
        points = self._calculate_drawing_points(x, y, w, h)

        self._painter.drawPolygon(QPolygon(points))


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
        super(PyDMDrawingEllipse, self).__init__(parent, init_channel)

    def draw_item(self):
        """
        Draws the ellipse after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super(PyDMDrawingEllipse, self).draw_item()
        maxsize = not self.is_square()
        _, _, w, h = self.get_bounds(maxsize=maxsize)
        self._painter.drawEllipse(QPoint(0, 0), w / 2.0, h / 2.0)

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
        super(PyDMDrawingCircle, self).__init__(parent, init_channel)

    def _calculate_radius(self, width, height):
        return min(width, height) / 2.0

    def draw_item(self):
        """
        Draws the circle after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super(PyDMDrawingCircle, self).draw_item()
        _, _, w, h = self.get_bounds()
        r = self._calculate_radius(w, h)
        self._painter.drawEllipse(QPoint(0, 0), r, r)


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
    def __init__(self, parent=None, init_channel=None):
        super(PyDMDrawingArc, self).__init__(parent, init_channel)
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

    def draw_item(self):
        """
        Draws the arc after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super(PyDMDrawingArc, self).draw_item()
        maxsize = not self.is_square()
        x, y, w, h = self.get_bounds(maxsize=maxsize)
        self._painter.drawArc(x, y, w, h, self._start_angle, self._span_angle)


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
        super(PyDMDrawingPie, self).__init__(parent, init_channel)

    def draw_item(self):
        """
        Draws the pie after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super(PyDMDrawingPie, self).draw_item()
        maxsize = not self.is_square()
        x, y, w, h = self.get_bounds(maxsize=maxsize)
        self._painter.drawPie(x, y, w, h, self._start_angle, self._span_angle)


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
        super(PyDMDrawingChord, self).__init__(parent, init_channel)

    def draw_item(self):
        """
        Draws the chord after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super(PyDMDrawingChord, self).draw_item()
        maxsize = not self.is_square()
        x, y, w, h = self.get_bounds(maxsize=maxsize)
        self._painter.drawChord(x, y, w, h, self._start_angle, self._span_angle)


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
        super(PyDMDrawingPolygon, self).__init__(parent, init_channel)
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
        #(x + r*cos(theta), y + r*sin(theta))
        r = min(w, h)/2.0
        deg_step = 360.0/self._num_points

        points = []
        for i in range(self._num_points):
            xp = r * math.cos(math.radians(deg_step * i))
            yp = r * math.sin(math.radians(deg_step * i))
            points.append(QPointF(xp, yp))

        return points

    def draw_item(self):
        """
        Draws the Polygon after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super(PyDMDrawingPolygon, self).draw_item()
        maxsize = not self.is_square()
        x, y, w, h = self.get_bounds(maxsize=not self.is_square())
        poly = self._calculate_drawing_points(x, y, w, h)
        self._painter.drawPolygon(QPolygonF(poly))
