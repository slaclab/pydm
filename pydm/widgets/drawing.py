import math
from ..PyQt.QtGui import QWidget, QColor, QPainter, QBrush, QPen, QTransform, QPolygon, QPixmap, QStyle, QStyleOption
from ..PyQt.QtCore import pyqtProperty, Qt, QPoint, QFile
from .base import PyDMWidget

def deg_to_qt(deg):
    # Angles for Qt are in units of 1/16 of a degree
    return deg*16

def qt_to_deg(deg):
    # Angles for Qt are in units of 1/16 of a degree
    return deg/16.0

class PyDMDrawing(QWidget, PyDMWidget):
    def __init__(self, parent=None, init_channel=None):
        super().__init__(parent)
        self._rotation = 0.0
        self._brush = QBrush(Qt.SolidPattern)
        self._default_color = QColor()
        self._painter = QPainter()
        self._pen = QPen(Qt.NoPen)
        self._pen_style = Qt.NoPen
        self._pen_width = 0
        self._pen_color = QColor(0,0,0)

    def paintEvent(self, event):
        self._painter.begin(self)
        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, self._painter, self)
        self._painter.setRenderHint(QPainter.Antialiasing)

        if self._alarm_sensitive_content and self._alarm_state != 0:
            alarm_color = self._style.get("color", None)
            if alarm_color is not None:
                color = QColor(alarm_color)
            else:
                color = self._default_color
          
        self._brush.setColor(color)

        self._painter.setBrush(self._brush)
        self._painter.setPen(self._pen)

        self.draw_item()
        self._painter.end()

    def draw_item(self):
        xc, yc = self.get_center() 
        self._painter.translate(xc, yc)
        self._painter.rotate(-self._rotation)

    def get_center(self):
        return self.width()*0.5, self.height()*0.5

    def get_bounds(self, maxsize=False, force_no_pen=False):
        w, h = self.width(), self.height()

        if maxsize:
            w, h = self.get_inner_max()

        xc, yc = w* 0.5, h*0.5

        if self.has_border() and not force_no_pen:
            w = max(0, w - 2*self._pen_width)
            h = max(0, h - 2*self._pen_width)
            x = max(0, self._pen_width)
            y = max(0, self._pen_width)
        else:
            x = 0
            y = 0

        return x-xc, y-yc, w, h

    def has_border(self):
        if self._pen.style() != Qt.NoPen and self._pen.width() > 0:
            return True
        else:
            return False

    def is_square(self):
        return self.height() == self.width()

    def get_inner_max(self):
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

        #Angle normalization in range [-PI..PI)
        ang = angle - math.floor((angle + math.pi) / (2*math.pi)) * 2*math.pi
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

    @pyqtProperty(QBrush, doc=
    """
    The brush properties to be used when coloring the drawing 
    """
    )
    def brush(self):
        return self._brush

    @brush.setter
    def brush(self, new_brush):
        if new_brush != self._brush:
            self._brush = new_brush
            self._default_color = new_brush.color()
            self.update()

    @pyqtProperty(Qt.PenStyle, doc=
    """
    The pen style to be used on the border 
    """
    )
    def penStyle(self):
        return self._pen_style

    @penStyle.setter
    def penStyle(self, new_style):
        if new_style != self._pen_style:
            self._pen_style = new_style
            self._pen.setStyle(new_style)
            self.update()

    @pyqtProperty(QColor, doc=
    """
    The border color 
    """
    )
    def penColor(self):
        return self._pen_color

    @penColor.setter
    def penColor(self, new_color):
        if new_color != self._pen_color:
            self._pen_color = new_color
            self._pen.setColor(new_color)
            self.update()
  
    @pyqtProperty(float, doc=
    """
    Border width
    """
    )
    def penWidth(self):
        return self._pen_width

    @penWidth.setter
    def penWidth(self, new_width):
        if new_width < 0:
            return
        if new_width != self._pen_width:
            self._pen_width = new_width
            self._pen.setWidth(self._pen_width)
            self.update()

    @pyqtProperty(float, doc=
    """
    Counter-clockwise rotation in degrees to be applied to the drawing.
    """
    )
    def rotation(self):
        return self._rotation
  
    @rotation.setter
    def rotation(self, new_angle):
        if new_angle != self._rotation:
            self._rotation = new_angle
            self.update()

class PyDMDrawingLine(PyDMDrawing):
    def __init__(self, parent=None, init_channel=None):
        super(PyDMDrawingLine, self).__init__(parent, init_channel)

    def draw_item(self):
        super(PyDMDrawingLine, self).draw_item()
        x, y, w, h = self.get_bounds()
        self._painter.drawRect(x, 0, w, 1)


class PyDMDrawingImage(PyDMDrawing):
    def __init__(self, parent=None, init_channel=None):
        super(PyDMDrawingImage, self).__init__(parent, init_channel)
        self._file = ""
        self._pixmap = QPixmap()
        self._aspect_ratio_mode = Qt.KeepAspectRatio
        self.app = QApplication.instance()
 
    @pyqtProperty(str, doc=
    """
    The file to be loaded and displayed
    """
    )
    def filename(self):
        return self._file

    @filename.setter
    def filename(self, new_file):
        if new_file != self._file:
            self._file = new_file
            path_relative_to_ui_file = self._file
            try:
                #This could fail if we are in designer, where window() doesn't have the join_to_current_file_path method.
                path_relative_to_ui_file = self.app.get_path(self._file)
            except Exception as e:
                pass
            self._pixmap = QPixmap(path_relative_to_ui_file)
            self.update()

    @pyqtProperty(Qt.AspectRatioMode, doc=
    """
    Which aspect ratio mode to use
    """
    )
    def aspectRatioMode(self):
        return self._aspect_ratio_mode

    @aspectRatioMode.setter
    def aspectRatioMode(self, new_mode):
        if new_mode != self._aspect_ratio_mode:
            self._aspect_ratio_mode = new_mode
            self.update()

    def draw_item(self):
        super(PyDMDrawingImage, self).draw_item()
        x, y, w, h = self.get_bounds(maxsize=True, force_no_pen=True)
        _scaled = self._pixmap.scaled(w, h, self._aspect_ratio_mode, Qt.SmoothTransformation)
        self._painter.drawPixmap(x, y, _scaled)


class PyDMDrawingRectangle(PyDMDrawing):
    def __init__(self, parent=None, init_channel=None):
        super(PyDMDrawingRectangle, self).__init__(parent, init_channel)

    def draw_item(self):
        super(PyDMDrawingRectangle, self).draw_item()
        x, y, w, h = self.get_bounds(maxsize=True)
        self._painter.drawRect(x, y, w, h)


class PyDMDrawingTriangle(PyDMDrawing):
    def __init__(self, parent=None, init_channel=None):
        super(PyDMDrawingTriangle, self).__init__(parent, init_channel)

    def draw_item(self):
        super(PyDMDrawingTriangle, self).draw_item()
        x, y, w, h = self.get_bounds(maxsize=True)
        points = [
                QPoint(x, h/2.0),
                QPoint(x, y),
                QPoint(w/2.0, y)
        ]
        self._painter.drawPolygon(QPolygon(points))


class PyDMDrawingEllipse(PyDMDrawing):
    def __init__(self, parent=None, init_channel=None):
        super(PyDMDrawingEllipse, self).__init__(parent, init_channel)

    def draw_item(self):
        super(PyDMDrawingEllipse, self).draw_item()
        maxsize = not self.is_square()
        x, y, w, h = self.get_bounds(maxsize=maxsize)
        self._painter.drawEllipse(QPoint(0,0), w/2.0, h/2.0)


class PyDMDrawingCircle(PyDMDrawing):
    def __init__(self, parent=None, init_channel=None):
        super(PyDMDrawingCircle, self).__init__(parent, init_channel)

    def draw_item(self):
        super(PyDMDrawingCircle, self).draw_item()
        x, y, w, h = self.get_bounds()
        r = min(w, h)/2.0
        self._painter.drawEllipse(QPoint(0, 0), r, r)


class PyDMDrawingArc(PyDMDrawing):
    def __init__(self, parent=None, init_channel=None):
        super(PyDMDrawingArc, self).__init__(parent, init_channel)
        self.penStyle = Qt.SolidLine
        self.penWidth = 1.0
        self._start_angle = 0
        self._span_angle = deg_to_qt(90)

    @pyqtProperty(float, doc=
    """
    Start angle in degrees
    """
    )
    def startAngle(self):
        return qt_to_deg(self._start_angle)

    @startAngle.setter
    def startAngle(self, new_angle):
        if deg_to_qt(new_angle) != self._start_angle:
            self._start_angle = deg_to_qt(new_angle)
            self.update()

    @pyqtProperty(float, doc=
    """
    Span angle in degrees
    """
    )
    def spanAngle(self):
        return qt_to_deg(self._span_angle)

    @spanAngle.setter
    def spanAngle(self, new_angle):
        if deg_to_qt(new_angle) != self._span_angle:
            self._span_angle = deg_to_qt(new_angle)
            self.update()

    def draw_item(self):
        super(PyDMDrawingArc, self).draw_item()
        maxsize = not self.is_square()
        x, y, w, h = self.get_bounds(maxsize=maxsize)
        self._painter.drawArc(x, y, w, h, self._start_angle, self._span_angle)


class PyDMDrawingPie(PyDMDrawingArc):
    def __init__(self, parent=None, init_channel=None):
        super(PyDMDrawingPie, self).__init__(parent, init_channel)

    def draw_item(self):
        super(PyDMDrawingPie, self).draw_item()
        maxsize = not self.is_square()
        x, y, w, h = self.get_bounds(maxsize=maxsize)
        self._painter.drawPie(x, y, w, h, self._start_angle, self._span_angle)


class PyDMDrawingChord(PyDMDrawingArc):
    def __init__(self, parent=None, init_channel=None):
        super(PyDMDrawingChord, self).__init__(parent, init_channel)

    def draw_item(self):
        super(PyDMDrawingChord, self).draw_item()
        maxsize = not self.is_square()
        x, y, w, h = self.get_bounds(maxsize=maxsize)
        self._painter.drawChord(x, y, w, h, self._start_angle, self._span_angle)
 
