import json
from qtpy.QtWidgets import (
    QWidget,
    QPlainTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QApplication,
    QLabel,
)
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

        self.text_box = QPlainTextEdit()
        self.text_box.setReadOnly(True)
        self.font = QFont()
        self.font.setPointSize(16)
        self.text_box.setFont(self.font)
        self.text_box.setPlainText("Macros:")

        self.macros = {}
        self.init_macros()
        self.populate_macros()

        self.label = QLabel()
        self.label.setText("")
        self.label.setMinimumSize(100, 25)

        self.copy_button = QPushButton()
        self.copy_button.setCheckable(False)
        self.copy_button.setMinimumSize(75, 25)
        self.copy_button.setText("Copy Macros as JSON")
        self.copy_button.clicked.connect(self.copy_macros)

        self.clipboard = QApplication.clipboard()

        self.vBoxLayout = QVBoxLayout()
        self.vBoxLayout.addWidget(self.text_box)
        self.hBoxLayout = QHBoxLayout()
        self.hBoxLayout.addWidget(self.label, alignment=Qt.AlignRight)
        self.hBoxLayout.addWidget(self.copy_button, alignment=Qt.AlignRight)
        self.hBoxLayout.insertStretch(0)
        self.vBoxLayout.addLayout(self.hBoxLayout)

        self.setLayout(self.vBoxLayout)

    def init_macros(self):
        if self.parent() is not None:
            display_widget = self.parent().display_widget()
            if display_widget is not None:
                self.macros = display_widget.macros()

    def populate_macros(self):
        for macro, value in self.macros.items():
            line = "  {}={}".format(macro, value)
            self.text_box.appendPlainText(line)

    def copy_macros(self):
        self.clipboard.setText(json.dumps(self.macros))
        self.label.setText("Macros copied to clipboard!")
