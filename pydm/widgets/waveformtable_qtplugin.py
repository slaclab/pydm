from PyQt4 import QtGui, QtDesigner
from waveformtable import PyDMWaveformTable

class WaveformTableWidgetPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
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
    return PyDMWaveformTable(parent=parent, init_channel=None)

  def name(self):
    return "PyDMWaveformTable"

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
               '<widget class="PyDMWaveformTable" name=\"pydmWaveformTable\">\n'
               " <property name=\"toolTip\" >\n"
               "  <string></string>\n"
               " </property>\n"
               " <property name=\"whatsThis\" >\n"
               "  <string>Displays a waveform in table form.</string>\n"
               " </property>\n"
               "</widget>\n"
               )

  def includeFile(self):
    return "waveformtable"