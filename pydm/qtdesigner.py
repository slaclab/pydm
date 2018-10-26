from qtpy.QtCore import QTimer
from .utilities import stylesheet
from . import data_plugins


class DesignerHooks(object):
    """
    Class that handles the integration with PyDM and the Qt Designer
    by hooking up slots to signals provided by FormEditor and other classes.
    """
    __instance = None

    def __init__(self):
        if self.__initialized:
            return
        self.__form_editor = None
        self.__initialized = True
        self.__timer = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(DesignerHooks)
            cls.__instance.__initialized = False
        return cls.__instance

    @property
    def form_editor(self):
        return self.__form_editor

    @form_editor.setter
    def form_editor(self, editor):
        if self.form_editor is not None:
            return

        if not editor:
            return

        self.__form_editor = editor
        self.setup_hooks()

    def setup_hooks(self):
        # Set PyDM to be read-only
        data_plugins.set_read_only(True)

        if self.form_editor:
            fwman = self.form_editor.formWindowManager()
            if fwman:
                fwman.formWindowAdded.connect(
                    self.__new_form_added
                )

    def __new_form_added(self, form_window_interface):
        style_data = stylesheet._get_style_data(None)
        widget = form_window_interface.formContainer()
        widget.setStyleSheet(style_data)
        if not self.__timer:
            self.__start_kicker()

    def __kick(self):
        fwman = self.form_editor.formWindowManager()
        if fwman:
            widget = fwman.activeFormWindow()
            if widget:
                widget.update()

    def __start_kicker(self):
        self.__timer = QTimer()
        self.__timer.setInterval(100)
        self.__timer.timeout.connect(self.__kick)
        self.__timer.start()
