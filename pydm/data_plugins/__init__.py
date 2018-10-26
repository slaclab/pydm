"""
Loads all the data plugins available at the given PYDM_DATA_PLUGINS_PATH
environment variable and subfolders that follows the *_plugin.py and have
classes that inherits from the pydm.data_plugins.PyDMPlugin class.
"""
import os
import sys
import inspect
import logging
import imp
import uuid
from .plugin import PyDMPlugin
from ..utilities import protocol_and_address
from .. import config

logger = logging.getLogger(__name__)
plugin_modules = {}
__read_only = False


def plugin_for_address(address):
    """
    Find the correct PyDMPlugin for a channel
    """
    # Check for a configured protocol
    protocol, addr = protocol_and_address(address)
    # Use default protocol
    if protocol is None and config.DEFAULT_PROTOCOL is not None:
        logger.debug("Using default protocol %s for %s",
                     config.DEFAULT_PROTOCOL, address)
        # If no protocol was specified, and the default protocol
        # environment variable is specified, try to use that instead.
        protocol = config.DEFAULT_PROTOCOL
    # Load proper plugin module
    if protocol:
        try:
            return plugin_modules[str(protocol)]
        except KeyError as exc:
            logger.exception("Could not find protocol for %r", address)
    # Catch all in case of improper plugin specification
    logger.error("Channel {addr} did not specify a valid protocol "
                 "and no default protocol is defined. This channel "
                 "will receive no data. To specify a default protocol, "
                 "set the PYDM_DEFAULT_PROTOCOL environment variable."
                 "".format(addr=address))
    return None


def add_plugin(plugin):
    """
    Add a PyDM plugin to the global registry of protocol vs. plugins

    Parameters
    ----------
    plugin: PyDMPlugin
        The class of plugin to instantiate
    """
    # Warn users if we are overwriting a protocol which already has a plugin
    if plugin.protocol in plugin_modules:
        logger.warning("Replacing %s plugin with %s for use with protocol %s",
                       plugin, plugin_modules[plugin.protocol],
                       plugin.protocol)
    plugin_modules[plugin.protocol] = plugin()


def load_plugins_from_path(locations, token):
    """
    Load plugins from file locations that match a specific token


    Parameters
    ----------
    locations: list
        List of file locations

    token : str
        Phrase that must match the end of the filename for it to be checked for
        PyDMPlugins

    Returns
    -------
    plugins: dict
        Dictionary of plugins add from this folder
    """
    added_plugins = dict()
    for loc in locations:
        for root, _, files in os.walk(loc):
            if root.split(os.path.sep)[-1].startswith("__"):
                continue

            logger.debug("Looking for PyDM Data Plugins at: %s", root)
            for name in files:
                if name.endswith(token):
                    try:
                        logger.debug("Trying to load %s...", name)
                        sys.path.append(root)
                        temp_name = str(uuid.uuid4())
                        module = imp.load_source(temp_name,
                                                 os.path.join(root, name))
                    except Exception as e:
                        logger.exception("Unable to import plugin file %s."
                                         "This plugin will be skipped."
                                         "The exception raised was: %s",
                                         name, e)
                        continue
                    classes = [obj for name, obj in inspect.getmembers(module)
                               if (inspect.isclass(obj)
                                   and issubclass(obj, PyDMPlugin)
                                   and obj is not PyDMPlugin)]
                    # De-duplicate classes.
                    classes = list(set(classes))
                    for plugin in classes:
                        if plugin.protocol is not None:
                            # Add to global plugin list
                            add_plugin(plugin)
                            # Add to return dictionary of added plugins
                            added_plugins[plugin.protocol] = plugin
    return added_plugins


def is_read_only():
    """
    Check whether or not the app is running with the read only flag set.

    Returns
    -------
    bool
        True if read only. False otherwise.
    """
    return __read_only


def set_read_only(read_only):
    """
    Set the read only flag for the data plugins.

    Parameters
    ----------
    read_only : bool
    """
    global __read_only
    __read_only = read_only
    if read_only:
        logger.info("Running PyDM in Read Only mode.")


# Load the data plugins from PYDM_DATA_PLUGINS_PATH
logger.debug("*"*80)
logger.debug("* Loading PyDM Data Plugins")
logger.debug("*"*80)

DATA_PLUGIN_TOKEN = "_plugin.py"
path = os.getenv("PYDM_DATA_PLUGINS_PATH", None)
if path is None:
    locations = []
else:
    locations = path.split(os.pathsep)

# Ensure that we first visit the local data_plugins location
plugin_dir = os.path.dirname(os.path.realpath(__file__))
locations.insert(0, plugin_dir)

load_plugins_from_path(locations, DATA_PLUGIN_TOKEN)
