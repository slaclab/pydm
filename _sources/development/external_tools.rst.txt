External Tools
==============

To add an external tool to PyDM, you will need to subclass the following
base class and customize its methods:

.. autoclass:: pydm.tools.ExternalTool
   :members:
   :inherited-members:
   :show-inheritance:


Example:

.. code:: python

    from pydm.tools import ExternalTool
    from pydm.utilities.iconfont import IconFont


    class DummyTool(ExternalTool):

        def __init__(self):
            icon = IconFont().icon("cogs")
            name = "Dummy Tool"
            group = "Example"
            use_with_widgets = False
            super().__init__(
                icon=icon,
                name=name,
                group=group,
                use_with_widgets=use_with_widgets
            )

        def call(self, channels, sender):
            print("Called Dummy Tool from: {} with:".format(sender))
            print("Channels: ", channels)
            print("My info: ", self.get_info())

        def to_json(self):
            return ""

        def from_json(self, content):
            print("Received from_json: ", content)

        def get_info(self):
            ret = ExternalTool.get_info(self)
            ret.update({'file': __file__})
            return ret


Configuration
-------------

There are two options for telling PyDM where your external tools are.

The first is the ``PYDM_TOOLS_PATH`` environment variable, which is an
delimited list of paths to search for files that match the pattern
``*_tool.py``. They can be in the provided path or any subdirectory of that
path. On Linux, the delimiter is ":" whereas on Windows it is ";".

Alternatively, for Python packages that contain external tools, an entrypoint
may be used to locate the tool class.

Here is an example ``setup.py`` that could be used to locate a PyDM external
tool in your own Python package:

.. code:: python

    from setuptools import setup, find_packages

    setup(
        name="my_package",
        # ... other settings will go here
        entry_points={
            "gui_scripts": ["my_package_gui=my_package.main:main"],
            "pydm.tool": [
                "my_package=my_package.tool_name:ToolClassName",
            ],
        },
        install_requires=[],
    )


This would assume that you have the following:

1. A package named "my_package" with ``my_package/__init__.py`` and
   ``my_package/tool_name.py``.
2. In ``my_package/tool_name.py``, a ``ToolClassName`` that inherits from
   :class:`~pydm.tools.ExternalTool`.

After running ``pip install`` on the package, it should be readily available
in PyDM.
