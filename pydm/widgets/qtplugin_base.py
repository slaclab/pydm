"""Module to define a parent qtdesigner plugin class.

Please continue to name your qtdesigner plugin modules using the convention
modulename.py          <--- defines the widget
modulename_qtplugin.py <--- imports this module + the widget

However, a majority of the builtin plugins are defined in qtplugins.py
adjacent to this module.

NOTE: PyDMDesignerPlugin is a valid plugin, so designer will try to pick it up
      and instantiate it if you import it into another module's namespace. You
      will need to avoid having it present in the global namespace of any
      module that defines a qtplugin.

If you do not heed this warning, you will get a one-line traceback:
TypeError: __init__() takes exactly 3 arguments (1 given)
for each PyDMDesignerPlugin that Qt Designer tries to use. This will not
affect any of your widgets, but it will be annoying.

"""

import enum
import inspect
import logging
from typing import Dict, List, Optional, Type

import entrypoints
from qtpy import QtCore, QtDesigner, QtGui, QtWidgets

from pydm import config
from pydm.qtdesigner import DesignerHooks
from .qtplugin_extensions import PyDMExtensionFactory

logger = logging.getLogger(__name__)


class WidgetCategory(str, enum.Enum):
    """Categories for PyDM Widgets in the Qt Designer."""

    #: Widgets which can contain other widgets.
    CONTAINER = "PyDM Container Widgets"
    #: Widgets which contain displays.
    DISPLAY = "PyDM Display Widgets"
    #: Widgets which take user input.
    INPUT = "PyDM Input Widgets"
    #: Widgets which plot data.
    PLOT = "PyDM Plot Widgets"
    #: Widgets which draw things.
    DRAWING = "PyDM Drawing Widgets"
    #: Widgets which don't fit into any other category.
    MISC = "PyDM Misc. Widgets"


def qtplugin_factory(
    cls: Type[QtWidgets.QWidget],
    is_container: bool = False,
    group: str = "PyDM Widgets",
    extensions: Optional[List[Type]] = None,
    icon: Optional[QtGui.QIcon] = None,
) -> Type["PyDMDesignerPlugin"]:
    """
    Helper function to create a generic PyDMDesignerPlugin class.

    Parameters
    ----------
    cls : QWidget subclass
        The widget class.

    is_container : bool, optional
        True if this widget can contain other widgets (as in a Frame).
        This will also affect whether or not the widget can be used as the
        top-level widget of a display. Defaults to False.

    extensions : list of extension classes, optional
        Extension classes to use with the widget.

    icon : QtGui.QIcon, optional
        An icon to use with the widget in the designer.  Consider using
        the PyDM-provided fontawesome ``ifont`` here for simplicity.
    """

    class Plugin(PyDMDesignerPlugin):
        __doc__ = "PyDMDesigner Plugin for {}".format(cls.__name__)

        def __init__(self):
            super().__init__(cls, is_container, group, extensions, icon)

    return Plugin


class PyDMDesignerPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
    """
    Parent class to standardize how pydm plugins are accessed in qt designer.
    All functions have default returns that can be overridden as necessary.
    """

    def __init__(
        self,
        cls: Type[QtWidgets.QWidget],
        is_container: bool = False,
        group: str = "PyDM Widgets",
        extensions: Optional[List[Type]] = None,
        icon: Optional[QtGui.QIcon] = None,
    ):
        """
        Set up the plugin using the class info in cls

        :param cls: Class of the widget to use
        :type cls:  QWidget
        """
        QtDesigner.QPyDesignerCustomWidgetPlugin.__init__(self)
        self.initialized = False
        self.is_container = is_container
        self.cls = cls
        self._group = group

        if icon is None and QtWidgets.QApplication.instance() is not None:
            get_designer_icon = getattr(cls, "get_designer_icon", None)
            if get_designer_icon is not None:
                icon = get_designer_icon()

            if icon is None:
                icon = QtGui.QIcon()

        self._icon = icon
        self.extensions = extensions
        self.manager = None

    def initialize(self, core):
        """
        Override this function if you need special initialization instructions.
        Make sure you don't neglect to set the self.initialized flag to True
        after a successful initialization.

        :param core: form editor interface to use in the initialization
        :type core:  QDesignerFormEditorInterface
        """
        if self.initialized:
            return

        self.initialized = True

        designer_hooks = DesignerHooks()
        designer_hooks.form_editor = core

        if self.extensions is not None and len(self.extensions) > 0:
            self.manager = core.extensionManager()
            if self.manager:
                factory = PyDMExtensionFactory(parent=self.manager)
                self.manager.registerExtensions(factory, "org.qt-project.Qt.Designer.TaskMenu")  # Qt5

    def isInitialized(self):
        """
        Return True if initialize function has been called successfully.
        """
        return self.initialized

    def createWidget(self, parent):
        """
        Instantiate a widget with the given parent.

        :param parent: Parent widget of instantiated widget
        :type parent:  QWidget
        """
        w = self.cls(parent=parent)
        try:
            setattr(w, "extensions", self.extensions)
            w.init_for_designer()
        except (AttributeError, NameError):
            pass
        return w

    def name(self):
        """
        Return the class name of the widget.
        """
        return self.cls.__name__

    def group(self):
        """
        Return a common group name so all PyDM Widgets are together in
        Qt Designer.
        """
        return self._group

    def toolTip(self):
        """
        A short description to pop up on mouseover. If we leave this as an
        empty string, we'll have no tooltip by default and can override this
        on a case-by-case basis.
        """
        return ""

    def whatsThis(self):
        """
        A longer description of the widget for Qt Designer. By default, this
        is the entire class docstring.
        """
        return ""

    def isContainer(self):
        """
        Return True if this widget can contain other widgets.
        """
        return self.is_container

    def icon(self):
        """
        Return a QIcon to represent this widget in Qt Designer.
        """
        return QtGui.QIcon(self._icon.pixmap(QtCore.QSize(32, 32)))

    def domXml(self):
        """
        XML Description of the widget's properties.
        """
        return (
            '<widget class="{0}" name="{0}">\n'
            ' <property name="toolTip" >\n'
            "  <string>{1}</string>\n"
            " </property>\n"
            "</widget>\n"
        ).format(self.name(), self.toolTip())

    def includeFile(self):
        """
        Include the class module for the generated qt code
        """
        return self.cls.__module__


def create_designer_widget_from_widget(
    widget_cls: Type[QtWidgets.QWidget],
) -> Type[PyDMDesignerPlugin]:
    """
    Get a designable widget class.

    Accepts either user-provided :class:`PyDMDesignerPlugin` subclasses or
    :class:`QWidget` subclasses.

    In the case of :class:`QWidget` subclasses, designer-specific settings
    may be specified on a class attribute.  These arguments should match
    what :func:`qtplugin_factory` expects.
    """
    if not inspect.isclass(widget_cls):
        raise ValueError(f"Expected a class, got a {type(widget_cls).__name__}")
    if issubclass(widget_cls, PyDMDesignerPlugin):
        return widget_cls
    if issubclass(widget_cls, QtWidgets.QWidget):
        designer_kwargs = getattr(widget_cls, "_qt_designer_", None) or {}
        return qtplugin_factory(widget_cls, **designer_kwargs)

    raise ValueError(f"Expected a PyDMDesignerPlugin or a QWidget subclass, got a {type(widget_cls).__name__}")


def get_widgets_from_entrypoints(key: str = config.ENTRYPOINT_WIDGET) -> Dict[str, Type[PyDMDesignerPlugin]]:
    """
    Get all widgets from entrypoint definitions.

    Parameters
    ----------
    key : str, optional
        The entrypoint key.  Defaults to ``pydm.config.ENTRYPOINT_WIDGET``.

    Returns
    -------
    widgets : dict
        Dictionary of class name to ``PyDMDesignerPlugin`` subclass.
    """
    widgets = {}
    for entry in entrypoints.get_group_all(key):
        logger.debug("Found widget from entrypoint: %s", entry.name)
        try:
            plugin_cls = entry.load()
        except Exception as ex:
            logger.exception("Failed to load %s entry %s: %s", key, entry.name, ex)
            continue

        try:
            designer_widget = create_designer_widget_from_widget(plugin_cls)
        except Exception:
            logger.warning("Invalid widget class specified in entrypoint %s: %s", entry.name, plugin_cls)
        else:
            widgets[entry.name] = designer_widget

    return widgets
