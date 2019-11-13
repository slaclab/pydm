#######################
Plot Curve Editor
#######################

PyDM plot widgets keep the inventory of curves in the ``curves`` property which
is a list of JSON strings containing the definition of parameters for each of
the curves in a plot.

Since editing a list of JSON strings via Qt Designer is very unfriendly and
error prone, PyDM offers the Plot Curve Editor extension which can be invoked
via a Right-click and selecting the "Edit Curves..." item in the context menu
that pops-up.

.. figure:: /_static/widgets/curve_editor/curve_editor.gif
   :scale: 100 %
   :align: center
   :alt: Curve Editor in Action

   This animation demonstrates how to use the Curve Editor that is common to
   all the PyDM plot widgets.


.. Note::
  This is not applicable for users interacting with widgets via Python code.
  In this case you will need to serialize the list of JSON strings and use the
  ``setCurves`` property to configure the plot properly.
