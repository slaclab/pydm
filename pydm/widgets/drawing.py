import math
import os
from ..PyQt.QtGui import QApplication, QWidget, QColor, QPainter, QBrush, QPen, QPolygon, QPixmap, QStyle, QStyleOption
from ..PyQt.QtCore import pyqtProperty, Qt, QPoint, QSize, pyqtSlot
from ..PyQt.QtDesigner import QDesignerFormWindowInterface
from .base import PyDMWidget
from ..utilities import is_pydm_app

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
        QWidget.__init__(self, parent)
        PyDMWidget.__init__(self, init_channel=init_channel)
        self.alarmSensitiveBorder = False
        self._rotation = 0.0
        self._brush = QBrush(Qt.SolidPattern)
        self._default_color = QColor()
        self._painter = QPainter()
        self._pen = QPen(Qt.NoPen)
        self._pen_style = Qt.NoPen
        self._pen_width = 0
        self._pen_color = QColor(0, 0, 0)

    def sizeHint(self):
        return QSize(100,100)

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

        color = self._default_color
        if self._alarm_sensitive_content and self._alarm_state != 0 and self.channels() is not None:
            alarm_color = self._style.get("color", None)
            if alarm_color is not None:
                color = QColor(alarm_color)

        self._brush.setColor(color)

        self._painter.setBrush(self._brush)
        self._painter.setPen(self._pen)

        self.draw_item()
        self._painter.end()

    def alarm_severity_changed(self, new_alarm_severity):
        """
        Callback invoked when the Channel alarm severity is changed.
        This callback is not processed if the widget has no channel
        associated with it.
        This callback handles the composition of the stylesheet to be
        applied and the call
        to update to redraw the widget with the needed changes for the
        new state.

        Parameters
        ----------
        new_alarm_severity : int
            The new severity where 0 = NO_ALARM, 1 = MINOR, 2 = MAJOR
            and 3 = INVALID
        """
        PyDMWidget.alarm_severity_changed(self, new_alarm_severity)
        self.update()

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
        if self._pen.style() != Qt.NoPen and self._pen.width() > 0:
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
        if (origWidth <= origHeight):
            w0 = origWidth
            h0 = origHeight
        else:
            w0 = origHeight
            h0 = origWidth
        # Angle normalization in range [-PI..PI)
        ang = angle - math.floor((angle + math.pi) / (2 * math.pi)) * 2 * math.pi
        ang = math.fabs(ang)
        if (ang > math.pi / 2):
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

    @pyqtProperty(QBrush)
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
            self._brush = new_brush
            self._default_color = new_brush.color()
            self.update()

    @pyqtProperty(Qt.PenStyle)
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
        if new_style != self._pen_style:
            self._pen_style = new_style
            self._pen.setStyle(new_style)
            self.update()

    @pyqtProperty(QColor)
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
        if new_color != self._pen_color:
            self._pen_color = new_color
            self._pen.setColor(new_color)
            self.update()

    @pyqtProperty(float)
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

    @pyqtProperty(float)
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
    Renders an image given by the ```filename``` property.
    This class inherits from PyDMDrawing.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """
    def __init__(self, parent=None, init_channel=None, filename=""):
        super(PyDMDrawingImage, self).__init__(parent, init_channel)
        self.filename = filename
        self._pixmap = QPixmap()
        self._aspect_ratio_mode = Qt.KeepAspectRatio
        if not is_pydm_app():
            designer_window = self.get_designer_window()
            if designer_window is not None:
                designer_window.fileNameChanged.connect(self.designer_form_saved)

    def get_designer_window(self):
        #Internal function to find the designer window that owns this widget.
        p = self.parent()
        while p is not None:
            if isinstance(p, QDesignerFormWindowInterface):
                return p
            p = p.parent()
        return None
    
    @pyqtSlot(str)
    def designer_form_saved(self, filename):
        self.filename = self._file
        
    @pyqtProperty(str)
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
        This can be an absolute or relative path to the display file.

        Parameters
        -------
        new_file : str
            The filename to be used
        """
        self._file = new_file
        path_relative_to_ui_file = self._file
        if not os.path.isabs(self._file):                
            try:
                if is_pydm_app():
                    path_relative_to_ui_file = QApplication.instance().get_path(self._file)
                else:
                    p = self.get_designer_window()
                    if p is not None:
                        path_relative_to_ui_file = os.path.join(p.absoluteDir().absolutePath(), self._file)
            except Exception as e:
                print(e)
        self._pixmap = QPixmap(path_relative_to_ui_file)
        self.update()

    def sizeHint(self):
        if self._pixmap.size().isEmpty():
            return super(PyDMDrawingImage, self).sizeHint()
        return self._pixmap.size()

    @pyqtProperty(Qt.AspectRatioMode)
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

        Returns
        -------
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
        _scaled = self._pixmap.scaled(w, h, self._aspect_ratio_mode,
                                      Qt.SmoothTransformation)
        self._painter.drawPixmap(x, y, _scaled)


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

    def draw_item(self):
        """
        Draws the triangle after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super(PyDMDrawingTriangle, self).draw_item()
        x, y, w, h = self.get_bounds(maxsize=True)
        points = [
            QPoint(x, h / 2.0),
            QPoint(x, y),
            QPoint(w / 2.0, y)
        ]
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

    def draw_item(self):
        """
        Draws the circle after setting up the canvas with a call to
        ```PyDMDrawing.draw_item```.
        """
        super(PyDMDrawingCircle, self).draw_item()
        _, _, w, h = self.get_bounds()
        r = min(w, h) / 2.0
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

    @pyqtProperty(float)
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

    @pyqtProperty(float)
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

