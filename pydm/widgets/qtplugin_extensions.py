from ..PyQt.QtDesigner import QExtensionFactory, QPyDesignerTaskMenuExtension
from ..PyQt import QtGui, QtCore
from ..widgets.rules_editor import RulesEditor
from ..widgets.base import PyDMPrimitiveWidget


class PyDMExtensionFactory(QExtensionFactory):
    def __init__(self, parent=None, extension_class=None):
        super(PyDMExtensionFactory, self).__init__(parent)
        self.extension_class = extension_class

    def createExtension(self, obj, iid, parent):
        print("Factory - Create Extension for: ", type(obj))

        if isinstance(obj, PyDMPrimitiveWidget):
            print("Return the extension class")
            return self.extension_class(obj, parent)
        print("Not PyDMPrimitiveWidget... Return None")
        return None


class RulesTaskMenuExtension(QPyDesignerTaskMenuExtension):

    def __init__(self, widget, parent):
        super(RulesTaskMenuExtension, self).__init__(parent)
        print("Creating Rules Task Extension")
        self.widget = widget
        self.edit_rules_action = QtGui.QAction("Edit Rules...", self)
        self.edit_rules_action.triggered.connect(self.edit_rules)

    @QtCore.pyqtSlot()
    def edit_rules(self):
        print("Called Edit Rules from Extension")
        edit_rules_dialog = RulesEditor(self.widget, self.widget)
        edit_rules_dialog.exec_()

    def taskActions(self):
        return [self.edit_rules_action]
