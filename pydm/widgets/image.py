from ..PyQt.QtGui import QActionGroup
from ..PyQt.QtCore import pyqtSlot, pyqtProperty, Q_ENUMS, QTimer
from pyqtgraph import ImageView, ColorMap
import numpy as np
from .channel import PyDMChannel
from .colormaps import cmaps
from .base import PyDMWidget
from collections import OrderedDict
import pyqtgraph
pyqtgraph.setConfigOption('imageAxisOrder', 'row-major')

READINGORDER = OrderedDict([
                            ('Fortranlike', 0),
                            ('Clike', 1),
                            ])
COLORMAP = OrderedDict()
for i, cm in enumerate(sorted(cmaps.keys())):
    COLORMAP[cm] = i


class _ReadingOrderMap(object):
    for k in sorted(READINGORDER.keys()):
        locals()[k] = READINGORDER[k]


class _ColormapMap(object):
    for k in sorted(COLORMAP.keys()):
        locals()[k] = COLORMAP[k]


class PyDMImageView(ImageView, PyDMWidget, _ColormapMap, _ReadingOrderMap):
    """
    A PyQtGraph ImageView with support for Channels and more from PyDM.

    If there is no :attr:`channelWidth` it is possible to define the width of
    the image with the :attr:`width` property.

    The :attr:`normalizeData` property defines if the colors of the images are
    relative to the :attr:`colorMapMin` and :attr:`colorMapMax` property or to
    the minimum and maximum values of the image.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    image_channel : str, optional
        The channel to be used by the widget for the image data.
    width_channel : str, optional
        The channel to be used by the widget to receive the image width
        information
    """

    Q_ENUMS(_ReadingOrderMap)
    Q_ENUMS(_ColormapMap)

    readingorderdict = {}
    for rd, i in READINGORDER.items():
        readingorderdict[i] = rd

    colormapdict = {}
    for cm, i in COLORMAP.items():
        colormapdict[i] = cmaps[cm]

    def __init__(self, parent=None, image_channel=None, width_channel=None):
        """Initialize the object."""
        ImageView.__init__(self, parent)
        PyDMWidget.__init__(self)
        self._imagechannel = image_channel
        self._widthchannel = width_channel
        self.image_waveform = np.zeros(0)
        self._image_width = 0
        self._normalize_data = False

        # Hide some itens of the widget
        self.ui.histogram.hide()
        self.getImageItem().sigImageChanged.disconnect(
                                        self.ui.histogram.imageChanged)
        del self.ui.histogram
        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide()

        # Set color map limits
        self.cm_min = 0.0
        self.cm_max = 255.0
        self.data_max_int = None

        # Reading order of numpy array data
        self._readingOrder = 0

        self._colormapindex = COLORMAP["inferno"]
        self._cm_colors = self.colormapdict[self._colormapindex]
        self.setColorMap()

        # Menu to change Color Map
        cm_menu = self.getView().getMenu(None).addMenu("Color Map")
        cm_group = QActionGroup(self)
        for map_name in COLORMAP.keys():
            action = cm_group.addAction(map_name)
            action.setCheckable(True)
            action.index = COLORMAP[map_name]
            cm_menu.addAction(action)
            if action.index == self._colormapindex:
                action.setChecked(True)
        cm_menu.triggered.connect(self._changeColorMap)

        self.needs_redraw = False
        self.redraw_timer = QTimer(self)
        self.redraw_timer.timeout.connect(self.redrawImage)
        self._redraw_rate = 30
        self.maxRedrawRate = self._redraw_rate

    def _changeColorMap(self, action):
        """
        Change the colormap via action from ContextMenu.

        Method invoked by the colormap Action Menu that changes the
        current colormap used to render the image.

        Parameters
        ----------
        action : QAction
        """
        self.colormap = action.index

    def setColorMap(self, cmap=None):
        """
        Update the image colormap.

        Parameters
        ----------
        cmap : ColorMap
        """
        if not cmap:
            if not self._cm_colors.any():
                return
            pos = np.linspace(0.0, 1.0, num=len(self._cm_colors))
            cmap = ColorMap(pos, self._cm_colors)
        self.getView().setBackgroundColor(cmap.map(0))
        lut = cmap.getLookupTable(0.0, 1.0, alpha=False)
        self.getImageItem().setLookupTable(lut)
        self.getImageItem().setLevels([0.0, 1.0])

    @pyqtSlot(bool)
    def image_connection_state_changed(self, conn):
        if conn:
            self.redraw_timer.start()
        else:
            self.redraw_timer.stop()

    @pyqtSlot(np.ndarray)
    def image_value_changed(self, new_image):
        """
        Callback invoked when the Image Channel value is changed.

        Reshape and display the new image.

        Parameters
        ----------
        new_image : np.ndarray
            The new image data.  This can be a flat 1D array, or a 2D array.
        """
        if new_image is None:
            return
        self.image_waveform = new_image
        self.needs_redraw = True
        if self.data_max_int is None:
            self.data_max_int = np.iinfo(self.image_waveform.dtype).max

    def _reshapeImage(self, image):
        """Reshape the image according to the imageWidth and readingOrder."""
        return image.reshape(
                        (self.imageWidth, -1),
                        order=self.readingorderdict[self._readingOrder]
                        )

    @pyqtSlot(int)
    def image_width_changed(self, new_width):
        """
        Callback invoked when the Image Width Channel value is changed.

        Reshape the image data and triggers a ```redrawImage```

        Parameters
        ----------
        new_width : int
            The new image width
        """
        if new_width is None:
            return
        self.imageWidth = new_width

    def redrawImage(self):
        """Set the image data into the ImageItem."""
        if not self.needs_redraw:
            return
        image_dimensions = len(self.image_waveform.shape)
        if image_dimensions == 1:
            if self.imageWidth < 1:
                # There is no width for this image yet, so we can't draw it.
                return
            img = self._reshapeImage(self.image_waveform)
        else:
            img = self.image_waveform

        if len(img) <= 0:
            return
        if self._normalize_data:
            mini = self.image_waveform.min()
            maxi = self.image_waveform.max()
        else:
            mini = self.cm_min
            maxi = min(self.cm_max, self.data_max_int)
        img -= mini
        img *= 1/(maxi-mini)
        self.getImageItem().setImage(
                                    img,
                                    autoLevels=False,
                                    autoDownsample=True,
                                    autoHistogramRange=False)
        self.needs_redraw = False

    def setColorMapLimits(self, mn, mx):
        """Set the limit values for the colormap.

        Parameters
        ----------
        mn : int
            The lower limit
        mx : int
            The upper limit
        """
        if mn >= mx:
            return
        self.cm_max = float(mx)
        self.cm_min = float(mn)
        self.setColorMap()

    def keyPressEvent(self, ev):
        """Handle keypress events."""
        return

    @pyqtProperty(int)
    def maxRedrawRate(self):
        """
        The maximum rate (in Hz) at which the plot will be redrawn.
        The plot will not be redrawn if there is not new data to draw.

        Returns
        -------
        int
        """
        return self._redraw_rate

    @maxRedrawRate.setter
    def maxRedrawRate(self, redraw_rate):
        """
        The maximum rate (in Hz) at which the plot will be redrawn.
        The plot will not be redrawn if there is not new data to draw.

        Parameters
        -------
        redraw_rate : int
        """
        self._redraw_rate = float(redraw_rate)
        self.redraw_timer.setInterval(int((1.0/self._redraw_rate)*1000))

    @pyqtProperty(int)
    def imageWidth(self):
        """Return the width of the image.

        Returns
        ----------
        int
        """
        return self._image_width

    @imageWidth.setter
    def imageWidth(self, new_width):
        """Set the width of the image.

        Can be overridden by :attr:`widthChannel`.

        Parameters
        ----------
        new_width: int
        """
        if self._image_width != int(new_width) and self._widthchannel is None:
            self._image_width = int(new_width)

    @pyqtProperty(str)
    def widthChannel(self):
        """
        The channel address in use for the image width .

        Returns
        -------
        str
            Channel address
        """
        return str(self._widthchannel)

    @widthChannel.setter
    def widthChannel(self, value):
        """
        The channel address in use for the image width .

        Parameters
        ----------
        value : str
            Channel address
        """
        if self._widthchannel != value:
            self._widthchannel = str(value)

    @pyqtProperty(_ColormapMap)
    def colormap(self):
        """Return the index of the colormap to be used.

        Returns
        ----------
        int
        """
        return self._colormapindex

    @colormap.setter
    def colormap(self, new_colormapindex):
        """Set the index of the colormap to be used.

        Parameters
        ----------
        new_colormapindex: int
        """
        if self._colormapindex != new_colormapindex:
            self._colormapindex = new_colormapindex
            self._cm_colors = self.colormapdict[self._colormapindex]
            self.setColorMap()

    @pyqtProperty(bool)
    def normalizeData(self):
        """Return True if the colors are relative to data maximum and minimum.

        Returns
        ----------
        bool
        """
        return self._normalize_data

    @normalizeData.setter
    @pyqtSlot(bool)
    def normalizeData(self, new_norm):
        """Define if the colors are relative to maximum and minimum of data.

        Parameters
        ----------
        new_norm: bool
        """
        if self._normalize_data == new_norm:
            return
        self._normalize_data = new_norm
        self.redrawImage()

    @pyqtProperty(int)
    def colorMapMin(self):
        """Minimum value to be considered for color scale definition.

        Returns
        -------
        float
            minimum value of the color scale.
        """
        return self.cm_min

    @colorMapMin.setter
    @pyqtSlot(int)
    def colorMapMin(self, new_min):
        """Set the minimum value to be considered for color scale definition.

        Parameters
        -------
        new_min: float
        """
        if self.cm_min == new_min or new_min > self.cm_max:
            return
        self.cm_min = float(new_min)
        self.setColorMap()

    @pyqtProperty(int)
    def colorMapMax(self):
        """Maximum value to be considered for color scale definition.

        Returns
        -------
        float
            maximum value of the color scale.
        """
        return self.cm_max

    @colorMapMax.setter
    @pyqtSlot(int)
    def colorMapMax(self, new_max):
        """Set the maximum value to be considered for color scale definition.

        Parameters
        -------
        new_max: float
        """
        if self.cm_max == new_max or new_max < self.cm_min:
            return
        self.cm_max = float(new_max)
        self.setColorMap()

    @pyqtProperty(_ReadingOrderMap)
    def readingOrder(self):
        """Reading order of the :attr:`imageChannel` array.

        Returns
        -------
        int
            0 if the reading order is Fortranlike or 1 if it is Clike.
        """
        return self._readingOrder

    @readingOrder.setter
    def readingOrder(self, new_order):
        """Set reading order of the :attr:`imageChannel` array.

        Parameters
        ----------
        new_order: int
            0 if the reading order is Fortranlike or 1 if it is Clike.
        """
        if self._readingOrder != new_order:
            self._readingOrder = int(new_order)

    @pyqtProperty(str)
    def imageChannel(self):
        """
        The channel address in use for the image data .

        Returns
        -------
        str
            Channel address
        """
        return str(self._imagechannel)

    @imageChannel.setter
    def imageChannel(self, value):
        """
        The channel address in use for the image data .

        Parameters
        ----------
        value : str
            Channel address
        """
        if self._imagechannel != value:
            self._imagechannel = str(value)

    @pyqtProperty(str)
    def widthChannel(self):
        """
        The channel address in use for the image width .

        Returns
        -------
        str
            Channel address
        """
        return str(self._widthchannel)

    @widthChannel.setter
    def widthChannel(self, value):
        """
        The channel address in use for the image width .

        Parameters
        ----------
        value : str
            Channel address
        """
        if self._widthchannel != value:
            self._widthchannel = str(value)

    def channels(self):
        """
        Returns the channels being used for this Widget.

        Returns
        -------
        channels : list
            List of PyDMChannel objects
        """
        return [
            PyDMChannel(address=self.imageChannel,
                        connection_slot=self.connectionStateChanged,
                        value_slot=self.image_value_changed,
                        severity_slot=self.alarmSeverityChanged),
            PyDMChannel(address=self.widthChannel,
                        connection_slot=self.connectionStateChanged,
                        value_slot=self.image_width_changed,
                        severity_slot=self.alarmSeverityChanged)]
