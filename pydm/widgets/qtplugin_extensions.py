from ..PyQt.QtDesigner import QExtensionFactory, QPyDesignerTaskMenuExtension
from ..PyQt import QtGui, QtCore
from ..widgets.rules_editor import RulesEditor
from ..widgets.base import PyDMPrimitiveWidget


class PyDMExtensionFactory(QExtensionFactory):
    def __init__(self, parent=None, extension_class=None):
        super(PyDMExtensionFactory, self).__init__(parent)
        self.extension_class = extension_class

    def createExtension(self, obj, iid, parent):
        if isinstance(obj, PyDMPrimitiveWidget):
            return self.extension_class(obj, parent)
        return None


class RulesTaskMenuExtension(QPyDesignerTaskMenuExtension):

    def __init__(self, widget, parent):
        super(RulesTaskMenuExtension, self).__init__(parent)
        self.widget = widget
        self.edit_rules_action = QtGui.QAction("Edit Rules...", self)
        self.edit_rules_action.triggered.connect(self.edit_rules)

    @QtCore.pyqtSlot()
    def edit_rules(self):
        edit_rules_dialog = RulesEditor(self.widget, self.widget)
        edit_rules_dialog.exec_()

    def taskActions(self):
        return [self.edit_rules_action]
