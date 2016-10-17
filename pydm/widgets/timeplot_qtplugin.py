# Try PyQt5
try:
    pyqt5 = True
    from PyQt5 import QtGui, QtDesigner
except ImportError:
    pyqt5 =  False
    # Imports for Pyqt4
    from PyQt4 import QtGui, QtDesigner

from timeplot import PyDMTimePlot

class TimePlotWidgetPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
  def __init__(self, parent = None):
    QtDesigner.QPyDesignerCustomWidgetPlugin.__init__(self)
    self.initialized = False
  
  def initialize(self, core):
    if self.initialized:
      return
    self.initialized = True

  def isInitialized(self):
    return self.initialized

  def createWidget(self, parent):
    return PyDMTimePlot(None, parent=parent)

  def name(self):
    return "PyDMTimePlot"

  def group(self):
    return "PyDM Widgets"

  def toolTip(self):
    return ""

  def whatsThis(self):
    return ""

  def isContainer(self):
    return False
    
  def icon(self):
    return QtGui.QIcon()

  def domXml(self):
    return (
               '<widget class="PyDMTimePlot" name=\"pydmTimePlot\">\n'
               " <property name=\"toolTip\" >\n"
               "  <string></string>\n"
               " </property>\n"
               " <property name=\"whatsThis\" >\n"
               "  <string>Plots a channel vs time.</string>\n"
               " </property>\n"
               "</widget>\n"
               )

  def includeFile(self):
    return "timeplot"
