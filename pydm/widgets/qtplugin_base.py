"""
Module to define a parent qtdesigner plugin class.

Please continue to name your qtdesigner plugin modules using the convention
modulename.py          <--- defines the widget
modulename_qtplugin.py <--- imports this module + the widget

NOTE: PyDMDesignerPlugin is a valid plugin, so designer will try to pick it up
      and instantiate it if you import it into another module's namespace. You
      will need to avoid having it present in the global namespace of any
      module that defines a qtplugin.

If you do not heed this warning, you will get a one-line traceback:
TypeError: __init__() takes exactly 3 arguments (1 given)
for each PyDMDesignerPlugin that Qt Designer tries to use. This will not
affect any of your widgets, but it will be annoying.
"""
from ..PyQt import QtGui, QtDesigner

def qtplugin_factory(cls, is_container=False):
    """
    Helper function to create a generic PyDMDesignerPlugin class.

    :param cls: Widget class
    :type cls:  QWidget
    """
    class Plugin(PyDMDesignerPlugin):
        __doc__ = "PyDMDesigner Plugin for {}".format(cls.__name__)
        def __init__(self):
            super(Plugin, self).__init__(cls, is_container)
    return Plugin

class PyDMDesignerPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
    """
    Parent class to standardize how pydm plugins are accessed in qt designer.
    All functions have default returns that can be overriden as necessary.
    """
    def __init__(self, cls, is_container=False):
        """
        Set up the plugin using the class info in cls

        :param cls: Class of the widget to use
        :type cls:  QWidget
        """
        QtDesigner.QPyDesignerCustomWidgetPlugin.__init__(self)
        self.initialized = False
        self.is_container = is_container
        self.cls = cls

    def initialize(self, core):
        """
        Override this function if you need special initialization instructions.
        Make sure you don't neglect to set the self.initialized flag to True
        after a successful initialization.

        :param core: form editor interface to use in the initialization
        :type core:  QDesignerFormEditorInterface
        """
        if self.initialized:
            return
        self.initialized = True

    def isInitialized(self):
        """
        Return True if initialize function has been called successfully.
        """
        return self.initialized

    def createWidget(self, parent):
        """
        Instantiate a widget with the given parent.

        :param parent: Parent widget of instantiated widget
        :type parent:  QWidget
        """
        w = self.cls(parent=parent)
        try:
          w.init_for_designer()
        except (AttributeError, NameError):
          pass
        return w

    def name(self):
        """
        Return the class name of the widget.
        """
        return self.cls.__name__

    def group(self):
        """
        Return a common group name so all PyDM Widgets are together in
        Qt Designer.
        """
        return "PyDM Widgets"

    def toolTip(self):
        """
        A short description to pop up on mouseover. If we leave this as an
        empty string, we'll have no tooltip by default and can override this
        on a case-by-case basis.
        """
        return ""

    def whatsThis(self):
        """
        A longer description of the widget for Qt Designer. By default, this
        is the entire class docstring.
        """
        try:
            if isinstance(self.cls.__doc__, str):
                return self.cls.__doc__
        except AttributeError:
            pass
        return ""

    def isContainer(self):
        """
        Return True if this widget can contain other widgets.
        """
        return self.is_container

    def icon(self):
        """
        Return a QIcon to represent this widget in Qt Designer.
        """
        return QtGui.QIcon()

    def domXml(self):
        """
        XML Description of the widget's properties.
        """
        return (
                "<widget class=\"{0}\" name=\"{0}\">\n"
                " <property name=\"toolTip\" >\n"
                "  <string>{1}</string>\n"
                " </property>\n"
                " <property name=\"whatsThis\" >\n"
                "  <string>{2}</string>\n"
                " </property>\n"
                "</widget>\n"
               ).format(self.name(), self.toolTip(), self.whatsThis())

    def includeFile(self):
        """
        Include the class module for the generated qt code
        """
        return self.cls.__module__

