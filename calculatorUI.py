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

class calculator(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super(calculator, self).__init__(parent=parent, args=args, macros=None)
        self.calculation = None
        self.app = QApplication.instance()
        self.setup_ui()

    def minimumSizeHint(self):
        return QtCore.QSize(100, 100)

    def ui_filepath(self):
        return None

    def setup_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.lcdNumber = QLineEdit()
        self.lcdNumber.setObjectName("lcdNumber")
        main_layout.addWidget(self.lcdNumber)
        self.lcdNumber.setReadOnly(True)

        zero_row = QHBoxLayout()
        one_row = QHBoxLayout()
        two_row = QHBoxLayout()
        three_row = QHBoxLayout()
        four_row = QHBoxLayout()

        main_layout.addLayout(zero_row)
        main_layout.addLayout(one_row)
        main_layout.addLayout(two_row)
        main_layout.addLayout(three_row)
        main_layout.addLayout(four_row)


        self.sendInfo = PyDMLineEdit()
        zero_row.addWidget(self.sendInfo)
        self.sendInfo.setProperty("channel", "loc://{\"name\":\"sol\"}")
        #self.sendInfo.set_display()

        self.PyDMLabel = PyDMPushButton()
        zero_row.addWidget(self.PyDMLabel)
        self.PyDMLabel.channel = "loc://{\"name\":\"sol\",\"type\":\"str\",\"init\":\"0\"}"
        #self.PyDMLabel.displayFormat = "str"
        #self.PyDMLabel.showUnits = True

        self.three = QPushButton()
        three_row.addWidget(self.three)

        self.three.setText("3")
        self.three.clicked.connect(lambda: self.num(self.three))

        self.zero = QPushButton()
        four_row.addWidget(self.zero)

        self.zero.setText("0")
        self.zero.clicked.connect(lambda: self.num(self.zero))

        self.pushButton_9 = QPushButton()
        two_row.addWidget(self.pushButton_9)

        self.pushButton_9.setText("4")
        self.pushButton_9.clicked.connect(lambda: self.num(self.pushButton_9))

        self.pushButton_2 = QPushButton()
        zero_row.addWidget(self.pushButton_2)

        self.pushButton_2.setText("AC")
        self.pushButton_2.clicked.connect(lambda: self.num(self.pushButton_2))

        self.pushButton_4 = QPushButton()
        zero_row.addWidget(self.pushButton_4)

        self.pushButton_4.setText("/")
        self.pushButton_4.clicked.connect(lambda: self.num(self.pushButton_4))

        self.pushButton_5 = QPushButton()
        one_row.addWidget(self.pushButton_5)

        self.pushButton_5.setText("7")
        self. pushButton_5.clicked.connect(lambda: self.num(self.pushButton_5))

        self.pushButton_6 = QPushButton()
        one_row.addWidget(self.pushButton_6)

        self.pushButton_6.setText("8")
        self.pushButton_6.clicked.connect(lambda: self.num(self.pushButton_6))

        self.pushButton_16 = QPushButton()
        four_row.addWidget(self.pushButton_16)

        self.pushButton_16.setText(".")
        self.pushButton_16.clicked.connect(lambda: self.num(self.pushButton_16))

        self.pushButton_18 = QPushButton()
        four_row.addWidget(self.pushButton_18)

        self.pushButton_18.setText("=")
        self.pushButton_18.clicked.connect(lambda: self.num(self.pushButton_18))

        self.pushButton_7 = QPushButton()
        one_row.addWidget(self.pushButton_7)

        self.pushButton_7.setText("9")
        self.pushButton_7.clicked.connect(lambda: self.num(self.pushButton_7))

        self.pushButton_15 = QPushButton()
        three_row.addWidget(self.pushButton_15)

        self.pushButton_15.setText("2")
        self.pushButton_15.clicked.connect(lambda: self.num(self.pushButton_15))

        self.pushButton_13 = QPushButton()
        three_row.addWidget(self.pushButton_13)

        self.pushButton_13.setText("1")
        self.pushButton_13.clicked.connect(lambda: self.num(self.pushButton_13))

        self.five = QPushButton()
        two_row.addWidget(self.five)

        self.five.setText("5")
        self.five.clicked.connect(lambda: self.num(self.five))

        self.six = QPushButton()
        two_row.addWidget(self.six)

        self.six.setText("6")
        self.six.clicked.connect(lambda: self.num(self.six))

        self.pushButton_12 = QPushButton()
        two_row.addWidget(self.pushButton_12)

        self.pushButton_12.setText("-")
        self.pushButton_12.clicked.connect(lambda: self.num(self.pushButton_12))

        self.pushButton_19 = QPushButton()
        three_row.addWidget(self.pushButton_19)

        self.pushButton_19.setText("+")
        self.pushButton_19.clicked.connect(lambda: self.num(self.pushButton_19))

        self.pushButton_8 = QPushButton()
        one_row.addWidget(self.pushButton_8)

        self.pushButton_8.setText("*")
        self.pushButton_8.clicked.connect(lambda: self.num(self.pushButton_8))

    def num(self, button):
        text = button.text()

        if text == "=":
            solution = eval(self.calculation)
            self.sendInfo.setText(str(solution))
            print("updated", solution)
            self.calculation = solution
        elif text == "AC":
            self.calcuation = None
            solution = 0
            self.lcdNumber.setText('0')
        elif self.calculation == None:
            self.calculation = text
            self.lcdNumber.setText(self.calculation)
        else:
            self.calculation = str(self.calculation) + str(text)
            self.lcdNumber.setText(self.calculation)


