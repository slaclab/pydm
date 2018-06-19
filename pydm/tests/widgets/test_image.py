
# Unit Tests for the PyDMImageView Widgets


import pytest

from ...PyQt.QtGui import QKeyEvent
from ...PyQt.QtCore import pyqtProperty, QTimer, QThread, QEvent, Qt
from pyqtgraph import ColorMap
import numpy as np
import logging
logger = logging.getLogger(__name__)

from ...widgets.image import ReadingOrder, PyDMImageView
from ...widgets.channel import PyDMChannel
from ...widgets.colormaps import cmaps, PyDMColorMap
from .test_lineedit import find_action_from_menu


def test_readingorder_construct():
    """
    Test the construction of ReadingOrder.

    Expectations:
    Default values are assigned for the reading order types.
    """

    reading_order = ReadingOrder()

    assert reading_order.Fortranlike == 0
    assert reading_order.Clike == 1


def test_pydmimageview_construct(qtbot):
    """
    Test the construction of the Image View widget.

    Expectations:
    Defaut values and context menu actions are as expected.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
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
    Test the widget's context menu, and also test _changeColorMap().

    Expectations:
    1. The context menu contains all the actions from the color map (cmap).
    2. For each color action, execute _changeColorMap (as the triggered signal of the context menu would to this
       method), and confirm that the color map has been updated according to this action execution.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_image_view = PyDMImageView()
    qtbot.addWidget(pydm_image_view)

    menu = pydm_image_view.widget_ctx_menu()
    for action in pydm_image_view.cmap_for_action.keys():
        assert find_action_from_menu(menu, action.text())
        pydm_image_view._changeColorMap(action)
        assert pydm_image_view.colorMap == pydm_image_view.cmap_for_action[action]


@pytest.mark.parametrize("new_cm_min, new_cm_max", [
    (5.0, 5.4),
    (5.3, 7.1),
    (5.0, 20.5),
    (9, 15),
    (100, 10)
])
def test_set_color_limits(qtbot, new_cm_min, new_cm_max):
    """
    Test the widget's properties and setters for the minimum and maximum color values. This also means testing the
    colorMapMin and colorMapMax properties and setters implicitly.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    new_cm_min : int, float
    new_cm_max : int, float

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
        assert pydm_image_view.colorMapMin == 5
        assert pydm_image_view.colorMapMax == 5
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
    Test the image's colorMap property and setter, and Also testing setColorMap().

    Expectations:
    Test assessing and updating the color map while also making sure the currently selected color map is checked in the
    context menu.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    new_cmap : dict
        The new color map to update
    cm_colors : PyDMColorMap
        The selected PyDMColor Map out of the color map collection.
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
            assert pydm_image_view.colorMap == PyDMColorMap.Inferno
        else:
            pos = np.linspace(0.0, 1.0, num=len(pydm_image_view._cm_colors))
            cmap = ColorMap(pos, pydm_image_view._cm_colors)
            assert len(pos) == len(cmap.color)


@pytest.mark.parametrize("connected", [
    True,
    False
])
def test_image_connection_state_changed(qtbot, signals, monkeypatch, caplog, connected):
    """
    Test the widget's handling of the Image Channel connection state change.

    Expectations:
    1. If the connection is established, the redraw timer will start
    2. If the connection is not established, the redraw timer will stop

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        To emit the simulated connection state to the to widget's connection state signal
    monkeypatch : fixture
        To simulate the start or stop of the redraw timer by writing into a log
    caplog : fixture
        To capture the log events written by the simulated redraw timer
    connected : bool
        True if the Image Channel connection is established; False otherwise
    """
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
    """
    Test the widget's handling of an image data update.

    Expectations:
    1. The widget will obtain the new image data as an array if there is data, or None if there's no data
    2. If there is new image data, the "needs_redraw" flag will be set to True; False otherwise.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        To emit the simulated connection to the to widget's new image value signal
    new_image : np.ndarray
        The array containing the new image data
    """
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


def test_image_width_change(qtbot, signals):
    """
    Test the widget's property and setter of the image width.

    Expectations:
    The property will return the up-to-date value, and will set the new value correctly.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        To emit the connection state to the to widget's new image width signal
    """
    pydm_image_view = PyDMImageView()
    qtbot.addWidget(pydm_image_view)

    pydm_image_view._image_width = 10

    value_signal = signals.new_value_signal
    value_signal.connect(pydm_image_view.image_width_changed)
    value_signal.emit(100)
    assert pydm_image_view._image_width == 100

    pydm_image_view.image_width_changed(None)
    assert pydm_image_view._image_width == 100


def test_process_image(qtbot):
    """
    To test the widget's process image entry.

    Expectations:
    The image data provided will be returned as-is as this is a boilerplate method.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_image_view = PyDMImageView()
    qtbot.addWidget(pydm_image_view)

    image_data = np.array([[1.2, 2.2], [-3.5, 7.5]])
    assert np.array_equal(pydm_image_view.process_image(image_data), image_data)


@pytest.mark.parametrize("image_width, width_channel", [
    ("1", "width_channel"),
    ("2", None),
    ("1", "")
])
def test_image_width_and_width_channel(qtbot, image_width, width_channel):
    """
    Test the widget's image width and width channel property and setter.

    Expectations:
    The image width and width channel are strings, and they must be able to be accepted as int and str, respectively.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    image_width : str
        The new image width
    width_channel : str
        The new width channel
    """
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
    """
    The the widget's image redraw, by spawning a new update thread.

    Expectations:
    1. If the needs_redraw flag is set, the RedrawImage thread will be launched, and the ImageView will be updated with
       new image. This action is taken if there is no other RedrawImage thread. Otherwise, this means a misfire in the
       refresh timer, and an error will be returned, stating that the image processing is still taking place longer
       than the refresh rate.
    2. If the needs_redraw flag is not set, the RedrawImage thread will not be run, and an error message will be
       returned.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    signals : fixture
        To emit the connection state to the to widget's new image width signal
    caplog : fixture
        To capture error or event messages returned by the image redraw thread
    thread : ImageUpdateThread
        The thread to start updating an image with the new image waveform, reading order, and dimensions
    image_width : int
        The new width of the the image
    needs_redraw : bool
        True if the image needs to be redrawn; False if not
    reading_order : ReadingOrder
        Whether the image data can be read in Fortran or C order
    normalize_data : bool
        True if the colors are relative to data maximum and minimum; False if not\
    """
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
            assert any(i in caplog.text for i in ("ImageView RedrawImage Thread Launched",
                                                  "ImageView Update Display with new image"))
        else:
            assert "Image processing has taken longer than the refresh rate" in caplog.text
    else:
        assert "ImageUpdateThread - needs redraw is False. Aborting." in caplog.text


def test_properties_and_setters(qtbot):
    """
    Test the widget's basic properties and setters.

    Expectations:
    The properties will provide their up-to-date values, and the setters will set up the new values appropriately.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing

    """
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
    """
    Test the widget's handling of the keyPress event.

    Expectations:
    The keyPress event will trigger a log record of the same event.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    caplog : fixture
        To capture the keyPress log event
    """
    pydm_image_view = PyDMImageView()
    qtbot.addWidget(pydm_image_view)

    caplog.set_level(logging.DEBUG)

    key_event = QKeyEvent(QEvent.KeyPress, Qt.Key_A, Qt.NoModifier)
    pydm_image_view.keyPressEvent(key_event)
    assert "Key event '{0}' received.".format(key_event) in caplog.text


def test_channels(qtbot):
    """
    To test the channel list provided by the widgets.

    Expectations:
    If the widget does not have a list of channels, it will return a list of preset channels.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
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








