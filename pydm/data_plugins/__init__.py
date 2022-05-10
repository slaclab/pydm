"""
Loads all the data plugins available at the given PYDM_DATA_PLUGINS_PATH
environment variable and subfolders that follows the *_plugin.py and have
classes that inherits from the pydm.data_plugins.PyDMPlugin class.
"""
import imp
import inspect
import logging
import os
import sys
import uuid
from collections import deque
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Type

from qtpy.QtWidgets import QApplication

from .. import config
from ..utilities import log_failures, path_info, protocol_and_address
from .plugin import PyDMPlugin

logger = logging.getLogger(__name__)
plugin_modules: Dict[str, PyDMPlugin] = {}
__read_only = False
global __CONNECTION_QUEUE__
__CONNECTION_QUEUE__ = None
global __DEFER_CONNECTIONS__
__DEFER_CONNECTIONS__ = False
__plugins_initialized = False


@contextmanager
def connection_queue(defer_connections=False):
    global __CONNECTION_QUEUE__
    global __DEFER_CONNECTIONS__
    if __CONNECTION_QUEUE__ is None:
        __CONNECTION_QUEUE__ = deque()
        __DEFER_CONNECTIONS__ = defer_connections
    yield
    if __DEFER_CONNECTIONS__:
        return
    establish_queued_connections()


def establish_queued_connections():
    global __DEFER_CONNECTIONS__
    global __CONNECTION_QUEUE__
    if __CONNECTION_QUEUE__ is None:
        return
    try:
        while (__CONNECTION_QUEUE__ is not None and
               len(__CONNECTION_QUEUE__) > 0):
            channel = __CONNECTION_QUEUE__.popleft()
            establish_connection_immediately(channel)
            QApplication.instance().processEvents()
    except IndexError:
        pass
    finally:
        __CONNECTION_QUEUE__ = None
        __DEFER_CONNECTIONS__ = False


def establish_connection(channel):
    global __CONNECTION_QUEUE__
    if __CONNECTION_QUEUE__ is not None:
        __CONNECTION_QUEUE__.append(channel)
    else:
        establish_connection_immediately(channel)


def establish_connection_immediately(channel):
    plugin = plugin_for_address(channel.address)
    plugin.add_connection(channel)


def plugin_for_address(address: str) -> PyDMPlugin:
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
        initialize_plugins_if_needed()
        try:
            return plugin_modules[str(protocol)]
        except KeyError:
            logger.exception("Could not find protocol for %r", address)
    # Catch all in case of improper plugin specification
    logger.error("Channel {addr} did not specify a valid protocol "
                 "and no default protocol is defined. This channel "
                 "will receive no data. To specify a default protocol, "
                 "set the PYDM_DEFAULT_PROTOCOL environment variable."
                 "".format(addr=address))
    return None


def add_plugin(plugin: Type[PyDMPlugin]) -> PyDMPlugin:
    """
    Add a PyDM plugin to the global registry of protocol vs. plugins

    Parameters
    ----------
    plugin : PyDMPlugin type
        The class of plugin to instantiate

    Returns
    -------
    plugin : PyDMPlugin
        The instantiated PyDMPlugin.
    """
    # Warn users if we are overwriting a protocol which already has a plugin
    if plugin.protocol in plugin_modules:
        logger.warning(
            "Replacing %s plugin with %s for use with protocol %s",
            plugin,
            plugin_modules[plugin.protocol],
            plugin.protocol,
        )
    instance = plugin()
    plugin_modules[plugin.protocol] = instance
    return instance


@log_failures(
    logger,
    explanation=(
        "Unable to import plugin file: {args[0]}.  "
        "This plugin will be skipped."
    ),
    include_traceback=True,
)
def _get_plugins_from_source(source_filename: str) -> List[Type[PyDMPlugin]]:
    """
    For a given source filename, find PyDMPlugin classes.

    Parameters
    ----------
    source_filename : str
        The source code filename.

    Returns
    -------
    plugins : list of PyDMPlugin classes
        The plugin classes.
    """
    base_dir, _, _ = path_info(source_filename)
    if base_dir not in sys.path:
        sys.path.append(base_dir)
    temp_name = str(uuid.uuid4())
    module = imp.load_source(temp_name, source_filename)
    return list(
        set(
            obj
            for _, obj in inspect.getmembers(module)
            if _is_valid_plugin_class(obj)
        )
    )


def find_plugins_from_path(
    path: str, token: str = config.DATA_PLUGIN_SUFFIX
) -> Generator[Type[PyDMPlugin], None, None]:
    """
    Yield all data plugins found in the provided path.

    Parameters
    ----------
    path : str
        The path to look for plugins.
    token : str, optional
        The suffix that plugin files are expected to have.
    """

    for root, _, files in os.walk(path):
        if root.split(os.path.sep)[-1].startswith("__"):
            continue

        logger.debug("Looking for PyDM Data Plugins at: %s", root)
        for name in files:
            if name.endswith(token):
                yield from _get_plugins_from_source(os.path.join(root, name))


def _is_valid_plugin_class(obj: Any) -> bool:
    """Is the object a data plugin class?"""
    return (
        inspect.isclass(obj)
        and issubclass(obj, PyDMPlugin)
        and obj is not PyDMPlugin
    )


def load_plugins_from_path(
    locations: List[str],
    token: str = config.DATA_PLUGIN_SUFFIX
) -> Dict[str, PyDMPlugin]:
    """
    Load plugins from file locations that match a specific token

    Parameters
    ----------
    locations : list of str
        List of file locations

    token : str
        Phrase that must match the end of the filename for it to be checked for
        PyDMPlugins

    Returns
    -------
    plugins : dict
        Dictionary of plugins add from this folder
    """
    added_plugins = dict()
    for loc in locations:
        for plugin in find_plugins_from_path(loc, token=token):
            if plugin.protocol is not None:
                added_plugins[plugin.protocol] = add_plugin(plugin)
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


def initialize_plugins_if_needed():
    global __plugins_initialized

    if __plugins_initialized:
        return

    __plugins_initialized = True

    # Load the data plugins from PYDM_DATA_PLUGINS_PATH
    logger.debug("*"*80)
    logger.debug("* Loading PyDM Data Plugins")
    logger.debug("*"*80)

    path = os.getenv("PYDM_DATA_PLUGINS_PATH", None)
    if path is None:
        locations = []
    else:
        locations = path.split(os.pathsep)

    # Ensure that we first visit the local data_plugins location
    plugin_dir = os.path.dirname(os.path.realpath(__file__))
    locations.insert(0, plugin_dir)

    load_plugins_from_path(locations)
    # load_plugins_from_entrypoints(config.ENTRYPOINT_DATA_PLUGIN)
