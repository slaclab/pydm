# Unit Tests for the PyDMSlider Widget

import pytest
from logging import ERROR
import numpy as np

from ...PyQt.QtGui import QFrame, QLabel, QSlider, QVBoxLayout, QHBoxLayout, QSizePolicy, QWidget
from ...PyQt.QtCore import Qt, pyqtSignal, pyqtSlot, pyqtProperty, QMargins

from ...widgets.slider import PyDMSlider
from ...widgets.base import PyDMWritableWidget, compose_stylesheet


# --------------------
# POSITIVE TEST CASES
# --------------------

def test_construct(qtbot):
    pydm_slider = PyDMSlider()
    qtbot.addWidget(pydm_slider)

    assert pydm_slider.alarmSensitiveContent is True
    assert pydm_slider.alarmSensitiveBorder is False
    assert pydm_slider._show_limit_labels is True
    assert pydm_slider._show_value_label is True
    assert pydm_slider._user_defined_limits is False
    assert pydm_slider._needs_limit_info is True
    assert pydm_slider._minimum is None
    assert pydm_slider._maximum is None
    assert pydm_slider._user_minimum == -10.0
    assert pydm_slider._user_maximum == 10.0
    assert pydm_slider._num_steps == 101
    assert pydm_slider.orientation == Qt.Horizontal
    assert pydm_slider.isEnabled() is False

    assert type(pydm_slider.low_lim_label) == QLabel
    assert pydm_slider.low_lim_label.sizePolicy() == QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    assert pydm_slider.low_lim_label.alignment() == Qt.Alignment(Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)


    assert type(pydm_slider.high_lim_label) == QLabel
    assert pydm_slider.high_lim_label.sizePolicy() == QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    assert pydm_slider.high_lim_label.alignment() == Qt.Alignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)


    assert type(pydm_slider._slider) == QSlider
    assert pydm_slider._slider.orientation() == Qt.Orientation(Qt.Horizontal)

    assert pydm_slider._slider_position_to_value_map is None
    assert pydm_slider._mute_internal_slider_changes is False
    assert pydm_slider._orientation == Qt.Horizontal


def test_init_for_designer(qtbot):
    pydm_slider = PyDMSlider()
    qtbot.addWidget(pydm_slider)

    pydm_slider.init_for_designer()
    assert pydm_slider.value == 0.0


def test_properties_and_setters(qtbot):
    pydm_slider = PyDMSlider()
    qtbot.addWidget(pydm_slider)

    assert pydm_slider.orientation == Qt.Horizontal
    pydm_slider.orientation = Qt.Vertical
    assert pydm_slider.orientation == Qt.Vertical


@pytest.mark.parametrize("new_orientation", [
    Qt.Horizontal,
    Qt.Vertical
])
def test_setup_widgets_for_orientation(qtbot, new_orientation):
    pydm_slider = PyDMSlider()
    qtbot.addWidget(pydm_slider)

    pydm_slider.setup_widgets_for_orientation(new_orientation)
    layout = pydm_slider.layout()
    assert layout

    if new_orientation == Qt.Horizontal:
        assert type(layout) == QVBoxLayout
        assert layout.parent() == pydm_slider
        assert layout.contentsMargins() == QMargins(4, 0, 4, 4)
        assert layout.count() == 2

        label_layout = layout.itemAt(0)
        assert type(label_layout) == QHBoxLayout
        assert label_layout.count() == 5
        assert all([label_layout.stretch(i) == 0 for i in range(0, label_layout.count())])
        assert pydm_slider.orientation == new_orientation
    elif new_orientation == Qt.Vertical:
        assert type(layout) == QHBoxLayout
        assert layout.parent() == pydm_slider
        assert layout.contentsMargins() == QMargins(0, 4, 4, 4)
        assert layout.count() == 2

        label_layout = layout.itemAt(0)
        assert type(label_layout) == QVBoxLayout
        assert label_layout.count() == 5
        assert all([label_layout.stretch(i) == 0 for i in range(0, label_layout.count())])
        assert pydm_slider._slider.orientation() == new_orientation


@pytest.mark.parametrize("minimum, maximum, current_value", [
    (None, None, None),
    (10, 20.5, 11),
])
def test_update_labels(qtbot, signals, minimum, maximum, current_value):
    def validate(value, widget):
        if value is None:
            assert widget.text() == ""
        else:
            assert widget.text() == str(float(value))

    pydm_slider = PyDMSlider()
    qtbot.addWidget(pydm_slider)

    pydm_slider.userDefinedLimits = True
    pydm_slider.userMinimum = minimum
    pydm_slider.userMaximum = maximum

    signals.internal_slider_moved[int].connect(pydm_slider.internal_slider_moved)
    signals.internal_slider_moved[int].emit(current_value)

    pydm_slider.update_labels()

    validate(minimum, pydm_slider.low_lim_label)
    validate(maximum, pydm_slider.high_lim_label)
    validate(pydm_slider._slider_position_to_value_map[current_value], pydm_slider.value_label)


# --------------------
# NEGATIVE TEST CASES
# --------------------

@pytest.mark.parametrize("new_orientation", [
    -1,
    1000,
    None,
])
def test_setup_widgets_for_orientation_neg(qtbot, caplog, new_orientation):
    pydm_slider = PyDMSlider()
    qtbot.addWidget(pydm_slider)

    pydm_slider.setup_widgets_for_orientation(new_orientation)

    for record in caplog.records:
        assert record.levelno == ERROR
    assert "Invalid orientation" in caplog.text
