from qtpy import QtWidgets, QtGui, QtCore


def install_connection_inspector(parent, keys=None):
    """
    Install a QShortcut at the application which opens the PyDM Connection
    Inspector

    Parameters
    ----------
    parent : QWidget
        A shortcut is "listened for" by Qt's event loop when the shortcut's
        parent widget is receiving events.
    keys : QKeySequence, optional
        Default value is `Alt+C`
    """
    from pydm.connection_inspector import ConnectionInspector

    def show_inspector():
        c = ConnectionInspector(parent=parent)
        c.show()

    parent = parent or QtWidgets.QApplication.desktop()

    if keys is None:
        keys = QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_C)
    shortcut = QtWidgets.QShortcut(keys, parent);
    shortcut.setContext(QtCore.Qt.ApplicationShortcut)
    shortcut.activated.connect(show_inspector)
