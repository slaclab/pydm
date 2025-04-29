"""
Loads all the data plugins available at the given PYDM_DATA_PLUGINS_PATH
environment variable and subfolders that follows the *_plugin.py and have
classes that inherits from the pydm.data_plugins.PyDMPlugin class.
"""

import inspect
import logging
import os
from collections import deque
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional, Type

import entrypoints
from qtpy.QtWidgets import QApplication

from pydm import config
from pydm.utilities import import_module_by_filename, log_failures, parsed_address
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
        while __CONNECTION_QUEUE__ is not None and len(__CONNECTION_QUEUE__) > 0:
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


def plugin_for_address(address: str) -> Optional[PyDMPlugin]:
    """
    Find the correct PyDMPlugin for a channel
    """
    # Check for a configured protocol
    try:
        protocol = parsed_address(address).scheme
    except AttributeError:
        protocol = None

    # Use default protocol
    if protocol is None and config.DEFAULT_PROTOCOL is not None:
        logger.debug("Using default protocol %s for %s", config.DEFAULT_PROTOCOL, address)
        # If no protocol was specified, and the default protocol
        # environment variable is specified, try to use that instead.
        protocol = config.DEFAULT_PROTOCOL

    # Load proper plugin module
    if protocol:
        initialize_plugins_if_needed()
        try:
            return plugin_modules[(str(protocol)).lower()]
        except KeyError:
            logger.exception("Could not find protocol for %r", address)
    # Catch all in case of improper plugin specification
    logger.error(
        "Channel {addr} did not specify a valid protocol "
        "and no default protocol is defined. This channel "
        "will receive no data. To specify a default protocol, "
        "set the PYDM_DEFAULT_PROTOCOL environment variable."
        "".format(addr=address)
    )

    return None


def add_plugin(plugin: Type[PyDMPlugin]) -> Optional[PyDMPlugin]:
    """
    Add a PyDM plugin to the global registry of protocol vs. plugins

    Parameters
    ----------
    plugin : PyDMPlugin type
        The class of plugin to instantiate

    Returns
    -------
    plugin : PyDMPlugin, optional
        The instantiated PyDMPlugin. If instantiation failed, will return None.
    """
    # Warn users if we are overwriting a protocol which already has a plugin
    if plugin.protocol in plugin_modules:
        logger.warning(
            "Replacing %s plugin with %s for use with protocol %s",
            plugin,
            plugin_modules[plugin.protocol],
            plugin.protocol,
        )
    try:
        instance = plugin()
    except Exception:
        logger.exception(f"Data plugin: {plugin} failed to load and will not be available for use!")
        return None

    plugin_modules[plugin.protocol] = instance
    return instance


@log_failures(
    logger,
    explanation=("Unable to import plugin file: {args[0]}.  This plugin will be skipped."),
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
    module = import_module_by_filename(source_filename)
    return list(set(obj for _, obj in inspect.getmembers(module) if _is_valid_plugin_class(obj)))


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


def find_plugins_from_entrypoints(
    key: str = config.ENTRYPOINT_DATA_PLUGIN,
) -> Generator[Type[PyDMPlugin], None, None]:
    """
    Yield all PyDMPlugin classes specified by entrypoints.

    Uses ``entrypoints`` to find packaged external tools in packages that
    configure the ``pydm.data_plugin`` entrypoint.

    Parameters
    ----------
    key : str, optional
        The entrypoint key.
    """
    for entry in entrypoints.get_group_all(key):
        logger.debug("Found data plugin entrypoint: %s", entry.name)
        try:
            plugin_cls = entry.load()
        except Exception as ex:
            logger.exception("Failed to load %s entry %s: %s", key, entry.name, ex)
            continue

        if not _is_valid_plugin_class(plugin_cls):
            logger.warning("Invalid plugin class specified in entrypoint %s: %s", entry.name, plugin_cls)
            continue

        yield plugin_cls


def _is_valid_plugin_class(obj: Any) -> bool:
    """Is the object a data plugin class?"""
    return inspect.isclass(obj) and issubclass(obj, PyDMPlugin) and obj is not PyDMPlugin


def load_plugins_from_entrypoints(key: str = config.ENTRYPOINT_DATA_PLUGIN) -> Dict[str, PyDMPlugin]:
    """
    Load plugins from file locations that match a specific token

    Parameters
    ----------
    key : str, optional
        The entrypoint key.

    Returns
    -------
    plugins : dict
        Dictionary of plugins add from this folder
    """
    added_plugins = dict()
    for plugin in find_plugins_from_entrypoints(key):
        if not plugin.protocol:
            logger.warning(
                "No protocol specified for data plugin: %s.%s",
                plugin.__module__,
                plugin,
            )
            continue
        added_plugin = add_plugin(plugin)
        if added_plugin is not None:
            added_plugins[plugin.protocol] = added_plugin
    return added_plugins


def load_plugins_from_path(locations: List[str], token: str = config.DATA_PLUGIN_SUFFIX) -> Dict[str, PyDMPlugin]:
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
            if not plugin.protocol:
                logger.warning(
                    "No protocol specified for data plugin: %s.%s",
                    plugin.__module__,
                    plugin,
                )
                continue

            added_plugin = add_plugin(plugin)
            if added_plugin is not None:
                added_plugins[plugin.protocol] = added_plugin

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
    logger.debug("*" * 80)
    logger.debug("* Loading PyDM Data Plugins")
    logger.debug("*" * 80)

    path = os.getenv("PYDM_DATA_PLUGINS_PATH", None)
    if path is None:
        locations = []
    else:
        locations = path.split(os.pathsep)

    # Ensure that we first visit the local data_plugins location
    plugin_dir = os.path.dirname(os.path.realpath(__file__))
    locations.insert(0, plugin_dir)

    load_plugins_from_path(locations)
    load_plugins_from_entrypoints(config.ENTRYPOINT_DATA_PLUGIN)
