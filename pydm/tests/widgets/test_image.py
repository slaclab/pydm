
# Unit Tests for the PyDMImageView Widgets


import pytest

from ...PyQt.QtGui import QActionGroup, QKeyEvent
from ...PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QTimer, Q_ENUMS, QThread, QEvent, Qt
from pyqtgraph import ImageView
from pyqtgraph import ColorMap
from pyqtgraph.graphicsItems.ViewBox.ViewBoxMenu import ViewBoxMenu
import numpy as np
import threading
import logging
logger = logging.getLogger(__name__)

from ...widgets.image import ReadingOrder, ImageUpdateThread, PyDMImageView
from ...widgets.channel import PyDMChannel
from ...widgets.colormaps import cmaps, cmap_names, PyDMColorMap
from ...widgets.base import PyDMWidget
import pyqtgraph
from .test_lineedit import find_action_from_menu


def test_readingorder_construct():
    reading_order = ReadingOrder()

    assert reading_order.Fortranlike == 0
    assert reading_order.Clike == 1


def test_pydmimageview_construct(qtbot):
    pydm_image_view = PyDMImageView(image_channel="image_channel", width_channel="width_channel")
    qtbot.addWidget(pydm_image_view)

    assert pydm_image_view.thread is None
    assert pydm_image_view.axes == dict({'t': None, "x": 0, "y": 1, "c": None})
    assert pydm_image_view._imagechannel == "image_channel"
    assert pydm_image_view._widthchannel == "width_channel"
    assert np.array_equal(pydm_image_view.image_waveform, np.zeros(0))
    assert pydm_image_view._image_width == 0
    assert pydm_image_view._normalize_data is False
    assert pydm_image_view._auto_downsample is True

    assert pydm_image_view.cm_min == 0.0
    assert pydm_image_view.cm_max == 255.0

    assert pydm_image_view._reading_order == ReadingOrder.Fortranlike
    assert pydm_image_view.color_maps == cmaps

    for action in pydm_image_view.cm_group.actions():
        assert action.isCheckable()
        assert pydm_image_view.cmap_for_action[action] in pydm_image_view.color_maps

    assert pydm_image_view._colormap == PyDMColorMap.Inferno
    assert np.array_equal(pydm_image_view._cm_colors, pydm_image_view.color_maps[pydm_image_view._colormap])
    assert pydm_image_view.colorMap == pydm_image_view._colormap

    assert pydm_image_view.needs_redraw is False
    assert pydm_image_view._redraw_rate == 30


def test_widget_ctx_menu(qtbot):
    """
    Also test _changeColorMap()
    Parameters
    ----------
    qtbot

    Returns
    -------

    """
    pydm_image_view = PyDMImageView()
    qtbot.addWidget(pydm_image_view)

    menu = pydm_image_view.widget_ctx_menu()
    for action in pydm_image_view.cmap_for_action.keys():
        assert find_action_from_menu(menu, action.text())
        pydm_image_view._changeColorMap(action)
        assert pydm_image_view.colorMap == pydm_image_view.cmap_for_action[action]


@pytest.mark.parametrize("new_cm_min, new_cm_max", [
    (5, 5),
    (5, 7),
    (5, 20),
    (9, 15),
    (100, 10)
])
def test_set_color_limits(qtbot, new_cm_min, new_cm_max):
    """
    Also testing colorMapMin and colorMapMax properties and setters.

    Parameters
    ----------
    qtbot
    new_cm_min
    new_cm_max

    Returns
    -------

    """
    pydm_image_view = PyDMImageView()
    qtbot.addWidget(pydm_image_view)

    assert pydm_image_view.colorMapMin == 0.0
    assert pydm_image_view.colorMapMax == 255.0

    pydm_image_view.cm_max = 5
    pydm_image_view.colorMapMin = 10
    assert pydm_image_view.colorMapMin == 10
    assert pydm_image_view.colorMapMax == 10

    pydm_image_view.cm_min = 10
    pydm_image_view.colorMapMax = 5
    assert pydm_image_view.colorMapMin == 5
    assert pydm_image_view.colorMapMax == 5

    pydm_image_view.setColorMapLimits(new_cm_min, new_cm_max)

    if new_cm_min >= new_cm_max:
        # Nothing will be changed
        pydm_image_view.colorMapMin == 0
        pydm_image_view.colorMapMax == 10
    else:
        assert pydm_image_view.colorMapMin == new_cm_min
        assert pydm_image_view.colorMapMax == new_cm_max


@pytest.mark.parametrize("new_cmap, cm_colors", [
    (PyDMColorMap.Plasma, cmaps[PyDMColorMap.Plasma]),
    (PyDMColorMap.Plasma, np.array(0)),
    (None, cmaps[PyDMColorMap.Magma]),
    (None, np.zeros(0)),
])
def test_colormap_property_and_setter(qtbot, new_cmap, cm_colors):
    """
    Also testing setColorMap()

    Parameters
    ----------
    qtbot
    new_cmap
    cm_colors

    Returns
    -------

    """
    pydm_image_view = PyDMImageView()
    qtbot.addWidget(pydm_image_view)

    assert pydm_image_view.colorMap == PyDMColorMap.Inferno
    pydm_image_view._cm_colors = cm_colors

    pydm_image_view.colorMap = new_cmap

    if new_cmap:
        assert np.array_equal(pydm_image_view._cm_colors, pydm_image_view.color_maps[new_cmap])
        for action in pydm_image_view.cm_group.actions():
            if pydm_image_view.cmap_for_action[action] == pydm_image_view._colormap:
                assert action.isChecked()
            else:
                assert not action.isChecked()
    else:
        if not pydm_image_view._cm_colors.any():
            assert pydm_image_view.colorMap == None
        else:
            pos = np.linspace(0.0, 1.0, num=len(pydm_image_view._cm_colors))
            cmap = ColorMap(pos, pydm_image_view._cm_colors)
            assert len(pos) == len(cmap.color)


@pytest.mark.parametrize("connected", [
    True,
    False
])
def test_image_connection_state_changed(qtbot, signals, monkeypatch, caplog, connected):
    pydm_image_view = PyDMImageView()
    qtbot.addWidget(pydm_image_view)

    caplog.set_level(logging.INFO)

    def mock_start(*args):
        logger.info("QTimer redraw starts.")
    monkeypatch.setattr(QTimer, "start", mock_start)

    def mock_stop(*args):
        logger.info("QTimer redraw stops.")
    monkeypatch.setattr(QTimer, "stop", mock_stop)

    signals.connection_state_signal.connect(pydm_image_view.image_connection_state_changed)
    signals.connection_state_signal.emit(connected)

    if connected:
        assert "QTimer redraw starts." in caplog.text
    else:
        assert "QTimer redraw stops." in caplog.text


@pytest.mark.parametrize("new_image", [
    np.array([[-1.2, 3.5], [5.6, 6.7], [7.0, 8.9]]),
    np.zeros(0)
])
def test_image_value_changed(qtbot, signals, new_image):
    pydm_image_view = PyDMImageView()
    qtbot.addWidget(pydm_image_view)

    signals.send_value_signal[np.ndarray].connect(pydm_image_view.image_value_changed)
    signals.send_value_signal[np.ndarray].emit(new_image)

    if new_image is None or new_image.size == 0:
        assert np.array_equal(pydm_image_view.image_waveform, np.zeros(0))
        assert not pydm_image_view.needs_redraw
    else:
        assert np.array_equal(pydm_image_view.image_waveform , new_image)
        assert pydm_image_view.needs_redraw


@pytest.mark.parametrize("new_width", [
    100,
    None,
])
def test_image_width_change(qtbot, signals, new_width):
    pydm_image_view = PyDMImageView()
    qtbot.addWidget(pydm_image_view)

    pydm_image_view._image_width = 10

    value_signal = signals.new_value_signal
    value_signal[int].connect(pydm_image_view.image_width_changed)
    value_signal[int].emit(new_width)

    if new_width is None:
        assert pydm_image_view._image_width == 0
    else:
        assert pydm_image_view._image_width == new_width


def test_process_image(qtbot):
    pydm_image_view = PyDMImageView()
    qtbot.addWidget(pydm_image_view)

    image_data = np.array([[1.2, 2.2], [-3.5, 7.5]])
    assert np.array_equal(pydm_image_view.process_image(image_data), image_data)


@pytest.mark.parametrize("image_width, width_channel", [
    (1, "width_channel"),
    (2, None),
    (1, "")
])
def test_image_width_and_width_channel(qtbot, image_width, width_channel):
    pydm_image_view = PyDMImageView()
    qtbot.addWidget(pydm_image_view)

    assert pydm_image_view.imageWidth == 0

    pydm_image_view.widthChannel = width_channel
    pydm_image_view.imageWidth = image_width

    if width_channel:
        assert pydm_image_view.imageWidth == 0
    else:
        assert pydm_image_view.imageWidth == int(image_width)
    assert pydm_image_view.widthChannel == str(width_channel)


@pytest.mark.parametrize("thread, image_width, needs_redraw, reading_order, normalize_data", [
    (None, 100, True, ReadingOrder.Fortranlike, True),
    (None, 100, True, ReadingOrder.Fortranlike, True),
    (QThread(), 100, True, ReadingOrder.Fortranlike, True)
])
def test_redraw_image(qtbot, signals, caplog, thread, image_width, needs_redraw, reading_order, normalize_data):
    pydm_image_view = PyDMImageView()
    qtbot.addWidget(pydm_image_view)

    caplog.set_level(logging.DEBUG)

    assert pydm_image_view.thread is None

    pydm_image_view.thread = thread
    pydm_image_view.imageWidth = image_width
    pydm_image_view.needs_redraw = needs_redraw
    pydm_image_view.readingOrder = reading_order
    pydm_image_view.normalizeData = normalize_data

    new_image = np.array([[1.1, 2.2], [3.3, 4.5]])
    signals.send_value_signal[np.ndarray].connect(pydm_image_view.image_value_changed)
    signals.send_value_signal[np.ndarray].emit(new_image)

    signals.connection_state_signal.connect(pydm_image_view.image_connection_state_changed)
    signals.connection_state_signal.emit(True)
    signals.connection_state_signal.emit(False)

    pydm_image_view.redrawImage()

    if needs_redraw:
        if not thread:
            assert "ImageView RedrawImage Thread Launched" in caplog.text
        else:
            assert "Image processing has taken longer than the refresh rate" in caplog.text
    else:
        assert "ImageUpdateThread - needs redraw is False. Aborting." in caplog.text


def test_properties_and_setters(qtbot):
    pydm_image_view = PyDMImageView()
    qtbot.addWidget(pydm_image_view)

    # autoDownSample
    assert pydm_image_view.autoDownsample is True
    pydm_image_view.autoDownsample = False
    assert pydm_image_view.autoDownsample is False

    # normalizeData
    assert pydm_image_view.normalizeData is False
    pydm_image_view.normalizeData = True
    assert pydm_image_view.normalizeData is True

    # readingOrder
    assert pydm_image_view.readingOrder == ReadingOrder.Fortranlike
    pydm_image_view.readingOrder = ReadingOrder.Clike
    assert pydm_image_view.readingOrder == ReadingOrder.Clike

    # imageChannel
    assert pydm_image_view.imageChannel == "None"
    pydm_image_view.imageChannel = "abc"
    assert pydm_image_view.imageChannel == "abc"

    # maxRedrawRate
    pydm_image_view.maxRedrawRate == 30
    pydm_image_view.maxRedrawRate = 60
    assert pydm_image_view.maxRedrawRate == 60
    assert pydm_image_view.redraw_timer.interval() == int((1.0 / pydm_image_view.maxRedrawRate) * 1000)


def test_key_press_event(qtbot, caplog):
    pydm_image_view = PyDMImageView()
    qtbot.addWidget(pydm_image_view)

    caplog.set_level(logging.DEBUG)

    key_event = QKeyEvent(QEvent.KeyPress, Qt.Key_A, Qt.NoModifier)
    pydm_image_view.keyPressEvent(key_event)
    assert "Key event '{0}' received.".format(key_event) in caplog.text


def test_channels(qtbot):
    pydm_image_view = PyDMImageView()
    qtbot.addWidget(pydm_image_view)

    pydm_image_view_channels = pydm_image_view.channels()

    default_channels =[
        PyDMChannel(
            address=pydm_image_view.imageChannel,
            connection_slot=pydm_image_view.image_connection_state_changed,
            value_slot=pydm_image_view.image_value_changed,
            severity_slot=pydm_image_view.alarmSeverityChanged),
        PyDMChannel(
            address=pydm_image_view.widthChannel,
            connection_slot=pydm_image_view.connectionStateChanged,
            value_slot=pydm_image_view.image_width_changed,
            severity_slot=pydm_image_view.alarmSeverityChanged)]

    assert pydm_image_view_channels == default_channels


def test_channels_for_tools(qtbot):
    """
    Test the channel exposure for external tools.

    Expectations:
    The current default implementation is to provide the same channels via channel_for_tools as with channels(). This
    test ensures that will happen.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_image_view = PyDMImageView()
    qtbot.addWidget(pydm_image_view)

    assert all(x == y for x, y in zip(pydm_image_view.channels(), pydm_image_view.channels_for_tools()))
    for channel in pydm_image_view.channels():
        assert channel.address == pydm_image_view.imageChannel









