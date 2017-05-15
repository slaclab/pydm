from ..PyQt.QtGui import QLabel, QApplication, QColor, QBrush
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QTimer
from pyqtgraph import PlotWidget, ViewBox, AxisItem, PlotItem
from pyqtgraph import PlotCurveItem

class BasePlot(PlotWidget):
  def __init__(self, parent=None, background='default', axisItems=None):
    super(BasePlot, self).__init__(parent=parent, background=background, axisItems=axisItems)
    self.plotItem = self.getPlotItem()
    self.plotItem.hideButtons()
    self._auto_range_x = None
    self.setAutoRangeX(True)
    self._auto_range_y = None
    self.setAutoRangeY(True)
    self._show_x_grid = None
    self.setShowXGrid(False)
    self._show_y_grid = None
    self.setShowYGrid(False)
    self._curveColor=QColor(255,255,255)
    self.curve = PlotCurveItem(pen=self._curveColor)
    self.addItem(self.curve)
    self._title = None
    self._show_legend = False
    self._legend = None
  
  def getAutoRangeX(self):
    return self._auto_range_x
  
  def setAutoRangeX(self, value):
    self._auto_range_x = value
    self.plotItem.enableAutoRange(ViewBox.XAxis,enable=self._auto_range_x)
      
  def resetAutoRangeX(self):
    self.setAutoRangeX(True)
    
  autoRangeX = pyqtProperty("bool", getAutoRangeX, setAutoRangeX, resetAutoRangeX)
  
  def getAutoRangeY(self):
    return self._auto_range_y
  
  def setAutoRangeY(self, value):
    self._auto_range_y = value
    self.plotItem.enableAutoRange(ViewBox.YAxis,enable=self._auto_range_y)
      
  def resetAutoRangeY(self):
    self.setAutoRangeY(True)
    
  autoRangeY = pyqtProperty("bool", getAutoRangeY, setAutoRangeY, resetAutoRangeY)
  
  def getShowXGrid(self):
    return self._show_x_grid
  
  def setShowXGrid(self, value):
    self._show_x_grid = value
    self.showGrid(x=self._show_x_grid)
      
  def resetShowXGrid(self):
    self.setShowXGrid(False)
    
  showXGrid = pyqtProperty("bool", getShowXGrid, setShowXGrid, resetShowXGrid)
  
  def getShowYGrid(self):
    return self._show_y_grid
  
  def setShowYGrid(self, value):
    self._show_y_grid = value
    self.showGrid(y=self._show_y_grid)
      
  def resetShowYGrid(self):
    self.setShowYGrid(False)
    
  showYGrid = pyqtProperty("bool", getShowYGrid, setShowYGrid, resetShowYGrid)
  
  def getCurveColor(self):
    return self._curveColor

  def setCurveColor(self, color):
    if self._curveColor != color:
      self._curveColor = color
      self.curve.setPen(self._curveColor)
    
  curveColor = pyqtProperty(QColor, getCurveColor, setCurveColor)
  
  def getBackgroundColor(self):
    return self.backgroundBrush().color()

  def setBackgroundColor(self, color):
    if self.backgroundBrush().color() != color:
      self.setBackgroundBrush(QBrush(color))
    
  backgroundColor = pyqtProperty(QColor, getBackgroundColor, setBackgroundColor)

  def getAxisColor(self):
    return self.getAxis('bottom')._pen.color()

  def setAxisColor(self, color):
    if self.getAxis('bottom')._pen.color() != color:
      self.getAxis('bottom').setPen(color)
      self.getAxis('left').setPen(color)
      self.getAxis('top').setPen(color)
      self.getAxis('right').setPen(color)
      
  axisColor = pyqtProperty(QColor, getAxisColor, setAxisColor)
  
  def getPlotTitle(self):
    return str(self._title)
  
  def setPlotTitle(self, value):
    self._title = str(value)
    self.setTitle(self._title)

  def resetPlotTitle(self):
    self._title = None
    self.setTitle(self._title)
    
  title = pyqtProperty(str, getPlotTitle, setPlotTitle, resetPlotTitle)

  def getShowLegend(self):
    return self._show_legend
  
  def setShowLegend(self, value):
    self._show_legend = value
    if self._show_legend:
      if self._legend is None:
        self._legend = self.addLegend()
      else:
        self._legend.show()
    else:
      if self._legend is not None:
        self._legend.hide()

  def resetShowLegend(self):
    self._show_legend = False
    
  showLegend = pyqtProperty(bool, getShowLegend, setShowLegend, resetShowLegend)