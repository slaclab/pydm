#############
PyDMTabWidget
#############

The PyDM Tab Widget is a container widget that lets you switch between different pages of content using a tab bar.  Each tab has an optional alarm channel.  When a tab specifies an alarm channel, an alarm indicator will appear next to the label for that tab.  When the channel's alarm severity changes, the indicator will update accordingly.  This is most useful for 'summary' alarms, where you have one alarm that represents the alarm state of a whole group of devices.

.. figure:: /_static/widgets/tab_widget.png
   :scale: 100 %
   :alt: A screenshot of the PyDM Tab Widget.

   A screenshot of the PyDM Tab Widget.  The alarm indicators for each tab are displayed to the left of the tab's label.

Using the PyDM Tab Widget in Designer
=====================================

In designer, drag a tab widget from the widget list onto your display, and resize it appropriately.  You can use the property editor to give the current tab a label (the 'currentTabText' property), a name (the 'currentTabName' property - this is what you will use to refer to this tab in code), and an alarm channel ('currentTabAlarmChannel').  To add a new tab to the tab widget, right click on the widget and select 'Insert Page'.  You can choose to insert before or after the current tab.  To remove a tab, right click on the tab widget, and select 'Page X of Y' -> Delete.


Widget Properties
=================

======================  ====  ===========
Property                Type  Description
======================  ====  ===========
currentTabAlarmChannel  str   A channel to use for the alarm indicator on the current tab.
currentTabText          str   The label to use for the current tab. 
currentTabName          str   A name for the tab.  This is how you will refer to the tab in python code.
======================  ====  ===========


API Documentation
=================

.. autoclass:: pydm.widgets.tab_bar.PyDMTabWidget
   :members:
   :show-inheritance:


.. note::
   See `QTabWidget Documentation <https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QTabWidget.html>`_ for all inherited properties and methods.