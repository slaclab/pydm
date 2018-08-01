from . import qtlib
QT_LIB = qtlib.QT_LIB

from qtpy.QtCore import *
from qtpy.QtCore import qInstallMessageHandler as qInstallMsgHandler
QT_VERSION_STR = qVersion()
# for back compat
pyqtSignal = Signal
pyqtSlot = Slot
pyqtProperty = Property
