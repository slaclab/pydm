=================
Adding Help Files
=================

If you are creating a display and would like to add some documentation on how it works, PyDM provides the ability
to do this with a minimum of extra effort. By placing a .txt or .html file in the same directory as your display,
PyDM will load this file and automatically add it to both the View menu of the top menu bar, as well as the right
click menu of widgets on the display.

In order for PyDM to associate the help file with your display, it must have the same name as your display file. For
example, let's say that we have a file called drawing_demo.ui. By adding a file called drawing_demo.txt to the same
location, PyDM will load that file along with the display.

.. figure:: /_static/help_files.gif
   :scale: 100 %
   :align: center
   :alt: Help files

   Where to find the automatically loaded help file
