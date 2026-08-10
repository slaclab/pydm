==========================================
Tips for Performance of Large Applications
==========================================

This page is dedicated to best practices for large pydm applications.
We'll define a large application as one that has more than a few
thousand PVs and dynamically manages hundreds to thousands of
dynamically allocated and dynamically shown widgets.

These applications are typically constructed in the following manner:
- One entry python file with a ``Display`` subclass for pydm to find
- One "frame" ui file linked with this ``Display`` that contains some
  static resources and an empty layout.
- One or more "template" ui file that represents a repeated element
  in the aforementioned ``Display``.

This is a reasonably good approach for creating applications to view
and manage large numbers of repeated items on your beamline. There
are a few things to keep in mind in these and in related situations
to make sure your application loads quickly and stays responsive.

Dynamically Showing Many widgets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Calling .show() or setVisible(True) on hundreds or thousands of widgets
at once has a large performance penalty, causing the GUI to freeze from
the perspective of the user. This should be avoided as much as possible.

TODO things to investigate before finishing this docs section:
- Hiding unseen widgets in scroll areas
- Working into template repeater some sort of paint ten-at-a-time
  functionality
- Including some filtering help in pydm

Rules vs No Rules
^^^^^^^^^^^^^^^^^
The rules engine is very helpful when editing displays in designer, but
behind the scenes we can create problems if we overload the engine-
particularly if it takes more than 1/30th of a second to evaluate all
widget rules.

TODO things to investigate before finishing this docs section:
- Example alternatives to rules (signal/slot setups)
- Some built-in help for these sorts of constructs in the template
  repeater

Template Macros
^^^^^^^^^^^^^^^
Macros are very helpful for re-using ui files in a simple way, but
has a large performance penalty if we're repeatedly using it hundreds
or thousands of time at startup.

TODO things to investigate before finishing this docs section:
- Example alternatives to loading ui files
- Some built-in help for loading a pydm ui subdisplay in a way where
  we can initialize everything in init using init args and re-use classes
