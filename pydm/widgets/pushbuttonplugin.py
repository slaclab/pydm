from PyQt4 import QtDesigner, QtGui

from pushbutton import PyDMPushButton



class PyDMPushButtonPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
    """
    Provides a Python custom plugin for Qt Designer implementation of
    PyDMPushButtonPlugin
    """
    def __init__(self,parent=None):
        QtDesigner.QPyDesignerCustomWidgetPlugin.__init__(self)
        self.initialized = False


    def initialize(self,core):
        if self.initialized:
            return
        self.intialized = True

    def isInitialized(self):
        return self.initialized

    def createWidget(self,parent):
       return PyDMPushButton(parent=parent) 

    def name(self):
        return "PyDMPushButton"

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

    def doXml(self):
        return (
                '<widget class="PyDMPushButton" name=\"pydmPushButton\">\n'
                ' <property name=\"toolTip\" >\n'
                '  <string></string>\n'
                ' </property?\n'
                ' <property name=\"whatsThis\" >\n'
                '  <string></string>\n'
                ' </property>\n'
                '</widget>\n'
                )

    def includeFile(self):
        return 'pushbutton'
