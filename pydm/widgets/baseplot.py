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
    
    self._curves = OrderedDict()   
    self._title = None
    self._show_legend = False
    self._legend = self.addLegend()
    self._legend.hide()
    self._pending_colors = []
  
  def addCurve(self, curve_name, plot_item=None, curve_color=None):
    if curve_name in self._curves:
      raise ValueError("Curve name already exists in plot, curve names must be unique.")
    if plot_item is None:
      plot_item = PlotCurveItem()
    if len(self._pending_colors) > 0:
      curve_color = self._pending_colors.pop(0)
    if curve_color is None:
      curve_color = utilities.colors.default_colors[len(self._curves) % len(utilities.colors.default_colors)]
    plot_item.setPen(QColor(curve_color))
    self._curves[curve_name] = plot_item
    self.addItem(self._curves[curve_name])
    self._legend.addItem(self._curves[curve_name], curve_name)
  
  def removeCurve(self, curve_name):
    if curve_name not in self._curves:
      raise ValueError("Curve name does not exist in plot.")
    self._legend.removeItem(curve_name)
    self.removeItem(self._curves[curve_name])
    del self._curves[curve_name]
  
  def plotItemForCurve(self, curve_name):
    return self._curves[curve_name]
  
  def clear(self):
    for curve_name in self._curves:
      self._legend.removeItem(curve_name)
    super(BasePlot, self).clear()
  
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
  
  def getCurveColorList(self):
    colors = []
    for curve in self._curves.values():
      color_string = curve.opts['pen'].color().name()
      try:
        color_string = utilities.colors.svg_color_from_hex(color_string)
      except KeyError:
        pass
      colors.append(color_string)
    return colors
  
  def setCurveColorList(self, color_string_list):
    if len(self._curves) == 0:
      # When loading a plot widget from a .ui file, the curveColorList property might get set
      # before self._curves has been populated.  We check for that case here.  If there aren't
      # any curves yet, save the list of colors to self._pending_colors, which will get consumed
      # as new curves are added in self.addCurve().
      self._pending_colors = [str(color) for color in list(color_string_list)]
      return
    if len(color_string_list) != len(self._curves):
      raise ValueError("Number of items in color string list must match number of curves.  {colorcount} colors, {curvecount} curves.".format(colorcount=len(color_string_list), curvecount=len(self._curves)))
    for (curve, color_string) in zip(self._curves.values(), color_string_list):
      curve.setPen(QColor(color_string))
    
  curveColorList = pyqtProperty("QStringList", getCurveColorList, setCurveColorList)
  
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