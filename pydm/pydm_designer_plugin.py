print("Loading PyDM Widgets")

from pydm.utilities import ACTIVE_QT_WRAPPER, QtWrapperTypes

if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYQT5:
    from pydm.widgets.qtplugins import *  # noqa: E402, F403
elif ACTIVE_QT_WRAPPER == QtWrapperTypes.PYSIDE6:
    from pydm.widgets import qtplugins

    from PySide6.QtDesigner import QDesignerCustomWidgetInterface, QPyDesignerCustomWidgetCollection

    import inspect

    for _, value in inspect.getmembers(qtplugins):
        if inspect.isclass(value) and issubclass(value, QDesignerCustomWidgetInterface):
            QPyDesignerCustomWidgetCollection.addCustomWidget(value())
