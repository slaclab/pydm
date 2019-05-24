===============
Troubleshooting
===============

If you can't find the answer to your problem below please open an issue at our
bug tracker clicking on `this link <https://github.com/slaclab/pydm/issues/new?template=bug-report.md>`_.


I can't find the PyDM Widgets in Qt Designer
============================================

For Qt Designer to see the PyDM widgets, the PyQt Designer Plugin needs to
be installed. This is usually done as part of the PyQt install process, but
some package managers (like homebrew on OSX, Anaconda and others) don't install
the plugin when PyQt is installed.

You can verify if the plugin is available by opening the Qt Designer and opening
the "About Plugins" window. If the plugin is available you will see something
like **libpyqt5** in the list of "Loaded Plugins".

If you can't find it there, that means that your package manager did not provide
the proper installation for PyQt. In that case, you'll probably need to install
PyQt from source.
Follow the directions from the `PyQt documentation <http://pyqt.sourceforge.net/Docs/PyQt5/installation.html#building-and-installing-from-source>`_.

If you see the plugin there but still the PyDM Widgets are not loaded, make sure
that the :ref:`designer_plugin_path` is configured correctly.