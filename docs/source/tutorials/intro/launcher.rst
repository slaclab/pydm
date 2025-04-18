PyDM Launcher
=============

PyDM provides a command-line launcher that makes it easier for users to quickly run UI files as well as code based screens.
The launcher is responsible for setting up the Python logging module but it mainly just parses the command line parameters
and sends them to the instantiated PyDMApplication.

The Launcher is available for Linux, OSX and Windows and it can be called using the command line:

.. code-block:: bash

   pydm

This will result in the PyDM Main Window being displayed.

.. figure:: /_static/tutorials/intro/main_window.png
   :scale: 75 %
   :align: center
   :alt: PyDM Main Window

Command Line Arguments
----------------------

The PyDM Launcher accepts many command line arguments, here they are:

.. code-block:: bash

   pydm [-h] [--homefile HOMEFILE] [--perfmon] [--profile] [--faulthandler]
        [--hide-nav-bar] [--hide-menu-bar] [--hide-status-bar]
        [--fullscreen] [--read-only] [--log_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
        [--version] [-m MACRO] [--stylesheet STYLESHEET] [displayfile] ...


Where:

============================ ================================================================================
Argument                     Description
============================ ================================================================================
DISPLAY_FILE (positional)    | Loads a display from this file to show once PyDM has started.
-h, --help                   | Show the PyDM help message and exit.
-r, --recurse                | Recursively search for the provided DISPLAY_FILE in the current working
                             | directory and subfolders.
--homefile FILE              | Path to a PyDM file to return to when the home button is clicked in the
                             | navigation bar. This display remains loaded at all times, and is loaded
                             | even when a display file is specified separately. If the specified
                             | display file is identical to the home file, PyDM will not load two
                             | instances of the display.
                             | **Default:** None
--perfmon                    | Enable performance monitoring, and print CPU usage to the terminal.
--profile                    | Enable cProfile function profiling, printing on exit.
--faulthandler               | Enable faulthandler to trace segmentation faults.
--hide-nav-bar               | Start PyDM with the navigation bar hidden.
--hide-menu-bar              | Start PyDM with the menu bar hidden.
--hide-status-bar            | Start PyDM with the status bar hidden.
--fullscreen                 | Start PyDM in fullscreen mode.
--read-only                  | Start PyDM in read-only mode.
--log_level LEVEL            | Configure level of log display.
                             | **Choices:** DEBUG, INFO, WARNING, ERROR, CRITICAL
                             | **Default:** INFO
--version                    | Show PyDM's version number and exit.
-m, --macro STRING           | Specify macro replacements to use, in JSON object format. Reminder: JSON
                             | requires double quotes for strings, so you should wrap this whole argument
                             | in single quotes.
                             | **Example:** ``-m '{"sector": "LI25", "facility": "LCLS"}'``
                             | Macro replacements can also be specified as KEY=value pairs using a comma
                             | as delimiter. If you want to use spaces after the delimiters or around the
                             | = signs, wrap the entire set with quotes.
                             | **Example:** ``-m "sector = LI25, facility=LCLS"``
                             | **Default:** None
--stylesheet FILE            | Specify the full path to a CSS stylesheet file, which can be used to customize
                             | the appearance of PyDM and Qt widgets.
                             | **Default:** None
DISPLAY_ARGS... (positional) | Arguments to be passed to the PyDM client application (which is a QApplication
                             | subclass).
                             | **Default:** None
============================ ================================================================================


.. note::
   It is not mandatory to use the PyDM Launcher to run your screen, but keep in
   mind that without it you will need to handle command line arguments, logging
   setup, and the instantiation of the PyDMApplication in your own code.