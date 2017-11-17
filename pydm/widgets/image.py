from ..PyQt.QtGui import QActionGroup
from ..PyQt.QtCore import pyqtSlot, pyqtProperty, QTimer
from pyqtgraph import ImageView
from pyqtgraph import ColorMap
import numpy as np
from .channel import PyDMChannel
from .colormaps import cmaps
from .base import PyDMWidget
import pyqtgraph
pyqtgraph.setConfigOption('imageAxisOrder', 'row-major')

class PyDMImageView(ImageView, PyDMWidget):
    """
    A PyQtGraph ImageView with support for Channels and more from PyDM

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

    color_maps = cmaps
    def __init__(self, parent=None, image_channel=None, width_channel=None):
        ImageView.__init__(self, parent)
        PyDMWidget.__init__(self)
        self.axes = dict({'t': None, "x": 0, "y": 1, "c": None})
        self._imagechannel = image_channel
        self._widthchannel = width_channel
        self.image_waveform = np.zeros(0)
        self.image_width = 0
        self.ui.histogram.hide()
        self.getImageItem().sigImageChanged.disconnect(self.ui.histogram.imageChanged)
        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide()
        self.cm_min = 0.0
        self.cm_max = 255.0
        self.data_max_int = None  # This is the max value for the image waveform's data type.  It gets set when the waveform updates.
        self._colormapname = "inferno"
        self._cm_colors = None
        self.setColorMapToPreset(self._colormapname)
        cm_menu = self.getView().getMenu(None).addMenu("Color Map")
        cm_group = QActionGroup(self)
        for map_name in self.color_maps:
            action = cm_group.addAction(map_name)
            action.setCheckable(True)
            cm_menu.addAction(action)
            if map_name == self._colormapname:
                action.setChecked(True)
        cm_menu.triggered.connect(self.changeColorMap)
        self.needs_redraw = False
        self.redraw_timer = QTimer(self)
        self.redraw_timer.timeout.connect(self.redrawImage)
        self._redraw_rate = 30
        self.maxRedrawRate = self._redraw_rate
        
    def changeColorMap(self, action):
        """
        Method invoked by the colormap Action Menu that changes the
        current colormap used to render the image.

        Parameters
        ----------
        action : QAction
        """
        self.setColorMapToPreset(str(action.text()))

    @pyqtSlot(int)
    def setColorMapMin(self, new_min):
        """
        Set the minimal value for the colormap

        Parameters
        ----------
        new_min : int
        """
        if self.cm_min != new_min:
            self.cm_min = new_min
            if self.cm_min > self.cm_max:
                self.cm_max = self.cm_min
            self.setColorMap()

    @pyqtSlot(int)
    def setColorMapMax(self, new_max):
        """
        Set the maximum value for the colormap

        Parameters
        ----------
        new_max : int
        """
        if self.cm_max != new_max:
            if new_max >= self.data_max_int:
                new_max = self.data_max_int
            self.cm_max = new_max
            if self.cm_max < self.cm_min:
                self.cm_min = self.cm_max
            self.setColorMap()

    def setColorMapLimits(self, mn, mx):
        """
        Set the limit values for the colormap

        Parameters
        ----------
        mn : int
            The lower limit
        mx : int
            The upper limit
        """
        self.cm_max = mx
        self.cm_min = mn
        self.setColorMap()

    def setColorMapToPreset(self, name):
        """
        Load a predefined colormap

        Parameters
        ----------
        name : str
        """
        self._colormapname = str(name)
        self._cm_colors = self.color_maps[str(name)]
        self.setColorMap()

    def setColorMap(self, cmap=None):
        """
        Update the image colormap

        Parameters
        ----------
        cmap : ColorMap
        """
        if self.data_max_int is None:
            return
        if not cmap:
            if not self._cm_colors.any():
                return
            pos = np.linspace(0.0, 1.0, num=len(self._cm_colors))  # take default values
            cmap = ColorMap(pos, self._cm_colors)
        self.getView().setBackgroundColor(cmap.map(0))
        lut = cmap.getLookupTable(0.0, 1.0, self.data_max_int, alpha=False)
        self.getImageItem().setLookupTable(lut)
        self.getImageItem().setLevels([self.cm_min, float(min(self.cm_max, self.data_max_int))])  # set levels from min to max of image (may improve min here)

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
            self.setColorMap() #Now that we know the max size, set the color map appropriately.

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
        self.image_width = int(new_width)

    def redrawImage(self):
        """
        Set the image data into the ImageItem
        """
        if not self.needs_redraw:
            return
        image_dimensions = len(self.image_waveform.shape)
        if image_dimensions == 1:
            if self.image_width < 1:
                #We don't have a width for this image yet, so we can't draw it.
                return
            img = self.image_waveform.reshape(self.image_width, -1, order='F')
        else:
            img = self.image_waveform
        if len(img) > 0:
            self.getImageItem().setImage(img, autoLevels=False, autoDownsample=True)
            self.needs_redraw = False

    def keyPressEvent(self, ev):
        return

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
                        connection_slot=self.image_connection_state_changed,
                        value_slot=self.image_value_changed,
                        severity_slot=self.alarmSeverityChanged),
            PyDMChannel(address=self.widthChannel,
                        connection_slot=self.connectionStateChanged,
                        value_slot=self.image_width_changed,
                        severity_slot=self.alarmSeverityChanged)]

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
        self._redraw_rate = redraw_rate
        self.redraw_timer.setInterval(int((1.0/self._redraw_rate)*1000))