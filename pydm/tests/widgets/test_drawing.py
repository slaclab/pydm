# Unit Tests for the PyDM drawing widgets


from logging import ERROR
import pytest

from ...PyQt.QtGui import QApplication, QWidget, QColor, QPainter, QBrush, QPen, QPolygon, QPixmap, QStyle, QStyleOption
from ...PyQt.QtCore import pyqtProperty, Qt, QPoint, QSize, pyqtSlot
from ...PyQt.QtDesigner import QDesignerFormWindowInterface

from ...widgets.base import PyDMWidget
from ...widgets.drawing import deg_to_qt, qt_to_deg, PyDMDrawing, PyDMDrawingLine, PyDMDrawingImage, PyDMDrawingChord, \
    PyDMDrawingPie
from ...application import PyDMApplication
from ...utilities import is_pydm_app


# --------------------
# POSITIVE TEST CASES
# --------------------

@pytest.mark.parametrize("deg, expected_qt_deg", [
    (0, 0),
    (1, 16),
    (-1, -16),
])
def test_deg_to_qt(deg, expected_qt_deg):
    assert deg_to_qt(deg) == expected_qt_deg


@pytest.mark.parametrize("qt_deg, expected_deg", [
    (0, 0),
    (16, 1),
    (-16, -1),
    (-32.0, -2),
    (16.16, 1.01)
])
def test_qt_to_deg(qt_deg, expected_deg):
    assert qt_to_deg(qt_deg) == expected_deg


def test_pydmdrawing_construct(qtbot):
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    assert pydm_drawing.alarmSensitiveBorder is False
    assert pydm_drawing._rotation == 0.0
    assert pydm_drawing._brush.style() == Qt.SolidPattern
    assert pydm_drawing._default_color
    assert pydm_drawing._painter
    assert pydm_drawing._pen.style() == pydm_drawing._pen_style == Qt.NoPen
    assert pydm_drawing._pen_width == 0
    assert pydm_drawing._pen_color == QColor(0, 0, 0)


def test_pydmdrawing_sizeHint(qtbot):
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    assert pydm_drawing.sizeHint() == QSize(100, 100)


@pytest.mark.parametrize("alarm_sensitive_content", [
    True,
    False,
])
def test_pydmdrawing_paintEvent(qtbot, signals, test_alarm_style_sheet_map, alarm_sensitive_content):
    """
    Test the paintEvent handling of the widget. This test method will also execute PyDMDrawing alarm_severity_changed
    and draw_item().

    Parameters
    ----------
    qtbot
    signals
    test_alarm_style_sheet_map
    alarm_sensitive_content
    """
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    pydm_drawing.alarmSensitiveContent = alarm_sensitive_content
    signals.new_severity_signal.connect(pydm_drawing.alarmSeverityChanged)
    signals.new_severity_signal.emit(PyDMWidget.ALARM_MAJOR)

    with qtbot.waitExposed(pydm_drawing):
        pydm_drawing.show()
    pydm_drawing.setFocus()

    def wait_focus():
        return pydm_drawing.hasFocus()

    qtbot.waitUntil(wait_focus, timeout=5000)

    alarm_color = test_alarm_style_sheet_map[PyDMWidget.ALARM_CONTENT][pydm_drawing._alarm_state]

    if alarm_sensitive_content:
        assert pydm_drawing.brush.color() == QColor(alarm_color["color"])
    else:
        assert pydm_drawing.brush.color() == pydm_drawing._default_color


@pytest.mark.parametrize("widget_width, widget_height, expected_results", [
    (4.0, 4.0, (2.0, 2.0)),
    (1.0, 1.0, (0.5, 0.5)),
    (0, 0, (0, 0))
])
def test_pydmdrawing_get_center(qtbot, monkeypatch, widget_width, widget_height, expected_results):
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: widget_width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: widget_height)

    assert pydm_drawing.get_center() == expected_results


@pytest.mark.parametrize("width, height, rotation_deg, pen_width, has_border, max_size, force_no_pen, expected", [
    # Zero rotation, with typical width, height, pen_width, and variable max_size, has_border, and force_no_pen
    # width > height
    (25.53, 10.35, 0.0, 2, True, True, True, (-12.765, -5.175, 25.53, 10.35)),
    (25.53, 10.35, 0.0, 2, True, True, False, (-10.765, -3.175, 21.53, 6.35)),
    (25.53, 10.35, 0.0, 2, True, False, True,  (-12.765, -5.175, 25.53, 10.35)),
    (25.53, 10.35, 0.0, 2, True, False, False,  (-10.765, -3.175, 21.53, 6.35)),
    (25.53, 10.35, 0.0, 2, False, True, True, (-12.765, -5.175, 25.53, 10.35)),
    (25.53, 10.35, 0.0, 2, False, True, False, (-12.765, -5.175, 25.53, 10.35)),
    (25.53, 10.35, 0.0, 2, False, False, True, (-12.765, -5.175, 25.53, 10.35)),

    # width < height
    (10.35, 25.53, 0.0, 2, True, True, True, (-5.175, -12.765, 10.35, 25.53)),
    (10.35, 25.53, 0.0, 2, True, True, False, (-3.175, -10.765, 6.35, 21.53)),
    (10.35, 25.53, 0.0, 2, True, False, True, (-5.175, -12.765, 10.35, 25.53)),
    (10.35, 25.53, 0.0, 2, True, False, False, (-3.175, -10.765, 6.35, 21.53)),
    (10.35, 25.53, 0.0, 2, False, True, True, (-5.175, -12.765, 10.35, 25.53)),
    (10.35, 25.53, 0.0, 2, False, True, False, (-5.175, -12.765, 10.35, 25.53)),
    (10.35, 25.53, 0.0, 2, False, False, True, (-5.175, -12.765, 10.35, 25.53)),

    # width == height
    (10.35, 10.35, 0.0, 2, True, True, True, (-5.175, -5.175, 10.35, 10.35)),

    # Variable rotation, max_size, and force_no_pen, has_border is True
    (25.53, 10.35, 45.0, 2, True, True, True, (-5.207, -2.111, 10.415, 4.222)),
    (25.53, 10.35, 90.0, 2, True, True, False, (-3.175, -0.098, 6.35, 0.196)),
    (25.53, 10.35, 180.0, 2, True, False, True, (-12.765, -5.175, 25.53, 10.35)),
    (25.53, 10.35, 270.0, 2, True, False, False, (-10.765, -3.175, 21.53, 6.35)),
    (25.53, 10.35, 360.0, 2, False, True, True, (-12.765, -5.175, 25.53, 10.35)),
    (25.53, 10.35, 0.72, 2, False, True, False, (-12.382, -5.02, 24.764, 10.04)),
    (25.53, 10.35, 71.333, 2, False, False, True, (-12.765, -5.175, 25.53, 10.35)),
])
def test_pydmdrawing_get_bounds(qtbot, monkeypatch, width, height, rotation_deg, pen_width, has_border, max_size,
                                force_no_pen, expected):
    """
    Test the useful area calculations and compare the resulted tuple to the expected one
    Parameters
    ----------
    qtbot
    max_size
    force_no_pen
    expected
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
    calculated_bounds = tuple([round(x, 3) if isinstance(x, float) else x for x in calculated_bounds])
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
def test_pydmdrawing_is_square(qtbot, monkeypatch, width, height, expected_result):
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
def test_get_inner_max(qtbot, monkeypatch, width, height, rotation_deg, expected):
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    pydm_drawing._rotation = rotation_deg
    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: height)

    calculated_inner_max = pydm_drawing.get_inner_max()
    calculated_inner_max = tuple([round(x, 3) if isinstance(x, float) else x for x in calculated_inner_max])
    assert calculated_inner_max == expected


def test_properties_and_setters(qtbot):
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    assert pydm_drawing.penWidth == 0
    assert pydm_drawing.penColor == QColor(0, 0, 0)
    assert pydm_drawing.rotation == 0.0

    pydm_drawing.penWidth = 5
    pydm_drawing.penColor = QColor(255, 0, 0)
    pydm_drawing.rotation = 99.99

    assert pydm_drawing.penWidth == 5
    assert pydm_drawing.penColor == QColor(255, 0, 0)
    assert pydm_drawing.rotation == 99.99


@pytest.mark.parametrize("alarm_sensitive_content", [
    True,
    False,
])
def test_pydmdrawingline_draw_item(qtbot, signals, test_alarm_style_sheet_map, alarm_sensitive_content):
   pydm_drawingline = PyDMDrawingLine()
   qtbot.addWidget(pydm_drawingline)

   pydm_drawingline.alarmSensitiveContent = alarm_sensitive_content
   signals.new_severity_signal.connect(pydm_drawingline.alarmSeverityChanged)
   signals.new_severity_signal.emit(PyDMWidget.ALARM_MAJOR)

   with qtbot.waitExposed(pydm_drawingline):
       pydm_drawingline.show()
   pydm_drawingline.setFocus()

   def wait_focus():
       return pydm_drawingline.hasFocus()

   qtbot.waitUntil(wait_focus, timeout=5000)

   alarm_color = test_alarm_style_sheet_map[PyDMWidget.ALARM_CONTENT][pydm_drawingline._alarm_state]

   if alarm_sensitive_content:
       assert pydm_drawingline.brush.color() == QColor(alarm_color["color"])
   else:
       assert pydm_drawingline.brush.color() == pydm_drawingline._default_color


def test_pydmdrawingimage_construct(qtbot):
    pydm_drawingimage = PyDMDrawingImage()
    qtbot.addWidget(pydm_drawingimage)

    assert pydm_drawingimage._pixmap is not None
    assert pydm_drawingimage._aspect_ratio_mode == Qt.KeepAspectRatio
    assert pydm_drawingimage.filename == ""

    if not is_pydm_app():
        assert pydm_drawingimage.get_designer_window()


class Designer_Form(QWidget):
    def __init__(self, parent):
        self.parent = parent

    def parent(self):
        return self.parent


class Designer_Parent_Form:
    def __init__(self, parent):
        self.parent = parent

    def parent(self):
        return self.parent

@pytest.mark.parametrize("parent_type", [
    None,
])
def test_pydmdrawingimage_get_designer_window(qtbot, parent_type):
    parent = None
    if parent_type:
        parent = parent_type(parent=None)

    pydm_drawingimage = PyDMDrawingImage(parent=parent)
    qtbot.addWidget(pydm_drawingimage)

    designer_window = pydm_drawingimage.get_designer_window()

    if parent is None:
        assert designer_window is None
    elif isinstance(parent, QDesignerFormWindowInterface):
        assert designer_window == parent
    else:
        assert designer_window == parent.parent()


@pytest.mark.parametrize("width, height, pen_width, rotation_deg, start_angle_deg, span_angle_deg", [
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
def test_pydmdrawingpie_draw_item(qtbot, monkeypatch, width, height, pen_width, rotation_deg, start_angle_deg,
                                  span_angle_deg):
    pydm_drawingpie = PyDMDrawingPie()
    qtbot.addWidget(pydm_drawingpie)

    pydm_drawingpie._pen_width = pen_width
    pydm_drawingpie._rotation = rotation_deg
    pydm_drawingpie._start_angle = start_angle_deg
    pydm_drawingpie._span_angle = span_angle_deg

    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: height)

    pydm_drawingpie.draw_item()


@pytest.mark.parametrize("width, height, pen_width, rotation_deg, start_angle_deg, span_angle_deg", [
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
def test_pydmdrawingchord_draw_item(qtbot, monkeypatch, width, height, pen_width, rotation_deg, start_angle_deg,
                                    span_angle_deg):
    pydm_drawingchord = PyDMDrawingChord()
    qtbot.addWidget(pydm_drawingchord)

    pydm_drawingchord._pen_width = pen_width
    pydm_drawingchord._rotation = rotation_deg
    pydm_drawingchord._start_angle = start_angle_deg
    pydm_drawingchord._span_angle = span_angle_deg

    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: height)

    pydm_drawingchord.draw_item()


# --------------------
# NEGATIVE TEST CASES
# --------------------
@pytest.mark.parametrize("width, height, rotation_deg", [
    (0, 10.35, 0.0),
    (10.35, 0, 0.0),
    (0, 0, 45.0),
])
def test_get_inner_max_neg(qtbot, monkeypatch, caplog, width, height, rotation_deg):
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    pydm_drawing._rotation = rotation_deg
    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: height)

    for record in caplog.records:
        assert record.levelno == ERROR

    pydm_drawing.get_inner_max()

    if width == 0:
        assert "Invalid width. The value must be greater than 0" in caplog.text
    elif height == 0:
        assert "Invalid height. The value must be greater than 0" in caplog.text
