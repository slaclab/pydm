# Test the PyDMByteIndicator and PyDMBitIndicator Widgets

import pytest

from ...PyQt.QtGui import QWidget, QPaintEvent, QCommonStyle, QTabWidget, QColor, QPen, QGridLayout, QLabel, \
    QFontMetrics, QPainter, QBrush, QStyleOption, QStyle
from ...PyQt.QtCore import pyqtProperty, Qt, QSize, QPoint, QRect
import numpy as np
from ...widgets.byte import PyDMBitIndicator, PyDMByteIndicator


def test_pydm_bit_indicator_construct(qtbot):
    pydm_bitindicator = PyDMBitIndicator()
    qtbot.addWidget(pydm_bitindicator)

    assert pydm_bitindicator.autoFillBackground()
    assert pydm_bitindicator.circle is False
    assert type(pydm_bitindicator._painter) == QPainter
    assert pydm_bitindicator._brush == QBrush(Qt.SolidPattern)
    assert pydm_bitindicator._pen == QPen(Qt.SolidLine)


@pytest.mark.parametrize("draw_circle", [
    True,
    False
])
def test_pydm_bit_indicator_paint_event(qtbot, monkeypatch, draw_circle):
    pydm_bitindicator = PyDMBitIndicator()
    qtbot.addWidget(pydm_bitindicator)

    pydm_bitindicator.circle = draw_circle
    monkeypatch.setattr(QCommonStyle, "drawPrimitive", lambda *args: True)

    paint_event = QPaintEvent(QRect(100, 100, 100, 100))
    pydm_bitindicator.paintEvent(paint_event)

    painter = pydm_bitindicator._painter
    assert painter.pen().style() == QPainter.Antialiasing
    assert painter.pen().brush().style() == Qt.SolidPattern
    assert painter.pen().style() == Qt.SolidLine


def test_pydm_bit_indicator_set_color(qtbot, monkeypatch):
    pydm_bitindicator = PyDMBitIndicator()
    qtbot.addWidget(pydm_bitindicator)

    monkeypatch.setattr(QCommonStyle, "drawPrimitive", lambda *args: True)
    new_color = QColor(255, 0, 0)
    pydm_bitindicator.setColor(new_color)

    assert pydm_bitindicator._brush.color() == new_color


def test_pydm_bit_indicator_minimum_size_hint(qtbot):
    pydm_bitindicator = PyDMBitIndicator()
    qtbot.addWidget(pydm_bitindicator)

    fm = QFontMetrics(pydm_bitindicator.font())
    pydm_bitindicator.minimumSizeHint() == QSize(fm.height(), fm.height())


def test_pydm_byte_indicator_construct(qtbot):
    pydm_byteindicator = PyDMByteIndicator()
    qtbot.addWidget(pydm_byteindicator)

    assert pydm_byteindicator.value == 0
    assert type(pydm_byteindicator.layout()) == QGridLayout

    assert pydm_byteindicator._on_color == QColor(0, 255, 0)
    assert pydm_byteindicator._off_color == QColor(100, 100, 100)
    assert pydm_byteindicator._disconnected_color == QColor(255, 255, 255)
    assert pydm_byteindicator._invalid_color == QColor(255, 0, 255)

    assert pydm_byteindicator._pen_style == Qt.SolidLine
    assert pydm_byteindicator._line_pen == QPen(pydm_byteindicator._pen_style)
    assert pydm_byteindicator._orientation == Qt.Vertical


    assert len(pydm_byteindicator._labels) == 1
    assert pydm_byteindicator._show_labels is True
    assert pydm_byteindicator._label_position == QTabWidget.East
    assert pydm_byteindicator._num_bits == 1
    assert len(pydm_byteindicator._indicators) == 1
    assert pydm_byteindicator._circles is False
    assert pydm_byteindicator.layout().horizontalSpacing() == 5
    assert pydm_byteindicator.layout().verticalSpacing() == 0
    assert pydm_byteindicator.layout().originCorner() == Qt.Corner(Qt.TopLeftCorner)

    assert pydm_byteindicator._big_endian is False
    assert pydm_byteindicator._shift == 0
    assert pydm_byteindicator.numBits == 1


def test_int_for_designer(qtbot):
    pydm_byteindicator = PyDMByteIndicator()
    qtbot.addWidget(pydm_byteindicator)

    pydm_byteindicator.init_for_designer()

    assert pydm_byteindicator._connected is True
    assert pydm_byteindicator.value == 5


def _verify_bit_colors(widget, expected_indicator_bit_colors):
    for i in range(0, widget._num_bits):
        indicator = widget._indicators[i]
        color = indicator._brush.color()
        assert color == expected_indicator_bit_colors[i]


@pytest.mark.parametrize("is_connected, value, num_bits, expected_indicator_bit_colors", [
    (True, 4, 4, [PyDMByteIndicator.OFF_COLOR, PyDMByteIndicator.OFF_COLOR, PyDMByteIndicator.ON_COLOR,
                  PyDMByteIndicator.OFF_COLOR]),
    (True, 15, 4, [PyDMByteIndicator.ON_COLOR, PyDMByteIndicator.ON_COLOR, PyDMByteIndicator.ON_COLOR,
                  PyDMByteIndicator.ON_COLOR]),
    (True, 0, 4, [PyDMByteIndicator.OFF_COLOR, PyDMByteIndicator.OFF_COLOR, PyDMByteIndicator.OFF_COLOR,
                  PyDMByteIndicator.OFF_COLOR]),
    (False, 4, 4, [PyDMByteIndicator.DISCONNECTED_COLOR, PyDMByteIndicator.DISCONNECTED_COLOR,
                   PyDMByteIndicator.DISCONNECTED_COLOR, PyDMByteIndicator.DISCONNECTED_COLOR]),
    (False, 15, 4, [PyDMByteIndicator.DISCONNECTED_COLOR, PyDMByteIndicator.DISCONNECTED_COLOR,
                    PyDMByteIndicator.DISCONNECTED_COLOR, PyDMByteIndicator.DISCONNECTED_COLOR]),
])
def test_update_indicators(qtbot, is_connected, value, num_bits, expected_indicator_bit_colors):
    pydm_byteindicator = PyDMByteIndicator()
    qtbot.addWidget(pydm_byteindicator)

    pydm_byteindicator._connected = is_connected
    pydm_byteindicator.value = value
    pydm_byteindicator.numBits = num_bits

    pydm_byteindicator.update_indicators()
    _verify_bit_colors(pydm_byteindicator, expected_indicator_bit_colors)


def test_properties_and_setters(qtbot):
    pydm_byteindicator = PyDMByteIndicator()
    qtbot.addWidget(pydm_byteindicator)

    pydm_byteindicator._labels = [QLabel("Bit 0"), QLabel("Bit 1"), QLabel("Bit 2"), QLabel("Bit 3")]

    # onColor
    assert pydm_byteindicator.onColor == PyDMByteIndicator.ON_COLOR
    new_on_color = QColor(1, 1, 1)
    pydm_byteindicator.onColor = new_on_color
    assert pydm_byteindicator.onColor == new_on_color

    # offColor
    assert pydm_byteindicator.offColor == PyDMByteIndicator.OFF_COLOR
    new_off_color = QColor(2, 2, 2)
    pydm_byteindicator.offColor = new_off_color
    assert pydm_byteindicator.offColor == new_off_color

    # orientation
    assert pydm_byteindicator.orientation == Qt.Vertical
    pydm_byteindicator.orientation = Qt.Horizontal
    assert pydm_byteindicator.orientation == Qt.Horizontal

    # showLabels
    assert pydm_byteindicator.showLabels
    pydm_byteindicator.showLabels = False
    assert pydm_byteindicator.showLabels is False
    for label in pydm_byteindicator._labels:
        assert not label.isVisible()

    # bigEndian
    assert pydm_byteindicator.bigEndian is False
    assert pydm_byteindicator.layout().originCorner() == Qt.Corner(Qt.TopLeftCorner)
    pydm_byteindicator.bigEndian = True
    assert pydm_byteindicator.layout().originCorner() == Qt.Corner(Qt.BottomLeftCorner)

    # circles
    pydm_byteindicator._connected = True
    pydm_byteindicator.value = 16
    pydm_byteindicator.numBits = 4

    assert pydm_byteindicator.circles is False
    pydm_byteindicator.update_indicators()
    for indicator in pydm_byteindicator._indicators:
        assert indicator.circle == False

    pydm_byteindicator.circles = True
    for indicator in pydm_byteindicator._indicators:
        assert indicator.circle == True

    # labelPosition
    assert pydm_byteindicator.labelPosition == QTabWidget.East
    pydm_byteindicator.labelPosition = QTabWidget.North
    assert pydm_byteindicator.labelPosition == QTabWidget.North

    # shift
    assert pydm_byteindicator.shift == 0
    pydm_byteindicator.shift = 4
    assert pydm_byteindicator.shift == 4


def test_numBits(qtbot):
    pydm_byteindicator = PyDMByteIndicator()
    qtbot.addWidget(pydm_byteindicator)

    pydm_byteindicator._connected = True
    pydm_byteindicator._labels = [QLabel("Bit 0"), QLabel("Bit 1"), QLabel("Bit 2"), QLabel("Bit 3")]
    pydm_byteindicator.value = 8
    pydm_byteindicator.numBits = 4

    assert pydm_byteindicator.numBits == 4
    pydm_byteindicator.update_indicators()

    old_labels = pydm_byteindicator._labels

    pydm_byteindicator.numBits = 6
    new_labels = ["Bit {}".format(i) for i in range(0, pydm_byteindicator._num_bits)]
    for i, old_label in enumerate(old_labels):
        if i >= pydm_byteindicator._num_bits:
            break
        new_labels[i] = old_label

    assert pydm_byteindicator._labels == new_labels


def test_labels(qtbot):
    pydm_byteindicator = PyDMByteIndicator()
    qtbot.addWidget(pydm_byteindicator)

    pydm_byteindicator._labels = [QLabel("Bit 0"), QLabel("Bit 1")]
    current_labels = pydm_byteindicator.labels
    assert len(current_labels) == 2

    pydm_byteindicator.labels = ["Bit 0", "Bit 1", "Bit 2", "Bit 3"]
    current_labels = pydm_byteindicator.labels
    assert len(current_labels) == 4
    assert pydm_byteindicator.showLabels


def test_connection_changed(qtbot, signals):
    pydm_byteindicator = PyDMByteIndicator()
    qtbot.addWidget(pydm_byteindicator)

    pydm_byteindicator._connected = True
    pydm_byteindicator.value = 8
    pydm_byteindicator.numBits = 4

    pydm_byteindicator.update_indicators()
    expected_indicator_bit_colors = [PyDMByteIndicator.OFF_COLOR, PyDMByteIndicator.OFF_COLOR,
                                     PyDMByteIndicator.OFF_COLOR, PyDMByteIndicator.ON_COLOR]

    _verify_bit_colors(pydm_byteindicator, expected_indicator_bit_colors)

    signals.connection_state_signal.connect(pydm_byteindicator.connectionStateChanged)
    signals.connection_state_signal.emit(False)

    expected_indicator_bit_colors = [PyDMByteIndicator.DISCONNECTED_COLOR, PyDMByteIndicator.DISCONNECTED_COLOR,
                                     PyDMByteIndicator.DISCONNECTED_COLOR, PyDMByteIndicator.DISCONNECTED_COLOR]

    _verify_bit_colors(pydm_byteindicator, expected_indicator_bit_colors)


@pytest.mark.parametrize("orientation, label_position", [
    (Qt.Vertical, QTabWidget.East),
    (Qt.Vertical, QTabWidget.West),
    (Qt.Vertical, QTabWidget.North),
    (Qt.Vertical, QTabWidget.South),

    (Qt.Horizontal, QTabWidget.North),
    (Qt.Horizontal, QTabWidget.South),
    (Qt.Horizontal, QTabWidget.East),
    (Qt.Horizontal, QTabWidget.West)
])
def test_rebuild_and_clear_layout(qtbot, orientation, label_position):
    pydm_byteindicator = PyDMByteIndicator()
    qtbot.addWidget(pydm_byteindicator)

    # Must set the values to the attributes directly, not via the setters, which will call rebuild_layout() prematurely
    pydm_byteindicator._orientation = orientation
    pydm_byteindicator._label_position = label_position
    pydm_byteindicator._labels = [QLabel("Bit 0"), QLabel("Bit 1"), QLabel("Bit 2"), QLabel("Bit 3")]

    pydm_byteindicator._connected = True
    pydm_byteindicator.value = 8
    pydm_byteindicator.numBits = 4

    pydm_byteindicator.rebuild_layout()
    for col in range(0, pydm_byteindicator.layout().columnCount()):
        for row in range(0, pydm_byteindicator.layout().rowCount()):
            assert pydm_byteindicator.layout().itemAtPosition(row, col)

    pydm_byteindicator.clear()
    for col in range(0, pydm_byteindicator.layout().columnCount()):
        for row in range(0, pydm_byteindicator.layout().rowCount()):
            assert pydm_byteindicator.layout().itemAtPosition(row, col) is None


@pytest.mark.parametrize("circles, orientation", [
    (True, Qt.Horizontal),
    (True, Qt.Vertical),
    (False, Qt.Horizontal),
    (False, Qt.Vertical),
])
def test_set_spacing(qtbot, circles, orientation):
    pydm_byteindicator = PyDMByteIndicator()
    qtbot.addWidget(pydm_byteindicator)

    pydm_byteindicator._circles = circles
    pydm_byteindicator._orientation = orientation

    pydm_byteindicator.set_spacing()

    label_spacing = 5
    indicator_spacing = 0
    if circles:
        indicator_spacing = 5

    layout = pydm_byteindicator.layout()
    if orientation == Qt.Horizontal:
        assert layout.horizontalSpacing() == indicator_spacing
        assert layout.verticalSpacing() == label_spacing
    elif orientation == Qt.Vertical:
        assert layout.horizontalSpacing() == label_spacing
        assert layout.verticalSpacing() == indicator_spacing


def test_value_changed(qtbot, signals):
    pydm_byteindicator = PyDMByteIndicator()
    qtbot.addWidget(pydm_byteindicator)

    pydm_byteindicator._connected = True
    pydm_byteindicator.value = 8
    pydm_byteindicator.numBits = 4

    pydm_byteindicator.value = 2

    pydm_byteindicator.update_indicators()
    expected_indicator_bit_colors = [PyDMByteIndicator.OFF_COLOR, PyDMByteIndicator.ON_COLOR,
                                     PyDMByteIndicator.OFF_COLOR, PyDMByteIndicator.OFF_COLOR]
    _verify_bit_colors(pydm_byteindicator, expected_indicator_bit_colors)

    signals.new_value_signal[int].connect(pydm_byteindicator.channelValueChanged)
    signals.new_value_signal[int].emit(4)

    expected_indicator_bit_colors = [PyDMByteIndicator.OFF_COLOR, PyDMByteIndicator.OFF_COLOR,
                                     PyDMByteIndicator.ON_COLOR, PyDMByteIndicator.OFF_COLOR]
    _verify_bit_colors(pydm_byteindicator, expected_indicator_bit_colors)









