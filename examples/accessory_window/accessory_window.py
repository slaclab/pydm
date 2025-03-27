import os
import sys
from pydm import Display
from qtpy.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from qtpy.QtCore import Slot


class MyDisplay(Display):
    def __init__(self, parent=None, args=[]):
        super().__init__(parent=parent, args=args)
        self.tracks = [
            "Humming",
            "Cowboys",
            "All Mine",
            "Mysterons",
            "Only You",
            "Half Day Closing",
            "Over",
            "Glory Box",
            "Sour Times",
            "Roads",
            "Strangers",
        ]
        self.numbers = range(len(self.tracks))
        self.labels = [QLabel(str(i), parent=self) for i in self.numbers]
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Accessory Window Example")
        main = QHBoxLayout()
        sub = QVBoxLayout()
        settings_button = QPushButton(self)
        settings_button.setText("Open Settings Window")
        settings_button.clicked.connect(self.open_settings_window)
        sub.addWidget(settings_button)
        for label in self.labels:
            sub.addWidget(label)
        main.addLayout(sub)
        self.setLayout(main)
        path_to_class = os.path.dirname(sys.modules[self.__module__].__file__)
        accessory_ui_path = os.path.join(path_to_class, "settings_window.ui")
        self.accessory_window = Display(
            ui_filename=accessory_ui_path
        )  # Note: purposefully not setting 'parent' on this - that way it shows up as its own window.
        self.accessory_window.ui.numbersButton.toggled.connect(self.show_numbers)
        self.accessory_window.ui.tracksButton.toggled.connect(self.show_tracks)

    @Slot()
    def open_settings_window(self):
        self.accessory_window.show()

    @Slot(bool)
    def show_numbers(self, toggled):
        if toggled:
            for number, label in zip(self.numbers, self.labels):
                label.setText(str(number))

    @Slot(bool)
    def show_tracks(self, toggled):
        if toggled:
            for track, label in zip(self.tracks, self.labels):
                label.setText(track)
