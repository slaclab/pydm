from ..PyQt.QtDesigner import QExtensionFactory, QPyDesignerTaskMenuExtension
from ..PyQt.QtGui import QAction
from ..PyQt.QtCore import pyqtSlot
from .qtplugin_base import PyDMDesignerPlugin, WidgetCategory
from .baseplot import BasePlot
from .baseplot_curve_editor import BasePlotCurveEditorDialog


def qtplugin_plot_factory(cls, curve_editor_class=None):
    class PlotPlugin(BasePlotPlugin):
        __doc__ = "PyDMDesigner Plugin for {}".format(cls.__name__)
        PlotClass = cls
        CurveEditorClass = curve_editor_class
    return PlotPlugin


class BasePlotPlugin(PyDMDesignerPlugin):
    PlotClass = BasePlot
    CurveEditorClass = BasePlotCurveEditorDialog

    def __init__(self):
        super(BasePlotPlugin, self).__init__(self.PlotClass,
                                             group=WidgetCategory.PLOT)
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
            self.factory = BasePlotExtensionFactory(
                                    parent=manager,
                                    plot_class=self.PlotClass,
                                    curve_editor_class=self.CurveEditorClass)
            manager.registerExtensions(
                self.factory, 'org.qt-project.Qt.Designer.TaskMenu')  # Qt5
            manager.registerExtensions(
                self.factory, 'com.trolltech.Qt.Designer.TaskMenu')  # Qt4
        self.initialized = True

    def createWidget(self, parent):
        """
        Instantiate a widget with the given parent.

        :param parent: Parent widget of instantiated widget
        :type parent:  QWidget
        """
        plot = self.cls(parent=parent)
        plot.initialize_for_designer()
        return plot


class BasePlotExtensionFactory(QExtensionFactory):

    def __init__(self, parent=None, plot_class=None, curve_editor_class=None):
        super(BasePlotExtensionFactory, self).__init__(parent)
        self.plot_class = plot_class
        self.curve_editor_class = curve_editor_class

    def createExtension(self, obj, iid, parent):
        # Shouldn't have to check iid because we registered this factor for
        # only this iid type.
        # if  ((str(iid) != 'org.qt-project.Qt.Designer.TaskMenu') or
        #      (str(iid) != 'com.trolltech.Qt.Designer.TaskMenu')):
        #     print("Extension id didn't match TaskMenu type.")
        #     return None
        if isinstance(obj, self.plot_class):
            return BasePlotTaskMenuExtension(
                                    obj, parent, self.curve_editor_class)
        return None


class BasePlotTaskMenuExtension(QPyDesignerTaskMenuExtension):

    def __init__(self, plot, parent, curve_editor_class):
        super(BasePlotTaskMenuExtension, self).__init__(parent)
        self.curve_editor_class = curve_editor_class
        self.plot = plot
        self.edit_curves_action = QAction("Edit Curves...", self)
        self.edit_curves_action.triggered.connect(self.edit_curves)

    @pyqtSlot()
    def edit_curves(self):
        edit_curves_dialog = self.curve_editor_class(self.plot)
        edit_curves_dialog.exec_()

    def preferredEditAction(self):
        return self.edit_curves_action

    def taskActions(self):
        return [self.edit_curves_action]
