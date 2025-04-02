#######################
PyDMWidget
#######################

API Documentation
=================

.. autoclass:: pydm.widgets.base.PyDMWidget
   :members:
   :show-inheritance:

PyDMToolTip Instructions
========================
The PyDMToolTip property field takes a string. In the PyDMToolTip property field, the user can include the tag $(pv_value) to get the value of the
channel displayed on the tool tip.

.. note::

    If the toolTip property field is:

        The value of the channel is $(pv_value)

    The toolTip would read (assuming the value is 10 in this example):

        The value of the channel is 10

A period followed by a field name can retrieve other properties of the channel
(see the table below for all channel properties and associated field names.)

.. note::

    If the toolTip property field is:

        The timestamp of the channel is $(pv_value.TIME)

    The toolTip would read:

        The timestamp of the channel is 2022-09-15 09:56:47.099340

======================  ==============  ====================================
channel properties      pv_value.field  Description
======================  ==============  ====================================
channel value           $(pv_value)     Returns the value of the channel
channel address         .address        Returns the address of the channel
connection              .connection     Returns the connection status
alarm severity          .SEVR           Returns the alarm severity
enum string             .enum_strings
engineering unit        .EGU            Returns the engineering unit
precision               .PREC           Returns the precision of the channel
upper ctrl limit        .DRVH           Returns the upper ctrl limit
lower ctrl limit        .DRVL           Returns the lower ctrl limit
upper alarm limit       .HIHI           Returns the upper alarm limit
lower alarm limit       .LOLO           Returns the lower alarm limit
upper warning limit     .HIGH           Returns the upper warning limit
lower warning limit     .LOW            Returns the lower warning limit
timestamp               .TIME           Returns the timestamp of the channel
======================  ==============  ====================================

