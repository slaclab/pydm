from ..PyQt.QtGui import QActionGroup
from ..PyQt.QtCore import pyqtSlot, pyqtProperty
from pyqtgraph import ImageView
from pyqtgraph import ColorMap
import numpy as np
from .channel import PyDMChannel
from .colormaps import cmaps
from .base import PyDMWidget

class PyDMImageView(ImageView, PyDMWidget):
    color_maps = cmaps
    def __init__(self, parent=None, image_channel=None, width_channel=None):
        super(PyDMImageView, self).__init__(parent)
        self.axes = dict({'t': None, "x": 0, "y": 1, "c": None})
        self._imagechannel = image_channel
        self._widthchannel = width_channel
        self.image_waveform = np.zeros(0)
        self.image_width = 0
        self.ui.histogram.hide()
        del self.ui.histogram
        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide()
        self.cm_min = 0.0
        self.cm_max = 255.0
        self.data_max_int = 255  # This is the max value for the image waveform's data type.  It gets set when the waveform updates.
        self._colormapname = "inferno"
        self._cm_colors = None
        self._needs_reshape = False
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

    def changeColorMap(self, action):
        self.setColorMapToPreset(str(action.text()))

    @pyqtSlot(int)
    def setColorMapMin(self, new_min):
        if self.cm_min != new_min:
            self.cm_min = new_min
            if self.cm_min > self.cm_max:
                self.cm_max = self.cm_min
            self.setColorMap()

    @pyqtSlot(int)
    def setColorMapMax(self, new_max):
        if self.cm_max != new_max:
            if new_max >= self.data_max_int:
                new_max = self.data_max_int
            self.cm_max = new_max
            if self.cm_max < self.cm_min:
                self.cm_min = self.cm_max
            self.setColorMap()

    def setColorMapLimits(self, mn, mx):
        self.cm_max = mx
        self.cm_min = mn
        self.setColorMap()

    def setColorMapToPreset(self, name):
        self._colormapname = str(name)
        self._cm_colors = self.color_maps[str(name)]
        self.setColorMap()

    def setColorMap(self, cmap=None):
        if not cmap:
            if not self._cm_colors.any():
                return
            pos = np.linspace(0.0, 1.0, num=len(self._cm_colors))  # take default values
            cmap = ColorMap(pos, self._cm_colors)
        self.getView().setBackgroundColor(cmap.map(0))
        lut = cmap.getLookupTable(0.0, 1.0, self.data_max_int, alpha=False)
        self.getImageItem().setLookupTable(lut)
        self.getImageItem().setLevels([self.cm_min, float(self.data_max_int)])  # set levels from min to max of image (may improve min here)

    def image_value_changed(self, new_image):
        if new_image is None:
            return
        if self.image_width == 0:
            self.image_waveform = new_image
            self._needs_reshape = True
            # We'll wait to draw the image until we get the width.
            return
        if len(new_image.shape) == 1:
            self.image_waveform = new_image.reshape((int(self.image_width), -1), order='F')
        elif len(new_image.shape) == 2:
            self.image_waveform = new_image
        self.data_max_int = np.amax(self.image_waveform)  # take the max value of the recieved image
        self.setColorMap()  # to update the colormap immediately
        self.redrawImage()

    def image_width_changed(self, new_width):
        if new_width is None:
            return
        self.image_width = int(new_width)
        if self._needs_reshape:
            self.image_waveform = self.image_waveform.reshape((int(self.image_width), -1), order='F')
            self._needs_reshape = False
        self.redrawImage()

    def redrawImage(self):
        if len(self.image_waveform) > 0 and self.image_width > 0:
            self.setImage(self.image_waveform, autoLevels=False,
                          autoHistogramRange=False, xvals=[0, 1])

    @pyqtProperty(str)
    def imageChannel(self):
        return str(self._imagechannel)

    @imageChannel.setter
    def imageChannel(self, value):
        if self._imagechannel != value:
            self._imagechannel = str(value)

    @pyqtProperty(str)
    def widthChannel(self):
        return str(self._widthchannel)

    @widthChannel.setter
    def widthChannel(self, value):
        if self._widthchannel != value:
            self._widthchannel = str(value)

    def channels(self):
        return [
            PyDMChannel(address=self.imageChannel,
                        connection_slot=self.connectionStateChanged,
                        waveform_slot=self.image_value_changed,
                        severity_slot=self.alarmSeverityChanged),
            PyDMChannel(address=self.widthChannel,
                        connection_slot=self.connectionStateChanged,
                        value_slot=self.image_width_changed,
                        severity_slot=self.alarmSeverityChanged)]
