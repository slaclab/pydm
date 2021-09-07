import os
import json
from qtpy import QtCore
from pydm import Display
from qtpy.QtWidgets import (QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame,
    QApplication, QWidget, QLCDNumber)
from pydm.widgets import PyDMEmbeddedDisplay, PyDMLabel, PyDMLineEdit
from pydm.utilities import connection
from pydm.widgets.pushbutton import PyDMPushButton

class localTest(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super(localTest, self).__init__(parent=parent, args=args, macros=None)
        self.app = QApplication.instance()
        self.setup_ui()
        self.test = None

    def minimumSizeHint(self):
        return QtCore.QSize(100, 100)

    def ui_filepath(self):
        return None

    def setup_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        num_buttons = 4
        row = []
        self.button = []
        self.label = []

        display_list = [0,2,1,0]

        address_book = ["loc://{\"name\":\"bool_var\",\"type\":\"bool\",\"init\":false}",
                        "loc://{\"name\":\"int_var\",\"type\":\"int\",\"init\":10}",
                        "loc://{\"name\":\"str_var\",\"type\":\"str\",\"init\":\"Hello World\"}",
                        "loc://{\"name\":\"array_var\",\"type\":\"array\",\"init\":[0,0,0]}"]
        listener_book = ["loc://{\"name\":\"bool_var\"}",
                        "loc://{\"name\":\"int_var\"}",
                        "loc://{\"name\":\"str_var\"}",
                        "loc://{\"name\":\"array_var\"}"]

        for index in range(0,num_buttons):
            row.append(index)
            row[index] = QHBoxLayout()
            main_layout.addLayout(row[index])

        for key in range(0, num_buttons):
            self.button.append(key)
            self.button[key] = PyDMLineEdit()
            row[key].addWidget(self.button[key])
            self.button[key].channel = address_book[key]

            self.label.append(key)
            self.label[key]  = PyDMLabel()
            row[key].addWidget(self.label[key])
            self.label[key].channel = listener_book[key]
            self.label[key].displayFormat = display_list[key]
            self.label[key].showUnits = True

        #self.test("cat")

        #print(self.test)








