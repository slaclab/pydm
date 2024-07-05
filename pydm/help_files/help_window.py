from pathlib import Path
from qtpy.QtWidgets import QTextBrowser, QVBoxLayout, QWidget
from qtpy.QtCore import Qt
from typing import Optional


class HelpWindow(QWidget):
    """
    A window for displaying a help file for a PyDM display

    Parameters
    ----------
    help_file_path : str
        The path to the help file to be displayed
    """

    def __init__(self, help_file_path: str, parent: Optional[QWidget] = None):
        super().__init__(parent, Qt.Window)
        self.resize(500, 400)

        path = Path(help_file_path)
        self.setWindowTitle(f"Help for {path.stem}")

        self.display_content = QTextBrowser()

        with open(help_file_path) as file:
            if path.suffix == ".txt":
                self.display_content.setText(file.read())
            else:
                self.display_content.setHtml(file.read())

        self.vBoxLayout = QVBoxLayout()
        self.vBoxLayout.addWidget(self.display_content)
        self.setLayout(self.vBoxLayout)
