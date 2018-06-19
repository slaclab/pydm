from . import qtlib
QT_LIB = qtlib.QT_LIB
if QT_LIB == 'PyQt5':
    from PyQt5.uic import *
