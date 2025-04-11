import logging

from qtpy.QtDesigner import QExtensionFactory, QPyDesignerTaskMenuExtension
from qtpy import QtWidgets

from pydm.utilities import copy_to_clipboard, get_clipboard_text
from pydm.widgets.base import PyDMPrimitiveWidget

from pydm.widgets.rules_editor import RulesEditor
from pydm.widgets.designer_settings import BasicSettingsEditor
from pydm.widgets.archiver_time_plot_editor import ArchiverTimePlotCurveEditorDialog
from pydm.widgets.waveformplot_curve_editor import WaveformPlotCurveEditorDialog
from pydm.widgets.timeplot_curve_editor import TimePlotCurveEditorDialog
from pydm.widgets.scatterplot_curve_editor import ScatterPlotCurveEditorDialog
from pydm.widgets.eventplot_curve_editor import EventPlotCurveEditorDialog
from pydm.widgets.symbol_editor import SymbolEditor


logger = logging.getLogger(__name__)


class PyDMExtensionFactory(QExtensionFactory):
    def __init__(self, parent=None):
        super().__init__(parent)

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
        super().__init__(parent)

        self.widget = widget
        self.__actions = None
        self.__extensions = []
        extensions = getattr(widget, "extensions", None)

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


class BasicSettingsExtension(PyDMExtension):
    def __init__(self, widget):
        super().__init__(widget)
        self.widget = widget
        self.edit_settings_action = QtWidgets.QAction("Py&DM basic settings...", self.widget)
        self.edit_settings_action.triggered.connect(self.open_dialog)

        if not hasattr(widget, "channel"):
            self.channel_menu_action = None
        else:
            self.channel_menu_action = QtWidgets.QAction("PyDM C&hannel", self.widget)
            # self.channel_menu_action.triggered.connect(self.open_channel_menu)
            self.channel_menu = QtWidgets.QMenu()
            self.copy_channel_action = self.channel_menu.addAction("")
            self.copy_channel_action.triggered.connect(self.copy_channel)
            self.paste_channel_action = self.channel_menu.addAction("")
            self.paste_channel_action.triggered.connect(self.paste_channel)
            self.channel_menu.aboutToShow.connect(self.update_action_clipboard_text)
            edit_channel = self.channel_menu.addAction("&Edit channel...")
            edit_channel.triggered.connect(self.open_dialog)
            copy_channel_value = self.channel_menu.addAction("C&opy current value")
            copy_channel_value.triggered.connect(self.copy_channel_value)
            self.channel_menu_action.setMenu(self.channel_menu)

    def update_action_clipboard_text(self):
        self.copy_channel_action.setText(f"&Copy to clipboard: {self.widget.channel}")
        clipboard_text = get_clipboard_text() or ""
        self.paste_channel_action.setText(f"&Paste from clipboard: {clipboard_text[:100]}")

    def copy_channel(self, _):
        channel = self.widget.channel
        if channel:
            copy_to_clipboard(channel)

    def copy_channel_value(self, _):
        value = getattr(self.widget, "value", None)
        if value:
            copy_to_clipboard(value)

    def paste_channel(self, _):
        self.widget.channel = get_clipboard_text() or ""
        logger.info("Set widget channel to %r", self.widget.channel)

    def open_dialog(self, state):
        dialog = BasicSettingsEditor(self.widget, parent=None)
        dialog.exec_()

    def actions(self):
        actions = [
            self.edit_settings_action,
            self.channel_menu_action,
        ]
        return [action for action in actions if action is not None]


class RulesExtension(PyDMExtension):
    def __init__(self, widget):
        super().__init__(widget)
        self.widget = widget
        self.edit_rules_action = QtWidgets.QAction("Edit Rules...", self.widget)
        self.edit_rules_action.triggered.connect(self.edit_rules)

    def edit_rules(self, state):
        edit_rules_dialog = RulesEditor(self.widget, parent=None)
        edit_rules_dialog.exec_()

    def actions(self):
        return [self.edit_rules_action]


class SymbolExtension(PyDMExtension):
    def __init__(self, widget):
        super().__init__(widget)
        self.widget = widget
        self.edit_symbols_action = QtWidgets.QAction("Edit Symbols...", self.widget)
        self.edit_symbols_action.triggered.connect(self.edit_symbols)

    def edit_symbols(self, state):
        edit_symbols_dialog = SymbolEditor(self.widget, parent=None)
        edit_symbols_dialog.exec_()

    def actions(self):
        return [self.edit_symbols_action]


class BasePlotExtension(PyDMExtension):
    def __init__(self, widget, curve_editor_class):
        super().__init__(widget)
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
        super().__init__(widget, WaveformPlotCurveEditorDialog)


class ArchiveTimeCurveEditorExtension(BasePlotExtension):
    def __init__(self, widget):
        super().__init__(widget, ArchiverTimePlotCurveEditorDialog)


class TimeCurveEditorExtension(BasePlotExtension):
    def __init__(self, widget):
        super().__init__(widget, TimePlotCurveEditorDialog)


class ScatterCurveEditorExtension(BasePlotExtension):
    def __init__(self, widget):
        super().__init__(widget, ScatterPlotCurveEditorDialog)


class EventCurveEditorExtension(BasePlotExtension):
    def __init__(self, widget):
        super().__init__(widget, EventPlotCurveEditorDialog)
