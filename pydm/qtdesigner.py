from .utilities import stylesheet


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
        self.__set_stylesheet_hook()

    def __set_stylesheet_hook(self):
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
