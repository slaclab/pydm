from pydm import Display
from qtpy.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout


class MyDisplay(Display):
    def __init__(self, parent=None, args=[]):
        super().__init__(parent=parent, args=args)
        self.setup_ui()

    def setup_ui(self):
        main = QHBoxLayout()
        sub = QVBoxLayout()
        for i in range(10):
            sub.addWidget(QLabel(str(i)))
        main.addLayout(sub)
        self.setLayout(main)

    def ui_filename(self):
        return None

    def ui_filepath(self):
        return None
