Including Data Plugins
######################
PyDM is built with a flexible architecture such that information from multiple
sources can be displayed without changing widget code. This allows widgets to
be agnostic of the data source that updates them and focus on the logic of
displaying information.  PyDM will always import the built-in plugins found in
the ``data_plugins`` folder,  but some advanced users may want to include
custom data plugins as well. A mapping of ``protocol`` to ``PyDMPlugin`` is
kept within ``pydm.data_plugins.plugin_modules`` and mirrored in
:attr:`.PyDMApplication.plugins`. This is where the ``PyDMApplication`` will
determine which plugin to use when you provided it with a channel.

If you would like add a library of plugins from a specific folder for every
session, PyDM will check all paths provided by the environment variable
``$PYDM_DATA_PLUGINS_PATH``. This folder will be searched for files that fit
the name ``{}_plugin.py`` and attempt to load the contained plugin. Each of
these files should contain a single ``PyDMPlugin``. For those searching for a
more programmatic approach the API is documented below. Take note that all
plugins should be registered before the ``PyDMApplication`` is launched,
otherwise they will not be registered in time for connections to be made.

.. autofunction:: pydm.data_plugins.add_plugin

.. autofunction:: pydm.data_plugins.load_plugins_from_path
