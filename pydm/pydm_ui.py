# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'pydm.ui'
#
# Created: Thu Aug  6 16:06:42 2015
#      by: PyQt4 UI code generator 4.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

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
        MainWindow.resize(504, 113)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSizeConstraint(QtGui.QLayout.SetMaximumSize)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.panelSearchLineEdit = QtGui.QLineEdit(self.centralwidget)
        self.panelSearchLineEdit.setMinimumSize(QtCore.QSize(150, 0))
        self.panelSearchLineEdit.setObjectName(_fromUtf8("panelSearchLineEdit"))
        self.horizontalLayout.addWidget(self.panelSearchLineEdit)
        self.goButton = QtGui.QPushButton(self.centralwidget)
        self.goButton.setObjectName(_fromUtf8("goButton"))
        self.horizontalLayout.addWidget(self.goButton)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.backButton = QtGui.QPushButton(self.centralwidget)
        self.backButton.setObjectName(_fromUtf8("backButton"))
        self.horizontalLayout.addWidget(self.backButton)
        self.forwardButton = QtGui.QPushButton(self.centralwidget)
        self.forwardButton.setObjectName(_fromUtf8("forwardButton"))
        self.horizontalLayout.addWidget(self.forwardButton)
        self.homeButton = QtGui.QPushButton(self.centralwidget)
        self.homeButton.setObjectName(_fromUtf8("homeButton"))
        self.horizontalLayout.addWidget(self.homeButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.line = QtGui.QFrame(self.centralwidget)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.verticalLayout.addWidget(self.line)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 504, 22))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.actionEdit_in_Designer = QtGui.QAction(MainWindow)
        self.actionEdit_in_Designer.setObjectName(_fromUtf8("actionEdit_in_Designer"))
        self.actionSave_Screenshot = QtGui.QAction(MainWindow)
        self.actionSave_Screenshot.setObjectName(_fromUtf8("actionSave_Screenshot"))
        self.actionAbout_DIM = QtGui.QAction(MainWindow)
        self.actionAbout_DIM.setObjectName(_fromUtf8("actionAbout_DIM"))
        self.menuFile.addAction(self.actionAbout_DIM)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionEdit_in_Designer)
        self.menuFile.addAction(self.actionSave_Screenshot)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "PyDM Main Window", None))
        self.panelSearchLineEdit.setPlaceholderText(_translate("MainWindow", "Search for a display...", None))
        self.goButton.setText(_translate("MainWindow", "Go", None))
        self.backButton.setText(_translate("MainWindow", "Back", None))
        self.forwardButton.setText(_translate("MainWindow", "Forward", None))
        self.homeButton.setText(_translate("MainWindow", "Home", None))
        self.menuFile.setTitle(_translate("MainWindow", "File", None))
        self.actionEdit_in_Designer.setText(_translate("MainWindow", "Edit in Designer", None))
        self.actionSave_Screenshot.setText(_translate("MainWindow", "Save Screenshot", None))
        self.actionAbout_DIM.setText(_translate("MainWindow", "About PyDM", None))

