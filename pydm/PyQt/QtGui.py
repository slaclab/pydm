from . import qtlib
QT_LIB = qtlib.QT_LIB

from qtpy.QtGui import *
from qtpy.QtWidgets import *
#Crappy work around:  QItemSelection exists in QtGui for PyQt4 but QtCore for PyQt5.  We'll make it available in both.
from qtpy.QtCore import QItemSelection
