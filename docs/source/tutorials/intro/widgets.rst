Widgets
=======

Organization
------------

PyDM Widgets are divided into 5 main categories:

- Display Widgets
    Widgets used for visualization of channels such as Label, Byte Indicator, Image Viewer, Symbol and others.

- Input Widgets
    Widgets used to interact with a channel and write to it, such as Line Edit, Push Button, Combo Box,
    Checkbox, among others.

- Plot Widgets
    Widgets used for data visualization and plotting.

    Currently we offer three plot types:

    - Time Plot
       Plot scalar values versus time.

    - Waveform Plot
       Plot waveform (array) values versus either array index, or another waveform (array) of the same length.

    - Scatter Plot
       Plot one scalar channel versus a different scalar channel, adding each new data point to a ring buffer.

- Container Widgets
   Widgets that group or wrap other widgets (like Frame, Tab Widget and Embedded Display) are part of this category.

- Drawing Widgets
   Widgets used to display static shapes such as Rectangle, Triangle, Circle, Image, among others.


Common Properties
-----------------

All PyDM Widgets will have the same set of base properties. Not every widget uses all of them.

As an example, the PyDMEnumComboBox makes no use of the ``precision`` part of the base properties.


=====================   ====    ========================================================================
Property                Type    Description
=====================   ====    ========================================================================
alarmSensitiveContent   bool    Whether or not the content will be affected by an alarm state
alarmSensitiveBorder    bool    Whether or not the border will be affected by an alarm state
precisionFromPV         bool    Whether or not to use the precision information from the PV
precision               int     Precision to be used if precisionFromPV is ``False``
showUnits               bool    Whether or not to display the engineering units information
channel                 str     The :ref:`Channel <Channel>` value for this widget
=====================   ====    ========================================================================

Widget Set
----------

For a complete list of widgets as well as their user-level and API documentation please refer to the
`PyDM Widgets <http://slaclab.github.io/pydm/widgets/index.html>`_ section of PyDM documentation.
