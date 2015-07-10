#!/usr/local/lcls/package/python/current/bin/python

import sys, os
from PyQt4 import QtCore, QtGui
from display_ui import Ui_MainWindow
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
