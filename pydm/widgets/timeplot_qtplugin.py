from ..PyQt.QtDesigner import QExtensionFactory, QPyDesignerTaskMenuExtension
from ..PyQt.QtGui import QAction
from ..PyQt.QtCore import pyqtSlot
from .qtplugin_base import PyDMDesignerPlugin, qtplugin_factory
from .timeplot import PyDMTimePlot
from timeplot_curve_editor import TimePlotCurveEditorDialog
#PyDMTimePlotPlugin = qtplugin_factory(PyDMTimePlot)
Q_TYPEID = {'QPyDesignerContainerExtension':     'com.trolltech.Qt.Designer.Container',
            'QPyDesignerPropertySheetExtension': 'com.trolltech.Qt.Designer.PropertySheet',
            'QPyDesignerTaskMenuExtension':      'com.trolltech.Qt.Designer.TaskMenu',
            'QPyDesignerMemberSheetExtension':   'com.trolltech.Qt.Designer.MemberSheet'}
            
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
    if self.initialized:
       return
    manager = core.extensionManager()
    if manager:
      self.factory = PyDMTimePlotExtensionFactory(manager)
      manager.registerExtensions(self.factory, 'org.qt-project.Qt.Designer.TaskMenu')
      manager.registerExtensions(self.factory, 'com.trolltech.Qt.Designer.TaskMenu')
    #print("About to try and figure out what extensions are available.")
    #print(manager.extension(PyDMTimePlot(), 'org.qt-project.Qt.Designer.TaskMenu'))
    self.initialized = True


class PyDMTimePlotExtensionFactory(QExtensionFactory):
  def __init__(self, parent=None):
    super(PyDMTimePlotExtensionFactory, self).__init__(parent)

  def createExtension(self, obj, iid, parent):
    #Shouldn't have to check iid because we registered this factor for only this iid type.
    #if (str(iid) != 'org.qt-project.Qt.Designer.TaskMenu') or (str(iid) != 'com.trolltech.Qt.Designer.TaskMenu'):
    #  print("Extension id didn't match TaskMenu type.")
    #  return None
    if isinstance(obj, PyDMTimePlot):
      return PyDMTimePlotTaskMenuExtension(obj, parent)
    return None

class PyDMTimePlotTaskMenuExtension(QPyDesignerTaskMenuExtension):
  def __init__(self, time_plot, parent):
    super(PyDMTimePlotTaskMenuExtension, self).__init__(parent)
    self.time_plot = time_plot
    self.edit_curves_action = QAction("Edit Curves...", self)
    self.edit_curves_action.triggered.connect(self.edit_curves)

  @pyqtSlot()
  def edit_curves(self):
    edit_curves_dialog = TimePlotCurveEditorDialog(self.time_plot)
    edit_curves_dialog.exec_()

  def preferredEditAction(self):
    return self.edit_curves_action

  def taskActions(self):
    return [self.edit_curves_action]