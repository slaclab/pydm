#######################
PyDMWindow
#######################

The PyDM Window Widget is a container widget that allows the display creator to set certain global display
properties. It is currently used to hide specific UI elements when the display is the first loaded display
in the running PyDM instance.

Using the PyDM Window Widget in Designer
========================================

In designer, when creating a new display, select PyDMWindow as the base widget.


Widget Properties
=================

============= ==== ===========
Property      Type Description
============= ==== ===========
hideMenuBar   bool Hide the menu bar if this is the first loaded display.
hideNavBar    bool Hide the nav bar if this is the first loaded display.
hideStatusBar bool Hide the status bar if this is the first loaded display.
============= ==== ===========


API Documentation
=================

.. autoclass:: pydm.widgets.window.PyDMWindow
   :members:
   :show-inheritance:
