from .qtplugin_base import qtplugin_factory
from .led import PyDMLed

PyDMLedPlugin = qtplugin_factory(PyDMLed)