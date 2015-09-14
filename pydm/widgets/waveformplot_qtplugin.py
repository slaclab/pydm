from PyQt4 import QtGui, QtDesigner
from waveformplot import WaveformPlot

class WaveformPlotWidgetPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
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
    return WaveformPlot(None, parent)

  def name(self):
    return "WaveformPlot"

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
               '<widget class="WaveformPlot" name=\"waveformPlot\">\n'
               " <property name=\"toolTip\" >\n"
               "  <string></string>\n"
               " </property>\n"
               " <property name=\"whatsThis\" >\n"
               "  <string>Plots a waveform.</string>\n"
               " </property>\n"
               "</widget>\n"
               )

  def includeFile(self):
    return "waveformplot"