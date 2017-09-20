# -*- coding: utf-8 -*-

# This file was originally constructed in Designer from the
# pydm.ui file, and converted to python via pyuic4. However,
# to maintain compatibility with both PyQt4 and PyQt5,
# the output file must be modified by hand to change the
# import statements to import the PyQt compatibility layer
# from .PyQt.  If you use pyuic to change this file, you MUST
# edit by hand to re-include this message and the following
# import line.
from .PyQt import QtCore, QtGui

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
        MainWindow.resize(619, 89)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSizeConstraint(QtGui.QLayout.SetMaximumSize)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 619, 22))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        self.menuView = QtGui.QMenu(self.menubar)
        self.menuView.setObjectName(_fromUtf8("menuView"))
        self.menuHistory = QtGui.QMenu(self.menubar)
        self.menuHistory.setObjectName(_fromUtf8("menuHistory"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.navbar = QtGui.QToolBar(MainWindow)
        self.navbar.setMovable(False)
        self.navbar.setFloatable(False)
        self.navbar.setObjectName(_fromUtf8("navbar"))
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.navbar)
        self.actionEdit_in_Designer = QtGui.QAction(MainWindow)
        self.actionEdit_in_Designer.setObjectName(_fromUtf8("actionEdit_in_Designer"))
        self.actionAbout_PyDM = QtGui.QAction(MainWindow)
        self.actionAbout_PyDM.setEnabled(False)
        self.actionAbout_PyDM.setObjectName(_fromUtf8("actionAbout_PyDM"))
        self.actionReload_Display = QtGui.QAction(MainWindow)
        self.actionReload_Display.setObjectName(_fromUtf8("actionReload_Display"))
        self.actionIncrease_Font_Size = QtGui.QAction(MainWindow)
        self.actionIncrease_Font_Size.setObjectName(_fromUtf8("actionIncrease_Font_Size"))
        self.actionDecrease_Font_Size = QtGui.QAction(MainWindow)
        self.actionDecrease_Font_Size.setObjectName(_fromUtf8("actionDecrease_Font_Size"))
        self.actionShow_File_Path_in_Title_Bar = QtGui.QAction(MainWindow)
        self.actionShow_File_Path_in_Title_Bar.setCheckable(True)
        self.actionShow_File_Path_in_Title_Bar.setObjectName(_fromUtf8("actionShow_File_Path_in_Title_Bar"))
        self.actionBack = QtGui.QAction(MainWindow)
        self.actionBack.setObjectName(_fromUtf8("actionBack"))
        self.actionForward = QtGui.QAction(MainWindow)
        self.actionForward.setObjectName(_fromUtf8("actionForward"))
        self.actionHome = QtGui.QAction(MainWindow)
        self.actionHome.setObjectName(_fromUtf8("actionHome"))
        self.actionShow_Navigation_Bar = QtGui.QAction(MainWindow)
        self.actionShow_Navigation_Bar.setCheckable(True)
        self.actionShow_Navigation_Bar.setObjectName(_fromUtf8("actionShow_Navigation_Bar"))
        self.menuFile.addAction(self.actionAbout_PyDM)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionEdit_in_Designer)
        self.menuFile.addAction(self.actionReload_Display)
        self.menuView.addAction(self.actionIncrease_Font_Size)
        self.menuView.addAction(self.actionDecrease_Font_Size)
        self.menuView.addAction(self.actionShow_File_Path_in_Title_Bar)
        self.menuView.addAction(self.actionShow_Navigation_Bar)
        self.menuHistory.addAction(self.actionBack)
        self.menuHistory.addAction(self.actionForward)
        self.menuHistory.addAction(self.actionHome)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuHistory.menuAction())
        self.navbar.addAction(self.actionBack)
        self.navbar.addAction(self.actionForward)
        self.navbar.addSeparator()
        self.navbar.addAction(self.actionHome)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "PyDM Main Window", None))
        self.menuFile.setTitle(_translate("MainWindow", "File", None))
        self.menuView.setTitle(_translate("MainWindow", "View", None))
        self.menuHistory.setTitle(_translate("MainWindow", "History", None))
        self.navbar.setWindowTitle(_translate("MainWindow", "toolBar", None))
        self.actionEdit_in_Designer.setText(_translate("MainWindow", "Edit in Designer", None))
        self.actionAbout_PyDM.setText(_translate("MainWindow", "About PyDM", None))
        self.actionReload_Display.setText(_translate("MainWindow", "Reload Display", None))
        self.actionReload_Display.setShortcut(_translate("MainWindow", "Ctrl+R", None))
        self.actionIncrease_Font_Size.setText(_translate("MainWindow", "Increase Font Size", None))
        self.actionIncrease_Font_Size.setShortcut(_translate("MainWindow", "Ctrl+=", None))
        self.actionDecrease_Font_Size.setText(_translate("MainWindow", "Decrease Font Size", None))
        self.actionDecrease_Font_Size.setShortcut(_translate("MainWindow", "Ctrl+-", None))
        self.actionShow_File_Path_in_Title_Bar.setText(_translate("MainWindow", "Show File Path in Title Bar", None))
        self.actionBack.setText(_translate("MainWindow", "Back", None))
        self.actionBack.setShortcut(_translate("MainWindow", "Ctrl+Left", None))
        self.actionForward.setText(_translate("MainWindow", "Forward", None))
        self.actionForward.setShortcut(_translate("MainWindow", "Ctrl+Right", None))
        self.actionHome.setText(_translate("MainWindow", "Home", None))
        self.actionHome.setShortcut(_translate("MainWindow", "Ctrl+Shift+H", None))
        self.actionShow_Navigation_Bar.setText(_translate("MainWindow", "Show Navigation Bar", None))

