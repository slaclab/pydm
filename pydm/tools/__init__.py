import collections
import functools
import inspect
import logging
import os
from typing import Any, Dict, Generator, List, Optional, Union

import entrypoints
from qtpy.QtWidgets import QMenu, QWidget

from pydm.config import ENTRYPOINT_EXTERNAL_TOOL, EXTERNAL_TOOL_SUFFIX
from pydm.utilities import import_module_by_filename, log_failures
from .tools import ExternalTool

logger = logging.getLogger(__name__)
ext_tools: Dict[str, Any] = {}
_ext_tools_loaded: bool = False


def _is_valid_external_tool_class(obj: Any) -> bool:
    """Is the object a valid external tool?"""
    return inspect.isclass(obj) and issubclass(obj, ExternalTool) and obj is not ExternalTool


@log_failures(logger, explanation="Failed to load External Tool: {args[0]}")
def _get_tools_from_source(source_filename: str) -> List[ExternalTool]:
    """
    For a given source filename, find ExternalTool classes.

    Parameters
    ----------
    source_filename : str
        The source code filename.

    Returns
    -------
    tools : list of ExternalTool
        Instantiated external tools.

    Raises
    ------
    ValueError
        If no subclassed external tools are found.
    """
    module = import_module_by_filename(source_filename)
    classes = list(set(obj for _, obj in inspect.getmembers(module) if _is_valid_external_tool_class(obj)))

    if not classes:
        raise ValueError(
            f"Invalid File Format. {source_filename} has no class inheriting "
            "from ExternalTool. Nothing to open at this time."
        )
    return [c() for c in classes]


@log_failures(logger, explanation="Failed to load External Tool: {args[0]}")
def install_external_tool(tool: Union[str, ExternalTool]) -> None:
    """
    Install an External Tool at the PyDMApplication and add it to the main
    window Tools menu.

    Parameters
    ----------
    tool : str or pydm.tools.ExternalTool
        The full path to a file containing a ExternalTool definition
        or an Instance of an ExternalTool.
    """
    global ext_tools

    if isinstance(tool, str):
        objects = _get_tools_from_source(tool) or []
    else:
        objects = [tool]

    for tool_obj in objects:
        if not isinstance(tool_obj, ExternalTool):
            raise ValueError(f"Invalid tool found: {tool}. String or ExternalTool expected.")

        if tool_obj.group is not None and tool_obj.group:
            if tool_obj.group not in ext_tools:
                ext_tools[tool_obj.group] = {}
            ext_tools[tool_obj.group][tool_obj.name] = tool_obj
        else:
            ext_tools[tool_obj.name] = tool_obj

    ext_tools = collections.OrderedDict(sorted(ext_tools.items()))
    for ext_tool_name in ext_tools:
        if isinstance(ext_tools[ext_tool_name], dict):
            ext_tools[ext_tool_name] = collections.OrderedDict(sorted(ext_tools[ext_tool_name].items()))


def assemble_tools_menu(
    parent_menu: QMenu, clear_menu: bool = False, widget_only: bool = False, widget: Optional[QWidget] = None, **kwargs
) -> None:
    """
    Assemble the Tools menu for a given parent menu.

    Parameters
    ----------
    parent_menu : QMenu
        The main menu item to hold the tools menu tree.
    clear_menu : bool, optional
        Whether of not we should clear the menu before adding the tools.
    widget_only : bool, optional
        Whether or not generate only the menu for widgets compatible
        tools. This should be True when creating the menu for the
        PyDMWidgets and False for most of the other cases.
    widget : QWidget, optional
        The widget for which the menu is being assembled. This allow for the
        tools to filter if they are compatible or not with the widget based
        on properties, types and etc. Default is None which means all tools
        will be assembled.
    **kwargs :
        Parameters sent directly to the `call` method of the ExternalTool
        instance. In general this dict is composed by `channels` which
        is a list and `sender` which is a QWidget.
    """

    def assemble_action(menu, tool_obj):
        if tool_obj.icon is not None:
            action = menu.addAction(tool_obj.name)
            action.setIcon(tool_obj.icon)
        else:
            action = menu.addAction(tool_obj.name)
        action.triggered.connect(functools.partial(tool_obj.call, **kwargs))

    load_external_tools()

    if clear_menu:
        parent_menu.clear()
    else:
        parent_menu.addSeparator()

    for k, v in ext_tools.items():
        if isinstance(v, dict):
            m = QMenu(k, parent=parent_menu)
            should_create_menu = False
            for _, t in v.items():
                if widget_only:
                    if not t.use_with_widgets:
                        continue
                    if widget is not None and not t.is_compatible_with(widget):
                        logger.debug(
                            "Skipping tool %s as it is incompatible with widget %s.",
                            t.name,
                            widget,
                        )
                        continue
                elif not t.use_without_widget:
                    continue
                assemble_action(m, t)
                should_create_menu = True
            if should_create_menu:
                parent_menu.addMenu(m)
        else:
            if widget_only and not v.use_with_widgets:
                continue
            assemble_action(parent_menu, v)


def get_entrypoint_tools() -> Generator[ExternalTool, None, None]:
    """
    Yield all external tool classes specified by entrypoints.

    Uses ``entrypoints`` to find packaged external tools in packages that
    configure the ``pydm.tool`` entrypoint.
    """
    for entry in entrypoints.get_group_all(ENTRYPOINT_EXTERNAL_TOOL):
        logger.debug("Found external tool entrypoint: %s", entry.name)
        try:
            tool_cls = entry.load()
        except Exception as ex:
            logger.exception("Failed to load %s entry %s: %s", ENTRYPOINT_EXTERNAL_TOOL, entry.name, ex)
            continue

        if not _is_valid_external_tool_class(tool_cls):
            logger.warning("Invalid external tool class specified in entrypoint %s: %s", entry.name, tool_cls)
            continue

        yield tool_cls()


def get_tools_from_path() -> Generator[ExternalTool, None, None]:
    """Yield all external tool classes specified by PYDM_TOOLS_PATH."""
    tools_path = os.getenv("PYDM_TOOLS_PATH", None)

    if not tools_path:
        logger.debug("External Tools not loaded from PYDM_TOOLS_PATH as no path was specified.")
        return

    logger.debug("Looking for external tools at: %s", tools_path)
    for loc in tools_path.split(os.pathsep):
        for root, _, files in os.walk(loc):
            for name in files:
                if name.endswith(EXTERNAL_TOOL_SUFFIX):
                    tool_path = os.path.join(root, name)
                    logger.debug("Found tool in %s", tool_path)
                    yield from _get_tools_from_source(tool_path)


def load_external_tools():
    """
    Loads all the external tools available.

    1. Uses ``PYDM_TOOLS_PATH`` environment variable. Searches all directories
       and subdirectories for Python source code that matches the pattern
       ``*_tool.py`` which contain classes that inherit from
       :class:`pydm.tools.ExternalTool`.
    2. Uses ``entrypoints`` to find packaged external tools in packages that
       configure the ``pydm.tool`` entrypoint.

    If called previously, this function is a no-operation.
    """
    global _ext_tools_loaded

    if _ext_tools_loaded:
        return

    _ext_tools_loaded = True

    for tool in get_tools_from_path():
        install_external_tool(tool)

    for tool in get_entrypoint_tools():
        install_external_tool(tool)
