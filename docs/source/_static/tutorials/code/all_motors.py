import os
import json
from pydm import Display
from qtpy.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QFrame,
    QApplication,
    QWidget,
)
from qtpy import QtCore
from pydm.widgets import PyDMEmbeddedDisplay


class AllMotorsDisplay(Display):
    def __init__(self, parent=None, args=[], macros=None):
        super().__init__(parent=parent, args=args, macros=macros)
        # Placeholder for data to filter
        self.data = []
        # Reference to the PyDMApplication
        self.app = QApplication.instance()
        # Assemble the Widgets
        self.setup_ui()
        # Load data from file
        self.load_data()

    def minimumSizeHint(self):
        # This is the default recommended size
        # for this screen
        return QtCore.QSize(750, 120)

    def ui_filepath(self):
        # No UI file is being used
        return None

    def setup_ui(self):
        # Create the main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Create a Label to be the title
        lbl_title = QLabel("Motors Diagnostic")
        # Add some StyleSheet to it
        lbl_title.setStyleSheet(
            "\
            QLabel {\
                qproperty-alignment: AlignCenter;\
                border: 1px solid #FF17365D;\
                border-top-left-radius: 15px;\
                border-top-right-radius: 15px;\
                background-color: #FF17365D;\
                padding: 5px 0px;\
                color: rgb(255, 255, 255);\
                max-height: 25px;\
                font-size: 14px;\
            }"
        )

        # Add the title label to the main layout
        main_layout.addWidget(lbl_title)

        # Create the Search Panel layout
        search_layout = QHBoxLayout()

        # Create a GroupBox with "Filtering" as Title
        gb_search = QGroupBox(parent=self)
        gb_search.setTitle("Filtering")
        gb_search.setLayout(search_layout)

        # Create a label, line edit and button for filtering
        lbl_search = QLabel(text="Filter: ")
        self.txt_filter = QLineEdit()
        self.txt_filter.returnPressed.connect(self.do_search)
        btn_search = QPushButton()
        btn_search.setText("Search")
        btn_search.clicked.connect(self.do_search)

        # Add the created widgets to the layout
        search_layout.addWidget(lbl_search)
        search_layout.addWidget(self.txt_filter)
        search_layout.addWidget(btn_search)

        # Add the Groupbox to the main layout
        main_layout.addWidget(gb_search)

        # Create the Results Layout
        self.results_layout = QVBoxLayout()
        self.results_layout.setContentsMargins(0, 0, 0, 0)

        # Create a Frame to host the results of search
        self.frm_result = QFrame(parent=self)
        self.frm_result.setLayout(self.results_layout)

        # Create a ScrollArea so we can properly handle
        # many entries
        scroll_area = QScrollArea(parent=self)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll_area.setWidgetResizable(True)

        # Add the Frame to the scroll area
        scroll_area.setWidget(self.frm_result)

        # Add the scroll area to the main layout
        main_layout.addWidget(scroll_area)

    def load_data(self):
        # Extract the directory of this file...
        base_dir = os.path.dirname(os.path.realpath(__file__))
        # Concatenate the directory with the file name...
        data_file = os.path.join(base_dir, "motor_db.txt")
        # Open the file so we can read the data...
        with open(data_file, "r") as f:
            # For each line in the file...
            for entry in f.readlines():
                # Append to the list of data...
                self.data.append(entry[:-1])

    def do_search(self):
        # For each widget inside the results frame, lets destroy them
        for widget in self.frm_result.findChildren(QWidget):
            widget.setParent(None)
            widget.deleteLater()

        # Grab the filter text
        filter_text = self.txt_filter.text()

        # For every entry in the dataset...
        for entry in self.data:
            # Check if they match our filter
            if filter_text.upper() not in entry.upper():
                continue
            # Create a PyDMEmbeddedDisplay for this entry
            disp = PyDMEmbeddedDisplay(parent=self)
            disp.macros = json.dumps({"MOTOR": entry})
            disp.filename = "inline_motor.ui"
            disp.setMinimumWidth(700)
            disp.setMinimumHeight(40)
            disp.setMaximumHeight(100)
            # Add the Embedded Display to the Results Layout
            self.results_layout.addWidget(disp)
