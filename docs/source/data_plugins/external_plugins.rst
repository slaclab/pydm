External Data Plugins
=====================

To add an external data plugin to PyDM, you will need to subclass the following
base class and customize its methods:

.. autoclass:: pydm.data_plugins.PyDMPlugin
   :members:
   :inherited-members:
   :show-inheritance:


You will also need to create a connection class and refer to it with the
``connection_class`` class variable.  It should be subclassed from the
following:

.. autoclass:: pydm.data_plugins.plugin.PyDMConnection
   :members:
   :inherited-members:
   :show-inheritance:


Configuration
-------------

There are two options for telling PyDM where your external data plugin can
be found.

The first is the ``PYDM_DATA_PLUGINS_PATH`` environment variable, which is an
delimited list of paths to search for files that match the pattern
``*_plugin.py``. They can be in the provided path or any subdirectory of that
path. On Linux, the delimiter is ":" whereas on Windows it is ";".

Alternatively, for Python packages that contain external data plugins, an
entrypoint may be used to locate it.

Here is an example ``setup.py`` that could be used to locate a PyDM data plugin
in your own Python package:

.. code:: python

    from setuptools import setup, find_packages

    setup(
        name="my_package",
        # ... other settings will go here
        entry_points={
            "gui_scripts": ["my_package_gui=my_package.main:main"],
            "pydm.data_plugin": [
                "my_package=my_package.data:PluginClassName",
            ],
        },
        install_requires=[],
    )


This would assume that you have the following:

1. A package named "my_package" with ``my_package/__init__.py`` and
   ``my_package/data.py``.
2. In ``my_package/data.py``, a ``PluginClassName`` that inherits from
   :class:`~pydm.data_plugins.PyDMPlugin`.

After running ``pip install`` on the package, it should be readily available
in PyDM.
