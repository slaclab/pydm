from ..PyQt.QtGui import QApplication, QWidget, QPainter, QPixmap, QStyle, QStyleOption
from ..PyQt.QtCore import pyqtSlot, pyqtProperty, Qt, QFile, QSize, QSizeF, QRect, QRectF, qInstallMessageHandler
from ..PyQt.QtSvg import QSvgRenderer
from .channel import PyDMChannel
import json
import os.path

class PyDMSymbol(QWidget):
  def __init__(self, parent=None, init_channel=None):
    super(PyDMSymbol, self).__init__(parent)
    self.app = QApplication.instance()
    self._state_images = {} #Keyed on state values (ints), values are (filename, qpixmap or qsvgrenderer) tuples.
    self._channel = init_channel
    self._channels = None
    self._connected = False
    self._value = None
    self._aspect_ratio_mode = Qt.KeepAspectRatio
    self._sizeHint = self.minimumSizeHint()
    self._painter = QPainter()
  
  def init_for_designer(self):
    self._value = 0
  
  @pyqtProperty(str, doc=
  """
  JSON-formatted dictionary keyed on states (integers), with filenames of the image file to display for the state.
  """
  )
  def imageFiles(self):
    return json.dumps({str(state): val[0] for (state, val) in self._state_images.items()})

  @imageFiles.setter
  def imageFiles(self, new_files):
    new_file_dict = json.loads(str(new_files))
    self._sizeHint = QSize(0,0)
    for (state, filename) in new_file_dict.items():
      try:
        file_path = self.app.get_path(filename)
      except Exception as e:
        print(e)
        file_path = filename
      #First, lets try SVG.  We have to try SVG first, otherwise
      #QPixmap will happily load the SVG and turn it into a raster image.
      #Really annoying: We have to try to load the file as SVG,
      #and we expect it will fail often (because many images arent SVG).
      #Qt prints a warning message to stdout any time SVG loading fails.
      #So we have to temporarily silence Qt warning messages here.
      qInstallMessageHandler(self.qt_message_handler)
      svg = QSvgRenderer()
      svg.repaintNeeded.connect(self.update)
      if svg.load(file_path):
        self._state_images[int(state)] = (filename, svg)
        self._sizeHint = self._sizeHint.expandedTo(svg.defaultSize())
        qInstallMessageHandler(None)
        continue
      qInstallMessageHandler(None)
      #SVG didn't work, lets try QPixmap
      image = QPixmap(file_path)
      if not image.isNull():
        self._state_images[int(state)] = (filename, image)
        self._sizeHint = self._sizeHint.expandedTo(image.size())
        continue
      #If we get this far, the file specified could not be loaded at all.
      print("Could not load image: {}".format(filename))
      self._state_images[int(state)] = (filename, None)
  
  @pyqtProperty(Qt.AspectRatioMode, doc=
  """
  Which aspect ratio mode to use
  """
  )
  def aspectRatioMode(self):
    return self._aspect_ratio_mode

  @aspectRatioMode.setter
  def aspectRatioMode(self, new_mode):
    if new_mode != self._aspect_ratio_mode:
      self._aspect_ratio_mode = new_mode
      self.update()
  
  @pyqtProperty(str, doc=
  """
  The channel to be used 
  """
  )
  def channel(self):
    if self._channel is None:
      return ""
    return str(self._channel)

  @channel.setter
  def channel(self, value):
    if self._channel != value:
      self._channel = str(value)

  def channels(self):
    if self._channels is not None:
      return self._channels
    self._channels = [PyDMChannel(address=self._channel, connection_slot=self.connectionStateChanged, value_slot=self.receiveValue)]
    return self._channels

  #false = disconnected, true = connected
  @pyqtSlot(bool)
  def connectionStateChanged(self, connected):
    self._connected = connected
    self.update()
  
  @pyqtSlot(int)
  def receiveValue(self, new_value):
    self._value = new_value
    self.update()
  
  def sizeHint(self):
    return self._sizeHint
  
  def minimumSizeHint(self):
    return QSize(10,10) #This is totally arbitrary, I just want *some* visible nonzero size
  
  def paintEvent(self, event):
    self._painter.begin(self)
    opt = QStyleOption()
    opt.initFrom(self)
    self.style().drawPrimitive(QStyle.PE_Widget, opt, self._painter, self)
    #self._painter.setRenderHint(QPainter.Antialiasing)
    image_to_draw = self._state_images.get(self._value, (None, None))[1]
    if image_to_draw is None:
      self._painter.end()
      return
    if isinstance(image_to_draw, QPixmap):
      w = float(image_to_draw.width())
      h = float(image_to_draw.height())
      if self._aspect_ratio_mode == Qt.IgnoreAspectRatio:
        scale = (event.rect().width()/w, event.rect().height()/h)
      elif self._aspect_ratio_mode == Qt.KeepAspectRatio:
        sf = min(event.rect().width()/w, event.rect().height()/h)
        scale = (sf, sf)
      elif self._aspect_ratio_mode == Qt.KeepAspectRatioByExpanding:
        sf = max(event.rect().width()/w, event.rect().height()/h)
        scale = (sf, sf)
      self._painter.scale(scale[0], scale[1])
      self._painter.drawPixmap(event.rect().x(), event.rect().y(), image_to_draw)
    elif isinstance(image_to_draw, QSvgRenderer):
      draw_size = QSizeF(image_to_draw.defaultSize())
      draw_size.scale(QSizeF(event.rect().size()), self._aspect_ratio_mode)
      image_to_draw.render(self._painter, QRectF(0.0,0.0,draw_size.width(),draw_size.height()))
    self._painter.end()
  
  def qt_message_handler(self, msg_type, *args):
    #Intentionally supress all qt messages.  Make sure not to leave this handler installed.
    pass