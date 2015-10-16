from PyQt4.QtGui import QLabel, QApplication, QColor, QActionGroup
from PyQt4.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QString
from pyqtgraph import ImageView
from pyqtgraph import ImageItem
from pyqtgraph import ColorMap
import numpy as np
from channel import PyDMChannel

color_maps = {}
color_maps["Jet"] = np.array([[0,0,127,255],[0,0,255,255],[0,127,255,255],[0,255,255,255],[127,255,127,255],[255,255,0,255],[255,127,0,255],[255,0,0,255], [127,0,0,255]], dtype=np.ubyte)
color_maps["Monochrome"] = np.array([[0,0,0,255],[255,255,255,255]], dtype=np.ubyte)
color_maps["Hot"] = np.array([[0,0,0,255],[255,0,0,255],[255,127,0,255],[255,255,0,255],[255,255,255,255]], dtype=np.ubyte)
class PyDMImageView(ImageView):
  def __init__(self, image_channel=None, width_channel=None, parent=None):
    super(PyDMImageView, self).__init__(parent)
    self._imagechannel = image_channel
    self._widthchannel = width_channel
    self.image_waveform = None
    self.image_width = None
    self.ui.histogram.hide()
    self.ui.roiBtn.hide()
    self.ui.menuBtn.hide()
    self.cm_min = 0.0
    self.cm_max = 255.0
    self.data_max_int = 255 #This is the max value for the image waveform's data type.  It gets set when the waveform updates.
    self._colormapname = "Jet"
    self._cm_colors = None
    self.setColorMapToPreset(self._colormapname)
    cm_menu = self.getView().getMenu(None).addMenu("Color Map")
    cm_group = QActionGroup(self)
    for map_name in color_maps:
      action = cm_group.addAction(map_name)
      action.setCheckable(True)
      cm_menu.addAction(action)
      if map_name == self._colormapname:
        action.setChecked(True)
    cm_menu.triggered.connect(self.changeColorMap)

  def changeColorMap(self, action):
    self._colormapname = str(action.text())
    self.setColorMapToPreset(self._colormapname)

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

  def setColorMapToPreset(self, name):
    self._cm_colors = color_maps[name]
    self.setColorMap()

  def setColorMap(self, map=None):
    if not map:
      if not self._cm_colors.any():
        return
      pos = np.linspace(self.cm_min/float(self.data_max_int), self.cm_max/float(self.data_max_int), num=len(self._cm_colors))
      map = ColorMap(pos, self._cm_colors)
    self.getView().setBackgroundColor(map.map(0))
    self.ui.histogram.gradient.setColorMap(map)

  @pyqtSlot(np.ndarray)
  def receiveImageWaveform(self, new_waveform):
    self.image_waveform = new_waveform
    self.data_max_int = np.iinfo(self.image_waveform.dtype).max
    self.redrawImage()
  
  @pyqtSlot(int)
  def receiveImageWidth(self, new_width):
    self.image_width = new_width
    self.redrawImage()
  
  def redrawImage(self):
    if self.image_waveform.any() and self.image_width:
      self.getImageItem().setImage(self.image_waveform.reshape((-1, int(self.image_width))))
  
  # -2 to +2, -2 is LOLO, -1 is LOW, 0 is OK, etc.  
  @pyqtSlot(int)
  def alarmStatusChanged(self, new_alarm_state):
    pass
  
  #0 = NO_ALARM, 1 = MINOR, 2 = MAJOR, 3 = INVALID  
  @pyqtSlot(int)
  def alarmSeverityChanged(self, new_alarm_severity):
    pass
    
  #false = disconnected, true = connected
  @pyqtSlot(bool)
  def connectionStateChanged(self, connected):
    pass

  def getImageChannel(self):
    return QString.fromAscii(self._imagechannel)
  
  def setImageChannel(self, value):
    if self._imagechannel != value:
      self._imagechannel = str(value)

  def resetImageChannel(self):
    if self._imagechannel != None:
      self._imagechannel = None
    
  imageChannel = pyqtProperty("QString", getImageChannel, setImageChannel, resetImageChannel)
  
  def getWidthChannel(self):
    return QString.fromAscii(self._widthchannel)
  
  def setWidthChannel(self, value):
    if self._widthchannel != value:
      self._widthchannel = str(value)

  def resetWidthChannel(self):
    if self._widthchannel != None:
      self._widthchannel = None
    
  widthChannel = pyqtProperty("QString", getWidthChannel, setWidthChannel, resetWidthChannel)
  
  def channels(self):
    return [PyDMChannel(address=self.imageChannel, connection_slot=self.connectionStateChanged, waveform_slot=self.receiveImageWaveform, severity_slot=self.alarmSeverityChanged),
            PyDMChannel(address=self.widthChannel, connection_slot=self.connectionStateChanged, value_slot=self.receiveImageWidth, severity_slot=self.alarmSeverityChanged)]
