from qtpy.QtDesigner import QExtensionFactory, QPyDesignerTaskMenuExtension
from qtpy import QtWidgets, QtCore

from ..widgets.base import PyDMPrimitiveWidget

from ..widgets.rules_editor import RulesEditor
from ..widgets.waveformplot_curve_editor import WaveformPlotCurveEditorDialog
from ..widgets.timeplot_curve_editor import TimePlotCurveEditorDialog
from ..widgets.scatterplot_curve_editor import ScatterPlotCurveEditorDialog


class PyDMExtensionFactory(QExtensionFactory):
    def __init__(self, parent=None):
        super(PyDMExtensionFactory, self).__init__(parent)

    def createExtension(self, obj, iid, parent):
        if not isinstance(obj, PyDMPrimitiveWidget):
            return None

        # For now check the iid for TaskMenu...
        if iid == "org.qt-project.Qt.Designer.TaskMenu":
            return PyDMTaskMenuExtension(obj, parent)
        # In the future we can expand to the others such as Property and etc
        # When the time comes...  we will need a new PyDMExtension and
        # the equivalent for PyDMTaskMenuExtension classes for the
        # property editor and an elif statement in here to instantiate it...

        return None


class PyDMTaskMenuExtension(QPyDesignerTaskMenuExtension):
    def __init__(self, widget, parent):
        super(PyDMTaskMenuExtension, self).__init__(parent)

        self.widget = widget
        self.__actions = None
        self.__extensions = []
        extensions = getattr(widget, 'extensions', None)

        if extensions is not None:
            for ex in extensions:
                extension = ex(self.widget)
                self.__extensions.append(extension)

    def taskActions(self):
        if self.__actions is None:
            self.__actions = []
            for ex in self.__extensions:
                self.__actions.extend(ex.actions())

        return self.__actions

    def preferredEditAction(self):
        if self.__actions is None:
            self.taskActions()
        if self.__actions:
            return self.__actions[0]


class PyDMExtension(object):
    def __init__(self, widget):
        self.widget = widget

    def actions(self):
        raise NotImplementedError


class RulesExtension(PyDMExtension):
    def __init__(self, widget):
        super(RulesExtension, self).__init__(widget)
        self.widget = widget
        self.edit_rules_action = QtWidgets.QAction("Edit Rules...", self.widget)
        self.edit_rules_action.triggered.connect(self.edit_rules)

    def edit_rules(self, state):
        edit_rules_dialog = RulesEditor(self.widget, parent=None)
        edit_rules_dialog.exec_()

    def actions(self):
        return [self.edit_rules_action]


class BasePlotExtension(PyDMExtension):
    def __init__(self, widget, curve_editor_class):
        super(BasePlotExtension, self).__init__(widget)
        self.widget = widget
        self.curve_editor_class = curve_editor_class
        self.edit_curves_action = QtWidgets.QAction("Edit Curves...", self.widget)
        self.edit_curves_action.triggered.connect(self.edit_curves)

    def edit_curves(self, state):
        edit_curves_dialog = self.curve_editor_class(self.widget, parent=self.widget)
        edit_curves_dialog.exec_()

    def actions(self):
        return [self.edit_curves_action]


class WaveformCurveEditorExtension(BasePlotExtension):
    def __init__(self, widget):
        super(WaveformCurveEditorExtension, self).__init__(widget, WaveformPlotCurveEditorDialog)


class TimeCurveEditorExtension(BasePlotExtension):
    def __init__(self, widget):
        super(TimeCurveEditorExtension, self).__init__(widget, TimePlotCurveEditorDialog)


class ScatterCurveEditorExtension(BasePlotExtension):
    def __init__(self, widget):
        super(ScatterCurveEditorExtension, self).__init__(widget, ScatterPlotCurveEditorDialog)
