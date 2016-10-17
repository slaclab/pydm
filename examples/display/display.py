#!/usr/local/lcls/package/python/current/bin/python

# Try PyQt5
try:
    pyqt5 = True
    from PyQt5 import QtCore, QtGui
    from display_ui5 import Ui_MainWindow

except ImportError:
    pyqt5 =  False
    # Imports for Pyqt4
    from PyQt4 import QtCore, QtGui
    from display_ui import Ui_MainWindow

import sys, os
from pydm import PyDMApplication

class DisplayWindow(QtGui.QMainWindow):
	def __init__(self, parent=None):
		QtGui.QMainWindow.__init__(self, parent)
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)

if __name__ == "__main__":
	app = PyDMApplication(sys.argv)
	window = DisplayWindow()
	window.show()
	app.start_connections()
	sys.exit(app.exec_())
