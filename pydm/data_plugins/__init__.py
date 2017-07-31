import os
import inspect
import importlib
import warnings
from .plugin import PyDMPlugin

#This code gets all .py files in the same directory that this file lives (data_plugins),
#finds the ones that have PyDMPlugin subclasses, and adds them to a list of modules.
#In principle, you should be able to add a new plugin just by putting a new file in this directory.

#PyDMApplication uses the plugin_modules list to create an instance of each plugin.

plugin_dir = os.path.dirname(os.path.realpath(__file__))
filenames = [os.path.splitext(f)[0] for f in os.listdir(plugin_dir) if os.path.splitext(f)[1] == ".py" and os.path.splitext(f)[0] != "__init__"]

plugin_modules = []
for filename in filenames:
  try:
    module = importlib.import_module("." + filename, "pydm.data_plugins")
  except NameError as e:
    warnings.warn("Unable to import plugin file {}. This plugin will be skipped.  The exception raised was: {}".format(filename, e), RuntimeWarning, stacklevel=2)
  classes = [obj for name, obj in inspect.getmembers(module) if inspect.isclass(obj) and issubclass(obj, PyDMPlugin) and obj is not PyDMPlugin]
  #De-duplicate classes.
  classes = list(set(classes))
  if len(classes) == 0:
    continue
  if len(classes) > 1:
    warnings.warn("More than one PyDMPlugin subclass in file {}. The first occurence (in alphabetical order) will be opened: {}".format(filename, classes[0].__name__), RuntimeWarning, stacklevel=0)
  plugin = classes[0]
  if plugin.protocol is not None:
    if plugin.protocol in plugin_modules and plugin_modules[plugin.protocol] != plugin:
      warnings.warn("More than one plugin is attempting to register the {protocol} protocol. Which plugin will get called to handle this protocol is undefined.".format(protocol=plugin.protocol, plugin=plugin.__name__), RuntimeWarning, stacklevel=0)
    plugin_modules.append(plugin)