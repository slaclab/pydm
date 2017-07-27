from ..PyQt.QtGui import QWidget, QTabWidget, QColor, QPen, QGridLayout, QLabel, QPalette, QFontMetrics, QPainter, QBrush, QStyleOption, QStyle
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, Qt, QStringList, QSize, QPoint
from .channel import PyDMChannel
import numpy as np

class PyDMBitIndicator(QWidget):
  def __init__(self, parent=None):
    super(PyDMBitIndicator, self).__init__(parent)
    self.setAutoFillBackground(True)
    self.circle = False
    self._painter = QPainter()
    self._brush = QBrush(Qt.SolidPattern)
    self._pen = QPen(Qt.SolidLine)
    
  def paintEvent(self, event):
    self._painter.begin(self)
    opt = QStyleOption()
    opt.initFrom(self)
    self.style().drawPrimitive(QStyle.PE_Widget, opt, self._painter, self)
    self._painter.setRenderHint(QPainter.Antialiasing)
    self._painter.setBrush(self._brush)
    self._painter.setPen(self._pen)
    if self.circle:
      rect = event.rect()
      w = rect.width()
      h = rect.height()
      r = min(w, h)/2.0 - 2.0*max(self._pen.widthF(), 1.0)
      self._painter.drawEllipse(QPoint(w/2.0, h/2.0), r, r)
    else:
      self._painter.drawRect(event.rect())
    self._painter.end()
  
  def setColor(self, color):
    self._brush.setColor(color)
    self.update()
  
  def minimumSizeHint(self):
    fm = QFontMetrics(self.font())
    return QSize(fm.height(), fm.height())

class PyDMByteIndicator(QWidget):
  def __init__(self, parent=None, init_channel=None):
    super(PyDMByteIndicator, self).__init__(parent)
    self.setLayout(QGridLayout(self))
    self._connected = False
    self._on_color = QColor(0,255,0)
    self._off_color = QColor(100,100,100)
    self._disconnected_color = QColor(255,255,255)
    self._invalid_color = QColor(255,0,255)
    self._pen_style = Qt.SolidLine
    self._line_pen = QPen(self._pen_style)
    self._orientation = Qt.Vertical
    #This is kind of ridiculous, importing QTabWidget just to get a 4-item enum thats usable in Designer.
    #PyQt5 lets you define custom enums that you can use in designer with QtCore.Q_ENUMS(), doesnt exist in PyQt4.
    self._show_labels = True
    self._label_position = QTabWidget.East
    self._channel = ""
    self._channels = None
    self._num_bits = 1
    self._labels = []
    self._indicators = []
    self._value = 0
    self._circles = False
    self.set_spacing()
    self.layout().setOriginCorner(Qt.TopLeftCorner)
    self._big_endian = False
    self._shift = 0
    self.numBits = 1 #Need to set the property to initialize _labels and _indicators
    #setting numBits there also performs the first rebuild_layout.
  
  def init_for_designer(self):
    self._connected = True
    self._value = 5
    self.update_indicators()
  
  @pyqtSlot(bool)
  def connectionStateChanged(self, connected):
    self._connected = connected
    self.update_indicators()
  
  def rebuild_layout(self):
    self.clear()
    pairs = zip(self._labels, self._indicators)
    #Hide labels until they are in the layout
    for label in self._labels:
      label.setVisible(False)
    #This is a horrendous mess of if statements
    #for every possible case.  Ugh.
    #There is probably a more clever way to do this.
    if self.orientation == Qt.Vertical:
      for i, (label, indicator) in enumerate(pairs):
        if self.labelPosition == QTabWidget.East:
          self.layout().addWidget(indicator, i, 0)
          self.layout().addWidget(label, i, 1)
          label.setVisible(self._show_labels)
        elif self.labelPosition == QTabWidget.West:
          self.layout().addWidget(label, i, 0)
          self.layout().addWidget(indicator, i, 1)
          label.setVisible(self._show_labels)
        else:
          self.layout().addWidget(indicator, i, 0)
          #Invalid combo of orientation and label position, so we don't reset label visibility here.
    elif self.orientation == Qt.Horizontal:
      for i, (label, indicator) in enumerate(pairs):
        if self.labelPosition == QTabWidget.North:
          self.layout().addWidget(label, 0, i)
          self.layout().addWidget(indicator, 1, i)
          label.setVisible(self._show_labels)
        elif self.labelPosition == QTabWidget.South:
          self.layout().addWidget(indicator, 0, i)
          self.layout().addWidget(label, 1, i)
          label.setVisible(self._show_labels)
        else:
          self.layout().addWidget(indicator, 0, i)
          #Invalid combo of orientation and label position, so we don't reset label visibility here.
    self.update_indicators()
    
  def clear(self):
    for col in range(0, self.layout().columnCount()):
      for row in range(0, self.layout().rowCount()):
        item = self.layout().itemAtPosition(row, col)
        if item is not None:
          w = item.widget()
          if w is not None:
            self.layout().removeWidget(w)
  
  def update_indicators(self):
    bits = np.unpackbits(np.array(self._value, dtype=np.uint8))
    bits = np.roll(bits[::-1], -self._shift)
    for i in range(0,self._num_bits):
      w = self._indicators[i]
      if self._connected:
        if bits[i] == 1:
          c = self._on_color
        else:
          c = self._off_color
      else:
        c = self._disconnected_color
      w.setColor(c)
  
  @pyqtProperty(QColor, doc=
  """
  The color for a bit in the 'on' state.
  """
  )
  def onColor(self):
    return self._on_color
  
  @onColor.setter
  def onColor(self, new_color):
    if new_color != self._on_color:
      self._on_color = new_color
      self.update_indicators()
  
  @pyqtProperty(QColor, doc=
  """
  The color for a bit in the 'off' state.
  """
  )
  def offColor(self):
    return self._off_color
  
  @offColor.setter
  def offColor(self, new_color):
    if new_color != self._off_color:
      self._off_color = new_color
      self.update_indicators()
    
  @pyqtProperty(Qt.Orientation, doc=
  """
  Whether to lay out the bit indicators vertically or horizontally.
  """)
  def orientation(self):
    return self._orientation
  
  @orientation.setter
  def orientation(self, new_orientation):
    self._orientation = new_orientation
    self.set_spacing()
    self.rebuild_layout()
  
  def set_spacing(self):
    label_spacing = 5
    if self._circles:
      indicator_spacing = 5
    else:
      indicator_spacing = 0
    if self._orientation == Qt.Horizontal:
      self.layout().setHorizontalSpacing(indicator_spacing)
      self.layout().setVerticalSpacing(label_spacing)
    elif self._orientation == Qt.Vertical:
      self.layout().setHorizontalSpacing(label_spacing)
      self.layout().setVerticalSpacing(indicator_spacing)
  
  @pyqtProperty(bool, doc=
  """
  Whether or not to show labels next to each bit indicator.
  """)
  def showLabels(self):
    return self._show_labels
  
  @showLabels.setter
  def showLabels(self, show):
    self._show_labels = show
    for label in self._labels:
      label.setVisible(show)
  
  @pyqtProperty(bool, doc=
  """
  Whether the most significant bit is at the start or end of the widget.
  """)
  def bigEndian(self):
    return self._big_endian
  
  @bigEndian.setter
  def bigEndian(self, is_big_endian):
    self._big_endian = is_big_endian
    if self._big_endian:
      self.layout().setOriginCorner(Qt.BottomLeftCorner)
    else:
      self.layout().setOriginCorner(Qt.TopLeftCorner)
    self.rebuild_layout()
  
  @pyqtProperty(bool, doc=
  """
  Draw indicators as circles, rather than rectangles.
  """)
  def circles(self):
    return self._circles
  
  @circles.setter
  def circles(self, draw_circles):
    self._circles = draw_circles
    self.set_spacing()
    for indicator in self._indicators:
      indicator.circle = self._circles
    self.update_indicators()
  
  
  @pyqtProperty(QTabWidget.TabPosition, doc=
  """
  The side of the widget to display labels on.
  """)
  def labelPosition(self):
    return self._label_position
  
  @labelPosition.setter
  def labelPosition(self, new_pos):
    self._label_position = new_pos
    self.rebuild_layout()
  
  @pyqtProperty(int, doc=
  """
  Number of bits to interpret.
  """)
  def numBits(self):
    return self._num_bits
  
  @numBits.setter
  def numBits(self, new_num_bits):
    if new_num_bits < 1:
      return
    self._num_bits = new_num_bits
    for indicator in self._indicators:
      indicator.deleteLater()
    self._indicators = [PyDMBitIndicator() for i in range(0, self._num_bits)]
    old_labels = self.labels
    new_labels = ["Bit {}".format(i) for i in range(0, self._num_bits)]
    for i, old_label in enumerate(old_labels):
      if i >= self._num_bits:
        break
      new_labels[i] = old_label
    self.labels = new_labels
  
  @pyqtProperty(int, doc=
  """
  Bit shift.
  """)
  def shift(self):
    return self._shift
  
  @shift.setter
  def shift(self, new_shift):
    self._shift = new_shift
    self.update_indicators()
  
  @pyqtProperty(QStringList, doc=
  """
  Labels for each bit.
  """)
  def labels(self):
    return [str(l.text()) for l in self._labels]
  
  @labels.setter
  def labels(self, new_labels):
    for label in self._labels:
      label.deleteLater()
    self._labels = [QLabel(text) for text in new_labels]
    #Have to reset showLabels to hide or show all the new labels we just made.
    self.showLabels = self._show_labels
    self.rebuild_layout()
  
  @pyqtProperty(str, doc=
  """
  The channel to be used.  The channel must supply a type convertable to an int.
  """
  )
  def channel(self):
    return str(self._channel)

  @channel.setter
  def channel(self, value):
    if self._channel != value:
      self._channel = str(value)
  
  def channels(self):
    if self._channels is not None:
      return self._channels
    self._channels = [PyDMChannel(address=self._channel, connection_slot=self.connectionStateChanged, value_slot=self.valueReceived)]
    return self._channels
  
  @pyqtSlot(int)
  def valueReceived(self, new_val):
    self._value = new_val
    self.update_indicators()