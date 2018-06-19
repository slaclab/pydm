import os, sys

QT_LIB = os.getenv("PYDM_QT_LIB")

if QT_LIB is None:
    #NOTE: If lib_order doesn't match the order in which pyqtgraph tries to import pyqt, both can get imported, and you'll start getting RuntimeErrors mentioning something about PyQt4 and PyQt5 both wrapping QObject.
    lib_order = ['PyQt5']
    for lib in lib_order:
        if lib in sys.modules:
            QT_LIB = lib
            break

if QT_LIB is None:
    for lib in lib_order:
        try:
            __import__(lib)
            QT_LIB = lib
            break
        except ImportError:
            pass

if QT_LIB is None:
    raise Exception("PyDM requires PyQt5 and it could not be imported.")
if QT_LIB == 'PyQt4':
    raise Exception("PyDM no longer supports PyQt4. "
                    "Please update to PyQt5 and try again.")
