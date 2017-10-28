from ..PyQt.QtDesigner import QExtensionFactory, QPyDesignerTaskMenuExtension
from ..PyQt.QtGui import QAction
from ..PyQt.QtCore import pyqtSlot
from .qtplugin_base import PyDMDesignerPlugin, WidgetCategory
from .scatterplot import PyDMScatterPlot
from .scatterplot_curve_editor import ScatterPlotCurveEditorDialog

class PyDMScatterPlotPlugin(PyDMDesignerPlugin):
    def __init__(self):
        super(PyDMScatterPlotPlugin, self).__init__(PyDMScatterPlot, group=WidgetCategory.PLOT)
        self.factory = None
        
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
        manager = core.extensionManager()
        if manager:
            self.factory = PyDMScatterPlotExtensionFactory(manager)
            manager.registerExtensions(self.factory, 'org.qt-project.Qt.Designer.TaskMenu') #Qt5
            manager.registerExtensions(self.factory, 'com.trolltech.Qt.Designer.TaskMenu') #Qt4
        self.initialized = True


class PyDMScatterPlotExtensionFactory(QExtensionFactory):
    def __init__(self, parent=None):
        super(PyDMScatterPlotExtensionFactory, self).__init__(parent)

    def createExtension(self, obj, iid, parent):
        #Shouldn't have to check iid because we registered this factor for only this iid type.
        #if (str(iid) != 'org.qt-project.Qt.Designer.TaskMenu') or (str(iid) != 'com.trolltech.Qt.Designer.TaskMenu'):
        #  print("Extension id didn't match TaskMenu type.")
        #  return None
        if isinstance(obj, PyDMScatterPlot):
            return PyDMScatterPlotTaskMenuExtension(obj, parent)
        return None

class PyDMScatterPlotTaskMenuExtension(QPyDesignerTaskMenuExtension):
    def __init__(self, scatter_plot, parent):
        super(PyDMScatterPlotTaskMenuExtension, self).__init__(parent)
        self.scatter_plot = scatter_plot
        self.edit_curves_action = QAction("Edit Curves...", self)
        self.edit_curves_action.triggered.connect(self.edit_curves)

    @pyqtSlot()
    def edit_curves(self):
        edit_curves_dialog = ScatterPlotCurveEditorDialog(self.scatter_plot)
        edit_curves_dialog.exec_()

    def preferredEditAction(self):
        return self.edit_curves_action

    def taskActions(self):
        return [self.edit_curves_action]

