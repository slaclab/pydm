from qtpy.QtWidgets import QWidget, QPlainTextEdit, QVBoxLayout
from qtpy.QtCore import Qt
from qtpy.QtGui import QFont


class MacroWindow(QWidget):
    """
    A replica of EDM's "Show Macros" display
    """
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Macros")
        self.setFixedWidth(750)
        self.setFixedHeight(500)

        text_box = QPlainTextEdit()
        text_box.setReadOnly(True)
        font = QFont()
        font.setPointSize(16)
        text_box.setFont(font)
        text_box.setPlainText("Macros:")

        # Populate macros
        if parent is not None:
            display_widget = parent.display_widget()
            if display_widget:
                macros = display_widget.macros()
                for macro, value in macros.items():
                    line = "  {}={}".format(macro, value)
                    text_box.appendPlainText(line)

        self.setLayout(QVBoxLayout(self))
        self.layout().addWidget(text_box)
