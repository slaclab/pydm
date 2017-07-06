from ..PyQt.QtDesigner import QExtensionFactory, QPyDesignerTaskMenuExtension
from ..PyQt.QtGui import QAction
from ..PyQt.QtCore import pyqtSlot
from .qtplugin_base import PyDMDesignerPlugin, qtplugin_factory
from .timeplot import PyDMTimePlot

#PyDMTimePlotPlugin = qtplugin_factory(PyDMTimePlot)

class PyDMTimePlotPlugin(PyDMDesignerPlugin):
  def __init__(self):
    super(PyDMTimePlotPlugin, self).__init__(PyDMTimePlot)
    self.factory = None
    
  def initialize(self, core):
    """
    Override this function if you need special initialization instructions.
    Make sure you don't neglect to set the self.initialized flag to True
    after a successful initialization.

    :param core: form editor interface to use in the initialization
    :type core:  QDesignerFormEditorInterface
    """
    print("Initializing plugin.")
    if self.initialized:
       return
    manager = core.extensionManager()
    if manager:
      self.factory = PyDMTimePlotExtensionFactory(manager)
      manager.registerExtensions(self.factory, 'org.qt-project.Qt.Designer.TaskMenu')
    print("About to try and figure out what extensions are available.")
    print(manager.extension(PyDMTimePlot(), 'org.qt-project.Qt.Designer.TaskMenu'))
    self.initialized = True


class PyDMTimePlotExtensionFactory(QExtensionFactory):
  def __init__(self, parent=None):
    print("Initializing extension factory!")
    super(PyDMTimePlotExtensionFactory, self).__init__(parent)

  def createExtension(self, obj, iid, parent):
    print("createExtension called...")
    if iid != 'org.qt-project.Qt.Designer.TaskMenu':
      return None
    if isinstance(obj, PyDMTimePlot):
      print("Creating extension!")
      return PyDMTimePlotTaskMenuExtension(obj, parent)
    return None

class PyDMTimePlotTaskMenuExtension(QPyDesignerTaskMenuExtension):
  def __init__(self, time_plot, parent):
    print("Initializing menu extension.")
    super(PyDMTimePlotTaskMenuExtension, self).__init__(parent)
    self.time_plot = time_plot
    self.edit_curves_action = QAction("Edit Curves...", self)
    self.edit_curves_action.triggered.connect(self.edit_curves)

  @pyqtSlot()
  def edit_curves(self):
    edit_curves_dialog = PlotCurveEditorDialog(self.time_plot)
    edit_curves_dialog.exec_()

  def preferredEditAction(self):
    return self.edit_curves_action

  def taskActions(self):
    print("Listing actions.")
    return [self.edit_curves_action]