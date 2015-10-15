from PyQt4.QtGui import QLabel, QApplication, QColor
from PyQt4.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QString
from pyqtgraph import ImageView
from pyqtgraph import ImageItem
from pyqtgraph import ColorMap
import numpy as np
from channel import PyDMChannel

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
    pos = np.array([0.0, 1.0/8.0, 2.0/8.0, 3.0/8.0, 4.0/8.0, 5.0/8.0, 6.0/8.0, 7.0/8.0, 1.0])
    color = np.array([[0,0,127,255],[0,0,255,255],[0,127,255,255],[0,255,255,255],[127,255,127,255],[255,255,0,255],[255,127,0,255],[255,0,0,255], [127,0,0,255]], dtype=np.ubyte)
    map = ColorMap(pos, color)
    #self.lut = map.getLookupTable(0.0,1.0,256)
    self.ui.histogram.gradient.setColorMap(map)
    self.getView().setBackgroundColor(map.map(0))

  @pyqtSlot(np.ndarray)
  def receiveImageWaveform(self, new_waveform):
    self.image_waveform = new_waveform
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
