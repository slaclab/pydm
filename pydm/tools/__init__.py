import os
import sys
import imp
import uuid
import inspect
import logging
import platform
import functools
import collections

from qtpy.QtWidgets import QMenu

from .tools import *
from ..utilities import path_info

logger = logging.getLogger(__name__)
ext_tools = {}


def install_external_tool(tool):
    """
    Install an External Tool at the PyDMApplication and add it to the
    main window Tools menu.

    Parameters
    ----------
    tool : str or pydm.tools.ExternalTool
        The full path to a file containing a ExternalTool definition
        or an Instance of an ExternalTool.
    """
    global ext_tools

    try:
        if isinstance(tool, str):
            base_dir, _, _ = path_info(tool)
            sys.path.append(base_dir)
            temp_name = str(uuid.uuid4())

            module = imp.load_source(temp_name, tool)
            classes = [obj for _, obj in inspect.getmembers(module)
                       if inspect.isclass(obj) and issubclass(obj,
                                                              ExternalTool) and obj != ExternalTool]
            if len(classes) == 0:
                raise ValueError(
                    "Invalid File Format. {} has no class inheriting from ExternalTool. Nothing to open at this time.".format(
                        tool))
            obj = [c() for c in classes]
        elif isinstance(tool, ExternalTool):
            # The actual tool to be installed...
            obj = [tool]
        else:
            raise ValueError(
                "Invalid argument for parameter 'tool'. String or ExternalTool expected.")

        for o in obj:
            if o.group is not None and o.group != "":
                if o.group not in ext_tools:
                    ext_tools[o.group] = dict()
                ext_tools[o.group][o.name] = o
            else:
                ext_tools[o.name] = o

        ext_tools = collections.OrderedDict(sorted(ext_tools.items()))
        for k in ext_tools.keys():
            if isinstance(ext_tools[k], dict):
                ext_tools[k] = collections.OrderedDict(
                    sorted(ext_tools[k].items()))
    except Exception as e:
        logger.exception("Failed to load External Tool: %s." % tool)


def assemble_tools_menu(parent_menu, clear_menu=False, widget_only=False,
                        **kwargs):
    """
    Assemble the Tools menu for a given parent menu.

    Parameters
    ----------
    parent_menu : QMenu
        The main menu item to hold the tools menu tree.
    clear_menu : bool
        Whether of not we should clear the menu before adding the tools.
    widget_only : bool
        Whether or not generate only the menu for widgets compatible
        tools. This should be True when creating the menu for the
        PyDMWidgets and False for most of the other cases.
    kwargs : dict
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
                if widget_only and not t.use_with_widgets:
                    continue
                assemble_action(m, t)
                should_create_menu = True
            if should_create_menu:
                parent_menu.addMenu(m)
        else:
            if widget_only and not v.use_with_widgets:
                continue
            assemble_action(parent_menu, v)


def load_external_tools():
    """
    Loads all the external tools available at the given
    `PYDM_TOOLS_PATH` environment variable and subfolders that
    follows the `*_tool.py` and have classes that inherits from
    the `pydm.tools.ExternalTool` class.
    """
    if not ext_tools:
        EXT_TOOLS_TOKEN = "_tool.py"
        path = os.getenv("PYDM_TOOLS_PATH", None)

        if path is not None:
            logger.debug("Looking for external tools at: {}".format(path))
            if platform.system() == "Windows":
                locations = path.split(";")
            else:
                locations = path.split(":")
            for loc in locations:
                for root, _, files in os.walk(loc):
                    for name in files:
                        if name.endswith(EXT_TOOLS_TOKEN):
                            install_external_tool(os.path.join(root, name))
        else:
            logger.debug(
                "External Tools not loaded. No External Tools Path specified.")
