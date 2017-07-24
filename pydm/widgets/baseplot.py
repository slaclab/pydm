from ..PyQt.QtGui import QLabel, QApplication, QColor, QBrush
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QTimer
from .. import utilities
from pyqtgraph import PlotWidget, ViewBox, AxisItem, PlotItem
from pyqtgraph import PlotCurveItem
from collections import OrderedDict

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
    
    self._curves = []
    self._title = None
    self._show_legend = False
    self._legend = self.addLegend()
    self._legend.hide()
  
  def addCurve(self, plot_item, curve_color=None):
    if curve_color is None:
      curve_color = utilities.colors.default_colors[len(self._curves) % len(utilities.colors.default_colors)]
    plot_item.setPen(QColor(curve_color))
    self._curves.append(plot_item)
    self.addItem(plot_item)
    #self._legend.addItem(plot_item, plot_item.curve_name)
  
  def removeCurve(self, plot_item):
    self.removeItem(plot_item)
    #self._legend.removeItem(plot_item.name())
    self._curves.remove(plot_item)
  
  def removeCurveWithName(self, name):
    for curve in self._curves:
      if curve.name() == name:
        self.removeCurve(curve)
  
  def removeCurveAtIndex(self, index):
    curve_to_remove = self._curves[index]
    self.removeCurve(curve_to_remove)
    
  def setCurveAtIndex(self, index, new_curve):
    old_curve = self._curves[index]
    self._curves[index] = new_curve
    #self._legend.addItem(new_curve, new_curve.name())
    self.removeCurve(old_curve)
      
  def curveAtIndex(self, index):
    return self._curves[index]
  
  def curves(self):
    return self._curves
  
  def clear(self):
    legend_items = [label.text for (sample, label) in self._legend.items]
    for item in legend_items:
      self._legend.removeItem(item)
    self.plotItem.clear()
    self._curves = []
  
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
    if self._title is None:
      return ""
    return str(self._title)
  
  def setPlotTitle(self, value):
    self._title = str(value)
    if len(self._title) < 1:
      self._title=None
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
    self.setShowLegend(False)
    
  showLegend = pyqtProperty(bool, getShowLegend, setShowLegend, resetShowLegend)