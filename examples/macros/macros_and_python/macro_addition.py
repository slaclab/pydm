from pydm import Display


class MacroAddition(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super().__init__(parent=parent, macros=macros)
        self.ui.resultLabel.setText("{}".format(float(macros["a"]) + float(macros["b"])))

    def ui_filename(self):
        return "macro_addition.ui"
