# Unit Tests for the PyDM drawing widgets

import os
from logging import ERROR
import pytest

from qtpy.QtGui import QColor, QBrush, QPixmap
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Property, Qt, QPoint, QSize
from qtpy.QtDesigner import QDesignerFormWindowInterface

from ...widgets.base import PyDMWidget
from ...widgets.drawing import (deg_to_qt, qt_to_deg, PyDMDrawing,
                                PyDMDrawingLine, PyDMDrawingImage,
                                PyDMDrawingRectangle, PyDMDrawingTriangle,
                                PyDMDrawingEllipse,
                                PyDMDrawingCircle, PyDMDrawingArc,
                                PyDMDrawingPie, PyDMDrawingChord,
                                PyDMDrawingPolygon)

from ...utilities.stylesheet import apply_stylesheet


# --------------------
# POSITIVE TEST CASES
# --------------------

# # -------------
# # PyDMDrawing
# # -------------
@pytest.mark.parametrize("deg, expected_qt_deg", [
    (0, 0),
    (1, 16),
    (-1, -16),
])
def test_deg_to_qt(deg, expected_qt_deg):
    """
    Test the conversion from degrees to Qt degrees.

    Expectations:
    The angle measurement in degrees is converted correctly to Qt degrees, which are 16 times more than the degree
    value, i.e. 1 degree = 16 Qt degrees.

    Parameters
    ----------
    deg : int, float
        The angle value in degrees

    expected_qt_deg : int, floag
        The expected Qt degrees after the conversion
    """
    assert deg_to_qt(deg) == expected_qt_deg


@pytest.mark.parametrize("qt_deg, expected_deg", [
    (0, 0),
    (16, 1),
    (-16, -1),
    (-32.0, -2),
    (16.16, 1.01)
])
def test_qt_to_deg(qt_deg, expected_deg):
    """
       Test the conversion from Qt degrees to degrees.

       Expectations:
       The angle measurement in Qt degrees is converted correctly to degrees, which are 16 times less than the Qt degree
       value, i.e. 1 Qt degree = 1/16 degree

       Parameters
       ----------
       qt_deg : int, float
           The angle value in Qt degrees

       expected_deg : int, floag
           The expected degrees after the conversion
       """
    assert qt_to_deg(qt_deg) == expected_deg


def test_pydmdrawing_construct(qtbot):
    """
    Test the construction of a PyDM base object.

    Expectations:
    Attributes are assigned with the appropriate default values.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    assert pydm_drawing.alarmSensitiveBorder is False
    assert pydm_drawing._rotation == 0.0
    assert pydm_drawing._brush.style() == Qt.SolidPattern
    assert pydm_drawing._painter
    assert pydm_drawing._pen.style() == pydm_drawing._pen_style == Qt.NoPen
    assert pydm_drawing._pen_width == 0
    assert pydm_drawing._pen_color == QColor(0, 0, 0)


def test_pydmdrawing_sizeHint(qtbot):
    """
    Test the default size of the widget.

    Expectations:
    The size hint is a fixed size.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    assert pydm_drawing.sizeHint() == QSize(100, 100)


@pytest.mark.parametrize("alarm_sensitive_content", [
    True,
    False,
])
def test_pydmdrawing_paintEvent(qtbot, signals, alarm_sensitive_content):
    """
    Test the paintEvent handling of the widget. This test method will also execute PyDMDrawing alarm_severity_changed
    and draw_item().

    Expectations:
    The paintEvent will be triggered, and the widget's brush color is correctly set.
    
    NOTE: This test depends on the default stylesheet having different values for 'qproperty-brush' for different alarm states of PyDMDrawing.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    alarm_sensitive_content : bool
        True if the widget will be redraw with a different color if an alarm is triggered; False otherwise.
    """
    QApplication.instance().make_main_window()
    main_window = QApplication.instance().main_window
    qtbot.addWidget(main_window)
    pydm_drawing = PyDMDrawing(parent=main_window, init_channel='fake://tst')
    qtbot.addWidget(pydm_drawing)
    pydm_drawing.alarmSensitiveContent = alarm_sensitive_content
    brush_before = pydm_drawing.brush.color().name()
    signals.new_severity_signal.connect(pydm_drawing.alarmSeverityChanged)
    signals.new_severity_signal.emit(PyDMWidget.ALARM_MAJOR)

    brush_after = pydm_drawing.brush.color().name()
    if alarm_sensitive_content:
        assert brush_before != brush_after
    else:
        assert brush_before == brush_after


@pytest.mark.parametrize("widget_width, widget_height, expected_results", [
    (4.0, 4.0, (2.0, 2.0)),
    (1.0, 1.0, (0.5, 0.5)),
    (0, 0, (0, 0))
])
def test_pydmdrawing_get_center(qtbot, monkeypatch, widget_width, widget_height,
                                expected_results):
    """
    Test the calculation of the widget's center from its width and height.

    Expectations:
    The center of the widget is correctly calculated.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To override default attribute values
    widget_width : int, float
        The width of the widget
    widget_height : int, float
        The height of the widget
    expected_results : tuple
        The location of the center. This is a tuple of the distance from the width and that from the height.
    """
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: widget_width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: widget_height)

    assert pydm_drawing.get_center() == expected_results


@pytest.mark.parametrize(
    "width, height, rotation_deg, pen_width, has_border, max_size, force_no_pen, expected",
    [
        # Zero rotation, with typical width, height, pen_width, and variable max_size, has_border, and force_no_pen
        # width > height
        (25.53, 10.35, 0.0, 2, True, True, True,
         (-12.765, -5.175, 25.53, 10.35)),
        (25.53, 10.35, 0.0, 2, True, True, False,
         (-10.765, -3.175, 21.53, 6.35)),
        (25.53, 10.35, 0.0, 2, True, False, True,
         (-12.765, -5.175, 25.53, 10.35)),
        (25.53, 10.35, 0.0, 2, True, False, False,
         (-10.765, -3.175, 21.53, 6.35)),
        (25.53, 10.35, 0.0, 2, False, True, True,
         (-12.765, -5.175, 25.53, 10.35)),
        (25.53, 10.35, 0.0, 2, False, True, False,
         (-12.765, -5.175, 25.53, 10.35)),
        (25.53, 10.35, 0.0, 2, False, False, True,
         (-12.765, -5.175, 25.53, 10.35)),

        # width < height
        (10.35, 25.53, 0.0, 2, True, True, True,
         (-5.175, -12.765, 10.35, 25.53)),
        (10.35, 25.53, 0.0, 2, True, True, False,
         (-3.175, -10.765, 6.35, 21.53)),
        (10.35, 25.53, 0.0, 2, True, False, True,
         (-5.175, -12.765, 10.35, 25.53)),
        (10.35, 25.53, 0.0, 2, True, False, False,
         (-3.175, -10.765, 6.35, 21.53)),
        (10.35, 25.53, 0.0, 2, False, True, True,
         (-5.175, -12.765, 10.35, 25.53)),
        (10.35, 25.53, 0.0, 2, False, True, False,
         (-5.175, -12.765, 10.35, 25.53)),
        (10.35, 25.53, 0.0, 2, False, False, True,
         (-5.175, -12.765, 10.35, 25.53)),

        # width == height
        (
        10.35, 10.35, 0.0, 2, True, True, True, (-5.175, -5.175, 10.35, 10.35)),
        (10.35, 10.35, 0.0, 2, True, True, False, (-3.175, -3.175, 6.35, 6.35)),
        (10.35, 10.35, 0.0, 2, True, False, True,
         (-5.175, -5.175, 10.35, 10.35)),
        (
        10.35, 10.35, 0.0, 2, True, False, False, (-3.175, -3.175, 6.35, 6.35)),
        (10.35, 10.35, 0.0, 2, False, True, True,
         (-5.175, -5.175, 10.35, 10.35)),
        (10.35, 10.35, 0.0, 2, False, True, False,
         (-5.175, -5.175, 10.35, 10.35)),
        (10.35, 10.35, 0.0, 2, False, False, True,
         (-5.175, -5.175, 10.35, 10.35)),

        # Variable rotation, max_size, and force_no_pen, has_border is True
        (25.53, 10.35, 45.0, 2, True, True, True,
         (-5.207, -2.111, 10.415, 4.222)),
        (25.53, 10.35, 145.0, 2, True, True, True,
         (-5.714, -2.316, 11.428, 4.633)),
        (25.53, 10.35, 90.0, 2, True, True, False,
         (-3.175, -0.098, 6.35, 0.196)),
        (25.53, 10.35, 180.0, 2, True, False, True,
         (-12.765, -5.175, 25.53, 10.35)),
        (25.53, 10.35, 270.0, 2, True, False, False,
         (-10.765, -3.175, 21.53, 6.35)),
        (25.53, 10.35, 360.0, 2, False, True, True,
         (-12.765, -5.175, 25.53, 10.35)),
        (25.53, 10.35, 0.72, 2, False, True, False,
         (-12.382, -5.02, 24.764, 10.04)),
        (25.53, 10.35, 71.333, 2, False, False, True,
         (-12.765, -5.175, 25.53, 10.35)),
    ])
def test_pydmdrawing_get_bounds(qtbot, monkeypatch, width, height, rotation_deg,
                                pen_width, has_border, max_size,
                                force_no_pen, expected):
    """
    Test the useful area calculations and compare the resulted tuple to the expected one.

    Expectations:
    The drawable area boundaries are correctly calculated.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To override default attribute values
    max_size : bool
        If True, draw the widget within the maximum rectangular dimensions given by ```get_inner_max```. If False,
        draw the widget within the user-provided width and height
    force_no_pen : bool
        If True, consider the pen width while calculating the bounds. If False, do not take into account the pen width
    expected : tuple
        The (x, y) coordinates of the starting point, and the maximum width and height of the rendered image
    """
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    pydm_drawing._rotation = rotation_deg
    pydm_drawing._pen_width = pen_width
    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: height)

    if has_border:
        monkeypatch.setattr(PyDMDrawing, "has_border", lambda *args: True)
    else:
        monkeypatch.setattr(PyDMDrawing, "has_border", lambda *args: False)

    calculated_bounds = pydm_drawing.get_bounds(max_size, force_no_pen)
    calculated_bounds = tuple(
        [round(x, 3) if isinstance(x, float) else x for x in calculated_bounds])
    assert calculated_bounds == expected


@pytest.mark.parametrize("pen_style, pen_width, expected_result", [
    (Qt.NoPen, 0, False),
    (Qt.NoPen, 1, False),
    (Qt.SolidLine, 0, False),
    (Qt.DashLine, 0, False),
    (Qt.SolidLine, 1, True),
    (Qt.DashLine, 10, True)
])
def test_pydmdrawing_has_border(qtbot, pen_style, pen_width, expected_result):
    """
    Test the determination whether the widget will be drawn with a border, taking into account the pen style and width

    Expectations:
    The widget has a border if the pen style is not Qt.NoPen, and the pen width is greater than 0.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    pen_style : PenStyle
        The style (patterns) of the pen
    pen_width : int
        The thickness of the pen's lines
    expected_result : bool
        True if the widget has a border, False otherwise
    """
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    pydm_drawing.penStyle = pen_style
    pydm_drawing.penWidth = pen_width

    assert pydm_drawing.has_border() == expected_result


@pytest.mark.parametrize("width, height, expected_result", [
    (10, 15, False),
    (10.5, 22.333, False),
    (-10.333, -10.332, False),
    (10.333, 10.333, True),
    (-20.777, -20.777, True),
    (70, 70, True),
])
def test_pydmdrawing_is_square(qtbot, monkeypatch, width, height,
                               expected_result):
    """
    Check if the widget has the same width and height values.

    Expectations:
    The widget's squareness checking returns True if its width and height are the same; False otherwise.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To override dialog behaviors
    width : int, float
        The width of the widget
    height : int, float
        The height of a widget
    expected_result
        True if the widget has equal width and height; False otherwise
    """
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: height)

    assert pydm_drawing.is_square() == expected_result


@pytest.mark.parametrize("width, height, rotation_deg, expected", [
    (25.53, 10.35, 0.0, (25.53, 10.35)),
    (10.35, 25.53, 0.0, (10.35, 25.53)),
    (25.53, 10.35, 45.0, (10.415, 4.222)),
    (10.35, 25.53, 45.0, (4.222, 10.415)),
    (10.35, 25.53, 360.0, (10.35, 25.53)),
    (10.35, 25.53, -45.0, (4.222, 10.415)),
    (10.35, 25.53, -270.0, (4.196, 10.35)),
    (10.35, 25.53, -360.0, (10.35, 25.53)),
])
def test_pydmdrawing_get_inner_max(qtbot, monkeypatch, width, height,
                                   rotation_deg, expected):
    """
    Test the calculation of the inner rectangle in a rotated rectangle.

    Expectations:
    The returned inner rectangle's width and height are in a tuple, and must match with the values expected.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To override existing method behaviors
    width : int, float
        The width of the rotated rectangle
    height : int, float
        The height of the rotated rectangle
    rotation_deg : float
        The rectangle's rotation angle (in degrees)
    expected : tuple
        The tuple containing the width and height of the inner rectangle
    """
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    pydm_drawing._rotation = rotation_deg
    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: height)

    calculated_inner_max = pydm_drawing.get_inner_max()
    calculated_inner_max = tuple(
        [round(x, 3) if isinstance(x, float) else x for x in
         calculated_inner_max])
    assert calculated_inner_max == expected


def test_pydmdrawing_properties_and_setters(qtbot):
    """
    Test the PyDMDrawing base class properties and setters.

    Expectations:
    Attribute values are to be retained and retrieved correctly.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    assert pydm_drawing.penWidth == 0
    assert pydm_drawing.penColor == QColor(0, 0, 0)
    assert pydm_drawing.rotation == 0.0
    assert pydm_drawing._brush.style() == Qt.SolidPattern
    assert pydm_drawing.penStyle == Qt.NoPen

    # The pen width will retain the previously set value if a negative value is attempted to be assigned to it
    pydm_drawing.penWidth = -1
    assert pydm_drawing.penWidth == 0

    pydm_drawing.penWidth = 5
    pydm_drawing.penWidth = -1
    assert pydm_drawing.penWidth == 5

    pydm_drawing.penColor = QColor(255, 0, 0)
    pydm_drawing.rotation = 99.99
    pydm_drawing.brush = QBrush(Qt.Dense3Pattern)

    assert pydm_drawing.penColor == QColor(255, 0, 0)
    assert pydm_drawing.rotation == 99.99
    assert pydm_drawing._brush.style() == Qt.Dense3Pattern


# # ----------------
# # PyDMDrawingLine
# # ----------------
@pytest.mark.parametrize("alarm_sensitive_content", [
    True,
    False,
])
def test_pydmdrawingline_draw_item(qtbot, signals, alarm_sensitive_content):
    """
    Test PyDMDrawingLine base class drawing handling.

    Expectations:
    The focus manipulation of the base widget object triggers the draw_item() method of the PyDMDrawLine object.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        To emit the alarm severity change signal in order to make an appearance change for the widget, thus triggering
        a redraw
    alarm_sensitive_content : bool
        True if the widget will be redraw with a different color if an alarm is triggered; False otherwise
    """
    pydm_drawingline = PyDMDrawingLine(init_channel='fake://tst')
    qtbot.addWidget(pydm_drawingline)

    pydm_drawingline.alarmSensitiveContent = alarm_sensitive_content
    signals.new_severity_signal.connect(pydm_drawingline.alarmSeverityChanged)
    signals.new_severity_signal.emit(PyDMWidget.ALARM_MAJOR)

    with qtbot.waitExposed(pydm_drawingline):
        pydm_drawingline.show()
    qtbot.waitUntil(lambda: pydm_drawingline.isEnabled(), timeout=5000)
    pydm_drawingline.setFocus()

    def wait_focus():
        return pydm_drawingline.hasFocus()

    qtbot.waitUntil(wait_focus, timeout=5000)


# # -----------------
# # PyDMDrawingImage
# # -----------------
def test_pydmdrawingimage_construct(qtbot):
    """
    Test the construct of a PyDMDrawingImage object.

    Expectations:
    The default attribute values are correctly set.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_drawingimage = PyDMDrawingImage()
    qtbot.addWidget(pydm_drawingimage)

    assert pydm_drawingimage._pixmap is not None
    assert pydm_drawingimage._aspect_ratio_mode == Qt.KeepAspectRatio
    assert pydm_drawingimage.filename == ""

    base_path = os.path.dirname(__file__)
    test_file = os.path.join(base_path, '..', '..', '..', 'examples', 'drawing',
                             'SLAC_logo.jpeg')
    pydm_drawingimage2 = PyDMDrawingImage(filename=test_file)
    qtbot.addWidget(pydm_drawingimage2)

    pydm_drawingimage3 = PyDMDrawingImage(filename=os.path.abspath(test_file))
    qtbot.addWidget(pydm_drawingimage3)

    pydm_drawingimage4 = PyDMDrawingImage(filename="foo")
    qtbot.addWidget(pydm_drawingimage4)

    test_gif = os.path.join(base_path, '..', '..', '..', 'examples', 'drawing',
                             'test.gif')
    pydm_drawingimage5 = PyDMDrawingImage(filename=test_gif)
    pydm_drawingimage5.movie_finished()
    qtbot.addWidget(pydm_drawingimage5)

    pydm_drawingimage5.filename = test_file
    pydm_drawingimage5.movie_frame_changed(-1)
    pydm_drawingimage5.movie_finished()


def test_pydmdrawingimage_get_designer_window(qtbot):
    """
    Test getting the designer window that owns the widget. Currently, only test with the parent window being None.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    parent = None
    pydm_drawingimage = PyDMDrawingImage(parent=parent)
    qtbot.addWidget(pydm_drawingimage)

    designer_window = pydm_drawingimage.get_designer_window()

    if parent is None:
        assert designer_window is None
    elif isinstance(parent, QDesignerFormWindowInterface):
        assert designer_window == parent
    else:
        assert designer_window == parent.parent()


def test_pydmdrawingimage_test_properties_and_setters(qtbot):
    """
    Test the PyDMDrawing base class properties and setters.

    Expectations:
    Attribute values are to be retained and retrieved correctly.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_drawingimage = PyDMDrawingImage()
    qtbot.addWidget(pydm_drawingimage)

    pydm_drawingimage.aspectRatioMode = Qt.KeepAspectRatioByExpanding
    assert pydm_drawingimage.aspectRatioMode == Qt.KeepAspectRatioByExpanding


@pytest.mark.parametrize("is_pixmap_empty", [
    True,
    False,
])
def test_pydmdrawingimage_size_hint(qtbot, monkeypatch, is_pixmap_empty):
    """
    Test the size hint of a PyDMDrawingImage object.

    Expectations:
    If the image is empty, the widget assumes the default size of width == height == 100 pixels. If not, the widget
    takes the size from the off screen image presentation (QPixmap).

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To override attribute values
    is_pixmap_empty : bool
        True if the image presentation is empty; False otherwise
    """
    pydm_drawingimage = PyDMDrawingImage()
    qtbot.addWidget(pydm_drawingimage)

    if is_pixmap_empty:
        monkeypatch.setattr(QSize, "isEmpty", lambda *args: True)
    else:
        monkeypatch.setattr(QPixmap, "size", lambda *args: QSize(125, 125))

    size_hint = pydm_drawingimage.sizeHint()
    assert size_hint == QSize(100,
                              100) if is_pixmap_empty else size_hint == pydm_drawingimage._pixmap.size()


@pytest.mark.parametrize("width, height, pen_width", [
    (7.7, 10.2, 0),
    (10.2, 7.7, 0),
    (5.0, 5.0, 0),
    (10.25, 10.25, 1.5),
    (10.25, 100.0, 5.125),
    (100.0, 10.25, 5.125),
])
def test_pydmdrawingimage_draw_item(qtbot, monkeypatch, width, height,
                                    pen_width):
    """
    Test the rendering of a PyDMDrawingImage object.

    Expectations:
    The drawing of the object takes place without any problems.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To override attribute values
    width : int, float
        The width to the widget
    height : int, float
        The height of the widget
    pen_width : int
        The width of the pen stroke
    """
    pydm_drawingimage = PyDMDrawingImage()
    qtbot.addWidget(pydm_drawingimage)

    pydm_drawingimage.penWidth = pen_width

    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: height)

    pydm_drawingimage.draw_item()


# # ---------------------
# # PyDMDrawingRectangle
# # ---------------------
@pytest.mark.parametrize("width, height, pen_width", [
    (7.7, 10.2, 0),
    (10.2, 7.7, 0),
    (5.0, 5.0, 0),
    (10.25, 10.25, 1.5),
    (10.25, 100.0, 5.125),
    (100.0, 10.25, 5.125),
])
def test_pydmdrawingrectangle_draw_item(qtbot, monkeypatch, width, height,
                                        pen_width):
    """
    Test the rendering of a PyDMDrawingRectangle object.

    Expectations:
    The drawing of the object takes place without any problems.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To override attribute values
    width : int, float
        The width to the widget
    height : int, float
        The height of the widget
    pen_width : int
        The width of the pen stroke
    """
    pydm_drawingrectangle = PyDMDrawingRectangle()
    qtbot.addWidget(pydm_drawingrectangle)

    pydm_drawingrectangle.penWidth = pen_width

    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: height)

    pydm_drawingrectangle.draw_item()


# # ---------------------
# # PyDMDrawingTriangle
# # ---------------------
@pytest.mark.parametrize("x, y, width, height, expected_points", [
    (0.0, 0.0, 7.7, 10.2, [QPoint(0, 5), QPoint(0, 0), QPoint(3, 0.0)]),
    (10.3, 0, 7.7, 10.2, [QPoint(10, 5), QPoint(10, 0), QPoint(3, 0)]),
    (10.3, 56.7, 7.7, 10.2, [QPoint(10, 5), QPoint(10, 56), QPoint(3, 56)]),
    (0.0, 10.75, 7.7, 10.2, [QPoint(0, 5), QPoint(0, 10), QPoint(3, 10)]),
    (-10.23, 0, 7.7, 10.2, [QPoint(-10, 5), QPoint(-10, 0), QPoint(3, 0)]),
    (0.0, -10.23, 7.7, 10.2, [QPoint(0, 5), QPoint(0, -10), QPoint(3, -10)]),
    (-60.23, -87.25, 7.7, 10.2,
     [QPoint(-60, 5), QPoint(-60, -87), QPoint(3, -87)]),
    (1, 2, 5.0, 5.0, [QPoint(1, 2), QPoint(1, 2), QPoint(2, 2)]),
])
def test_pydmdrawingtriangle_calculate_drawing_points(qtbot, x, y, width,
                                                      height, expected_points):
    """
    Test the calculations of the point coordinates of a PyDMDrawingTriangle widget.

    Expectations:
    The calculations match with the expected values.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    x : int, float
        The x-coordinate of the top of the triangle
    y: int, float
        The y-coordinate of the top of the triangle
    width : int, float
        The base measurement of the triangle
    height : int, float
        The height measurement of the triangle
    expected_points : tuple
        The collection of the three x and y coordinate sets of the triangle to draw
    """
    pydm_drawingtriangle = PyDMDrawingTriangle()
    qtbot.addWidget(pydm_drawingtriangle)

    calculated_points = pydm_drawingtriangle._calculate_drawing_points(x, y,
                                                                       width,
                                                                       height)
    assert calculated_points == expected_points


@pytest.mark.parametrize("width, height, pen_width", [
    (7.7, 10.2, 0),
    (10.2, 7.7, 0),
    (5.0, 5.0, 0),
    (10.25, 10.25, 1.5),
    (10.25, 100.0, 5.125),
    (100.0, 10.25, 5.125),
])
def test_pydmdrawingtriangle_draw_item(qtbot, monkeypatch, width, height,
                                       pen_width):
    """
    Test the rendering of a PyDMDrawingTriangle object.

    Expectations:
    The drawing of the object takes place without any problems.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To override attribute values
    width : int, float
        The width to the widget
    height : int, float
        The height of the widget
    pen_width : int
        The width of the pen stroke
    """
    pydm_drawingtriangle = PyDMDrawingTriangle()
    qtbot.addWidget(pydm_drawingtriangle)

    pydm_drawingtriangle.penWidth = pen_width

    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: height)

    pydm_drawingtriangle.draw_item()


# # -------------------
# # PyDMDrawingEclipse
# # -------------------
@pytest.mark.parametrize("width, height, pen_width", [
    (5.0, 5.0, 0),
    (10.25, 10.25, 1.5),
    (10.25, 100.0, 5.125),
])
def test_pydmdrawingeclipse_draw_item(qtbot, monkeypatch, width, height,
                                      pen_width):
    """
    Test the rendering of a PyDMDrawingEclipse object.

    Expectations:
    The drawing of the object takes place without any problems.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To override attribute values
    width : int, float
        The width to the widget
    height : int, float
        The height of the widget
    pen_width : int
        The width of the pen stroke
    """
    pydm_dymdrawingeclipse = PyDMDrawingEllipse()
    qtbot.addWidget(pydm_dymdrawingeclipse)

    pydm_dymdrawingeclipse.penWidth = pen_width

    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: height)

    pydm_dymdrawingeclipse.draw_item()


# # ------------------
# # PyDMDrawingCircle
# # ------------------
@pytest.mark.parametrize("width, height, expected_radius", [
    (5.0, 5.0, 2.5),
    (10.25, 10.25, 5.125),
    (10.25, 100.0, 5.125),
])
def test_pydmdrawingcircle_calculate_radius(qtbot, width, height,
                                            expected_radius):
    """
    Test the calculation of a PyDMDrawingCircle's radius.

    Expectations:
    Given the width and height of the circle, the calculated radius will match with the expected value.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    width : int, float
        The width to the widget
    height : int, float
        The height of the widget
    expected_radius : int, float
        The expected radius calculated from the given width and height
    """
    pydm_dymdrawingcircle = PyDMDrawingCircle()
    qtbot.addWidget(pydm_dymdrawingcircle)

    calculated_radius = pydm_dymdrawingcircle._calculate_radius(width, height)
    assert calculated_radius == expected_radius


@pytest.mark.parametrize("width, height, pen_width", [
    (5.0, 5.0, 0),
    (10.25, 10.25, 1.5),
    (10.25, 100.0, 5.125),
])
def test_pydmdrawingcircle_draw_item(qtbot, monkeypatch, width, height,
                                     pen_width):
    """
    Test the rendering of a PyDMDrawingCircle object.

    Expectations:
    The drawing of the object takes place without any problems.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To override attribute values
    width : int, float
        The width to the widget
    height : int, float
        The height of the widget
    pen_width : int
        The width of the pen stroke
    """
    pydm_dymdrawingcircle = PyDMDrawingCircle()
    qtbot.addWidget(pydm_dymdrawingcircle)

    pydm_dymdrawingcircle.penWidth = pen_width

    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: height)

    pydm_dymdrawingcircle.draw_item()


# # ---------------
# # PyDMDrawingArc
# # ---------------
def test_pydmdrawingarc_construct(qtbot):
    """
    Test the construct of a PyDMDrawingArc widget.

    Expectations:
    The default attribute values are as expected.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_drawingarc = PyDMDrawingArc()
    qtbot.addWidget(pydm_drawingarc)

    assert pydm_drawingarc._pen_style == Qt.SolidLine
    assert pydm_drawingarc._pen_width == 1.0
    assert pydm_drawingarc._start_angle == 0
    assert pydm_drawingarc._span_angle == deg_to_qt(90)


@pytest.mark.parametrize("width, height, start_angle_deg, span_angle_deg", [
    (10.333, 11.777, 0, 0),
    (10.333, 10.333, 0, 0),
    (10.333, 10.333, 0, 45),
    (10.333, 11.777, 0, 45),
    (10.333, 11.777, 0, -35),
    (10.333, 11.777, 11, 45),
    (10.333, 11.777, -11, -25),
])
def test_pydmdrawingarc_draw_item(qtbot, monkeypatch, width, height,
                                  start_angle_deg, span_angle_deg):
    """
    Test the rendering of a PyDMDrawingArc object.

    Expectations:
    The drawing of the object takes place without any problems.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To override attribute values
    width : int, float
        The width to the widget
    height : int, float
        The height of the widget
    start_angle_deg : int
        The start angle in degrees
    span_angle_deg : int
        The span angle in degrees
    """
    pydm_drawingarc = PyDMDrawingArc()
    qtbot.addWidget(pydm_drawingarc)

    pydm_drawingarc.startAngle = start_angle_deg
    pydm_drawingarc.spanAngle = span_angle_deg

    assert pydm_drawingarc.startAngle == start_angle_deg
    assert pydm_drawingarc.spanAngle == span_angle_deg

    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: height)

    pydm_drawingarc.draw_item()


# # ---------------
# # PyDMDrawingPie
# # ---------------
@pytest.mark.parametrize(
    "width, height, pen_width, rotation_deg, start_angle_deg, span_angle_deg", [
        (10.333, 11.777, 0, 0, 0, 0),
        (10.333, 10.333, 0, 0, 0, 0),
        (10.333, 11.777, 0, 0, 0, 45),
        (10.333, 11.777, 0, 0, 0, -35),
        (10.333, 11.777, 3, 15.333, 0, 0),
        (10.333, 11.777, 3, 15.333, 0, 45),
        (10.333, 11.777, 3, 15.333, 0, -35),
        (10.333, 11.777, 3, 15.333, 11, 45),
        (10.333, 11.777, 3, 15.333, -11, -25),
    ])
def test_pydmdrawingpie_draw_item(qtbot, monkeypatch, width, height, pen_width,
                                  rotation_deg, start_angle_deg,
                                  span_angle_deg):
    """
    Test the rendering of a PyDMDrawingPie object.

    Expectations:
    The drawing of the object takes place without any problems.

    Parameters
    ----------
    qtbot : fixture
       Window for widget testing
    monkeypatch : fixture
       To override attribute values
    width : int, float
       The width to the widget
    height : int, float
       The height of the widget
    pen_width: int
        The thickness of the pen stroke
    rotation_deg : int
        The rotation in degrees
    start_angle_deg : int
       The start angle in degrees
    span_angle_deg : int
       The span angle in degrees
    """
    pydm_drawingpie = PyDMDrawingPie()
    qtbot.addWidget(pydm_drawingpie)

    pydm_drawingpie._pen_width = pen_width
    pydm_drawingpie._rotation = rotation_deg
    pydm_drawingpie._start_angle = start_angle_deg
    pydm_drawingpie._span_angle = span_angle_deg

    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: height)

    pydm_drawingpie.draw_item()


# # -----------------
# # PyDMDrawingChord
# # -----------------
@pytest.mark.parametrize(
    "width, height, pen_width, rotation_deg, start_angle_deg, span_angle_deg", [
        (10.333, 11.777, 0, 0, 0, 0),
        (10.333, 10.333, 0, 0, 0, 0),
        (10.333, 11.777, 0, 0, 0, 45),
        (10.333, 11.777, 0, 0, 0, -35),
        (10.333, 11.777, 3, 15.333, 0, 0),
        (10.333, 11.777, 3, 15.333, 0, 45),
        (10.333, 11.777, 3, 15.333, 0, -35),
        (10.333, 11.777, 3, 15.333, 11, 45),
        (10.333, 11.777, 3, 15.333, -11, -25),
    ])
def test_pydmdrawingchord_draw_item(qtbot, monkeypatch, width, height,
                                    pen_width, rotation_deg, start_angle_deg,
                                    span_angle_deg):
    """
    Test the rendering of a PyDMDrawingChord object.

    Expectations:
    The drawing of the object takes place without any problems.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To override attribute values
    width : int, float
        The width to the widget
    height : int, float
        The height of the widget
    pen_width: int
        The thickness of the pen stroke
    rotation_deg : int
        The rotation in degrees
    start_angle_deg : int
        The start angle in degrees
    span_angle_deg : int
        The span angle in degrees
    """
    pydm_drawingchord = PyDMDrawingChord()
    qtbot.addWidget(pydm_drawingchord)

    pydm_drawingchord._pen_width = pen_width
    pydm_drawingchord._rotation = rotation_deg
    pydm_drawingchord._start_angle = start_angle_deg
    pydm_drawingchord._span_angle = span_angle_deg

    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: height)

    pydm_drawingchord.draw_item()

# # ---------------------
# # PyDMDrawingPolygon
# # ---------------------
@pytest.mark.parametrize("x, y, width, height, num_points, expected_points", [
    (0, 0, 100, 100, 3, [(50.0, 0),(-25, 43.3012),(-25, -43.3012)]),
    (0, 0, 100, 100, 4, [(50.0, 0), (0, 50.0), (-50.0, 0), (0, -50.0)])
])
def test_pydmdrawingpolygon_calculate_drawing_points(qtbot, x, y, width,
                                                      height, num_points,
                                                      expected_points):
    """
    Test the calculations of the point coordinates of a PyDMDrawingTriangle widget.

    Expectations:
    The calculations match with the expected values.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    x : int, float
        The x-coordinate
    y: int, float
        The y-coordinate
    width : int, float
        The base measurement
    height : int, float
        The height measurement
    num_points : int
        The number of points in the polygon
    expected_points : tuple
        The collection of the x and y coordinate sets
    """
    drawing = PyDMDrawingPolygon()
    qtbot.addWidget(drawing)

    drawing.numberOfPoints = num_points

    assert drawing.numberOfPoints == num_points

    calculated_points = drawing._calculate_drawing_points(x, y,
                                                          width,
                                                          height)

    for idx, p in enumerate(calculated_points):
        assert p.x() == pytest.approx(expected_points[idx][0], 0.1)
        assert p.y() == pytest.approx(expected_points[idx][1], 0.1)

    drawing.draw_item()

# --------------------
# NEGATIVE TEST CASES
# --------------------

# # -------------
# # PyDMDrawing
# # -------------
@pytest.mark.parametrize("width, height, rotation_deg", [
    (0, 10.35, 0.0),
    (10.35, 0, 0.0),
    (0, 0, 45.0),
    (-10.5, 10.35, 15.0),
    (10.35, -5, 17.5),
    (-10.7, -10, 45.50),
])
def test_get_inner_max_neg(qtbot, monkeypatch, caplog, width, height,
                           rotation_deg):
    """
    Test the handling of invalid width and/or height value during the inner rectangle calculations.

    Expectations:
    Invalid values will be logged as errors.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    monkeypatch : fixture
        To override attribute values
    caplog : fixture
        To capture the error logging
    width : int, float
        The width of the widget
    height : int, float
        The height of the widget
    rotation_deg : int, float
        The widget's rotation, in degrees
    """
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    pydm_drawing._rotation = rotation_deg
    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: height)

    pydm_drawing.get_inner_max()

    for record in caplog.records:
        assert record.levelno == ERROR

    if width == 0:
        assert "Invalid width. The value must be greater than 0" in caplog.text
    elif height == 0:
        assert "Invalid height. The value must be greater than 0" in caplog.text
