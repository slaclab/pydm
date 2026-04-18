import numpy as np
import pytest

from pydm.widgets.image import ImageUpdateThread, DimensionOrder, ReadingOrder


class FakeImageView:
    """Lightweight stand-in for PyDMImageView that provides only the
    attributes read by ``ImageUpdateThread``.  Avoids instantiating the
    real widget which triggers segfaults when run alongside other tests.
    """

    def __init__(self):
        self.image_waveform = np.zeros(0)
        self.imageWidth = 4
        self.readingOrder = ReadingOrder.Fortranlike
        self.needs_redraw = True
        self.cm_min = 0.0
        self.cm_max = 255.0
        self._normalize_data = False
        self._dimension_order = DimensionOrder.HeightFirst

    def process_image(self, img):
        """Return the image unmodified.

        Parameters
        ----------
        img : np.ndarray
            The image array.

        Returns
        -------
        np.ndarray
        """
        return img


def test_rgb_image_ignores_colormap_levels():
    """RGB images should derive display levels from their own data range,
    not from the mono colormap min/max settings.
    """
    view = FakeImageView()
    view.cm_min = 0.0
    view.cm_max = 4095.0
    view._normalize_data = False

    rgb_img = np.random.randint(0, 256, (4, 4, 3), dtype=np.uint8)
    view.image_waveform = rgb_img

    thread = ImageUpdateThread(view)
    emitted = []
    thread.updateSignal.connect(lambda data: emitted.append(data))
    thread.run()

    assert len(emitted) == 1
    mini, maxi, _ = emitted[0]
    assert mini == rgb_img.min()
    assert maxi == rgb_img.max()


def test_mono_image_uses_colormap_levels():
    """Mono images should respect colormap min/max when normalize is off."""
    view = FakeImageView()
    view.cm_min = 0.0
    view.cm_max = 4095.0
    view._normalize_data = False

    mono_img = np.random.randint(0, 4096, (4, 4), dtype=np.uint16)
    view.image_waveform = mono_img

    thread = ImageUpdateThread(view)
    emitted = []
    thread.updateSignal.connect(lambda data: emitted.append(data))
    thread.run()

    assert len(emitted) == 1
    mini, maxi, _ = emitted[0]
    assert mini == 0.0
    assert maxi == 4095.0
