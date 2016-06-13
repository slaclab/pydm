from PyQt4.QtGui import QLabel, QApplication, QColor
from PyQt4.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QString, QTimer
from pyqtgraph import PlotWidget, ViewBox, AxisItem, PlotItem
from pyqtgraph import PlotCurveItem

class BasePlot(PlotWidget):
  def __init__(self, parent=None, background='default', axisItems=None):
    super(BasePlot, self).__init__(parent=parent, background=background, axisItems=axisItems)
    self.showGrid(x=False, y=False)
    self.plotItem = self.getPlotItem()
    self.plotItem.hideButtons()
    self._auto_range_x = None
    self.setAutoRangeX(True)
    self._auto_range_y = None
    self.setAutoRangeY(True)
    self._show_x_grid = None
    self.setShowXGrid(True)
    self._show_y_grid = None
    self.setShowYGrid(True)
  
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