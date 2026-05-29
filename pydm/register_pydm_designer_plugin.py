print("Loading PyDM Widgets")

from pydm.utilities import ACTIVE_QT_WRAPPER, QtWrapperTypes
from pydm.widgets.qtplugins import get_all_custom_widgets_in_order


if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYQT5:
    globals().update({pl.plugin_name: pl for pl in get_all_custom_widgets_in_order()})

elif ACTIVE_QT_WRAPPER == QtWrapperTypes.PYSIDE6:
    from PySide6.QtDesigner import QDesignerCustomWidgetInterface, QPyDesignerCustomWidgetCollection

    import inspect

    for value in get_all_custom_widgets_in_order():
        if inspect.isclass(value) and issubclass(value, QDesignerCustomWidgetInterface):
            QPyDesignerCustomWidgetCollection.addCustomWidget(value())
