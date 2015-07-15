# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'display.ui'
#
# Created: Thu Jul  9 21:31:48 2015
#      by: PyQt4 UI code generator 4.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
from pydm import PyDMLabel
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(482, 416)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.formLayout = QtGui.QFormLayout(self.centralwidget)
        self.formLayout.setFormAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.pvLabel1 = PyDMLabel("ca://BPMS:MATT:1:XTH", self.centralwidget)
        self.pvLabel1.setAutoFillBackground(False)
        self.pvLabel1.setObjectName(_fromUtf8("pvLabel1"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.pvLabel1)
        self.label_2 = QtGui.QLabel(self.centralwidget)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_2)
        self.pvLabel2 = PyDMLabel("ca://BPMS:MATT:2:XTH", self.centralwidget)
        self.pvLabel2.setObjectName(_fromUtf8("pvLabel2"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.pvLabel2)
        self.label_3 = QtGui.QLabel(self.centralwidget)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label_3)
        self.pvLabel3 = PyDMLabel("ca://BPMS:MATT:3:XTH", self.centralwidget)
        self.pvLabel3.setObjectName(_fromUtf8("pvLabel3"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.pvLabel3)
        self.label_4 = QtGui.QLabel(self.centralwidget)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.label_4)
        self.pvLabel4 = PyDMLabel("ca://BPMS:MATT:4:XTH", self.centralwidget)
        self.pvLabel4.setObjectName(_fromUtf8("pvLabel4"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.pvLabel4)
        self.label_5 = QtGui.QLabel(self.centralwidget)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.LabelRole, self.label_5)
        self.pvLabel5 = PyDMLabel("ca://BPMS:MATT:5:XTH", self.centralwidget)
        self.pvLabel5.setObjectName(_fromUtf8("pvLabel5"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.pvLabel5)
        self.label_6 = QtGui.QLabel(self.centralwidget)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.LabelRole, self.label_6)
        self.pvLabel6 = PyDMLabel("ca://BPMS:MATT:6:XTH", self.centralwidget)
        self.pvLabel6.setObjectName(_fromUtf8("pvLabel6"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.FieldRole, self.pvLabel6)
        self.label_7 = QtGui.QLabel(self.centralwidget)
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.formLayout.setWidget(6, QtGui.QFormLayout.LabelRole, self.label_7)
        self.pvLabel7 = PyDMLabel("ca://BPMS:MATT:7:XTH", self.centralwidget)
        self.pvLabel7.setObjectName(_fromUtf8("pvLabel7"))
        self.formLayout.setWidget(6, QtGui.QFormLayout.FieldRole, self.pvLabel7)
        self.label_8 = QtGui.QLabel(self.centralwidget)
        self.label_8.setObjectName(_fromUtf8("label_8"))
        self.formLayout.setWidget(7, QtGui.QFormLayout.LabelRole, self.label_8)
        self.pvLabel8 = PyDMLabel("ca://BPMS:MATT:8:XTH", self.centralwidget)
        self.pvLabel8.setObjectName(_fromUtf8("pvLabel8"))
        self.formLayout.setWidget(7, QtGui.QFormLayout.FieldRole, self.pvLabel8)
        self.label_9 = QtGui.QLabel(self.centralwidget)
        self.label_9.setObjectName(_fromUtf8("label_9"))
        self.formLayout.setWidget(8, QtGui.QFormLayout.LabelRole, self.label_9)
        self.pvLabel9 = PyDMLabel("ca://BPMS:MATT:9:XTH", self.centralwidget)
        self.pvLabel9.setObjectName(_fromUtf8("pvLabel9"))
        self.formLayout.setWidget(8, QtGui.QFormLayout.FieldRole, self.pvLabel9)
        self.label_10 = QtGui.QLabel(self.centralwidget)
        self.label_10.setObjectName(_fromUtf8("label_10"))
        self.formLayout.setWidget(9, QtGui.QFormLayout.LabelRole, self.label_10)
        self.pvLabel10 = PyDMLabel("ca://BPMS:MATT:10:XTH", self.centralwidget)
        self.pvLabel10.setObjectName(_fromUtf8("pvLabel10"))
        self.formLayout.setWidget(9, QtGui.QFormLayout.FieldRole, self.pvLabel10)
				
        self.label_11 = QtGui.QLabel(self.centralwidget)
        self.label_11.setObjectName(_fromUtf8("label_11"))
        self.formLayout.setWidget(10, QtGui.QFormLayout.LabelRole, self.label_11)
        self.pvLabel11 = PyDMLabel("fake://faketest", self.centralwidget)
        self.pvLabel11.setObjectName(_fromUtf8("pvLabel11"))
        self.formLayout.setWidget(10, QtGui.QFormLayout.FieldRole, self.pvLabel11)
				
				
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 482, 22))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "Python Display Manager Proof-of-Concept", None))
        self.label.setText(_translate("MainWindow", "BPMS:MATT:1:XTH", None))
        self.pvLabel1.setText(_translate("MainWindow", "TextLabel", None))
        self.label_2.setText(_translate("MainWindow", "BPMS:MATT:2:XTH", None))
        self.pvLabel2.setText(_translate("MainWindow", "TextLabel", None))
        self.label_3.setText(_translate("MainWindow", "BPMS:MATT:3:XTH", None))
        self.pvLabel3.setText(_translate("MainWindow", "TextLabel", None))
        self.label_4.setText(_translate("MainWindow", "BPMS:MATT:4:XTH", None))
        self.pvLabel4.setText(_translate("MainWindow", "TextLabel", None))
        self.label_5.setText(_translate("MainWindow", "BPMS:MATT:5:XTH", None))
        self.pvLabel5.setText(_translate("MainWindow", "TextLabel", None))
        self.label_6.setText(_translate("MainWindow", "BPMS:MATT:6:XTH", None))
        self.pvLabel6.setText(_translate("MainWindow", "TextLabel", None))
        self.label_7.setText(_translate("MainWindow", "BPMS:MATT:7:XTH", None))
        self.pvLabel7.setText(_translate("MainWindow", "TextLabel", None))
        self.label_8.setText(_translate("MainWindow", "BPMS:MATT:8:XTH", None))
        self.pvLabel8.setText(_translate("MainWindow", "TextLabel", None))
        self.label_9.setText(_translate("MainWindow", "BPMS:MATT:9:XTH", None))
        self.pvLabel9.setText(_translate("MainWindow", "TextLabel", None))
        self.label_10.setText(_translate("MainWindow", "BPMS:MATT:10:XTH", None))
        self.pvLabel10.setText(_translate("MainWindow", "TextLabel", None))
        self.label_11.setText(_translate("MainWindow", "Fake Protocol", None))
        self.pvLabel11.setText(_translate("MainWindow", "TextLabel", None))

