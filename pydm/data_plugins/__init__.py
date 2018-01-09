import os
import sys
import inspect
import imp
import uuid
import warnings
import platform
from .plugin import PyDMPlugin

# This code gets all *_plugin.py files in the same directory that this file lives (data_plugins),
# finds the ones that have PyDMPlugin subclasses, and adds them to a list of modules.
# In principle, you should be able to add a new plugin just by putting a new file in this directory.

# PyDMApplication uses the plugin_modules list to create an instance of each plugin.

plugin_dir = os.path.dirname(os.path.realpath(__file__))
plugin_modules = []

"""
Loads all the data plugins available at the given
PYDM_DATA_PLUGINS_PATH environment variable and subfolders that
follows the *_plugin.py and have classes that inherits from
the pydm.data_plugins.PyDMPlugin class.
"""
DATA_PLUGIN_TOKEN = "_plugin.py"
path = os.getenv("PYDM_DATA_PLUGINS_PATH", None)
if path is None:
    locations = []
else:
    locations = path.split(os.pathsep)

# Ensure that we first visit the local data_plugins location
locations.insert(0, plugin_dir)

print("*"*80)
print("* Loading PyDM Data Plugins")
print("*"*80)

for loc in locations:
    for root, _, files in os.walk(loc):
        if root.split(os.path.sep)[-1].startswith("__"):
            continue

        print("Looking for PyDM Data Plugins at: {}".format(root))
        for name in files:
            if name.endswith(DATA_PLUGIN_TOKEN):
                try:
                    print("\tTrying to load {}...".format(name))
                    sys.path.append(root)
                    temp_name = str(uuid.uuid4())
                    module = imp.load_source(temp_name, os.path.join(root, name))
                except Exception as e:
                    warnings.warn("Unable to import plugin file {}. This plugin will be skipped.    The exception raised was: {}".format(name, e), RuntimeWarning, stacklevel=2)
                classes = [obj for name, obj in inspect.getmembers(module) if inspect.isclass(obj) and issubclass(obj, PyDMPlugin) and obj is not PyDMPlugin]
                # De-duplicate classes.
                classes = list(set(classes))
                if len(classes) == 0:
                    continue
                if len(classes) > 1:
                    warnings.warn("More than one PyDMPlugin subclass in file {}. The first occurrence (in alphabetical order) will be opened: {}".format(name, classes[0].__name__), RuntimeWarning, stacklevel=0)
                plugin = classes[0]
                if plugin.protocol is not None:
                    if plugin.protocol in plugin_modules and plugin_modules[plugin.protocol] != plugin:
                        warnings.warn("More than one plugin is attempting to register the {protocol} protocol. Which plugin will get called to handle this protocol is undefined.".format(protocol=plugin.protocol, plugin=plugin.__name__), RuntimeWarning, stacklevel=0)
                    plugin_modules.append(plugin)
