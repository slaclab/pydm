from . import qtlib
QT_LIB = qtlib.QT_LIB
if QT_LIB == 'PyQt5':
    from PyQt5.QtCore import *
    from PyQt5.QtCore import qInstallMessageHandler as qInstallMsgHandler
    Signal = pyqtSignal
    Slot = pyqtSlot
    Property = pyqtProperty
