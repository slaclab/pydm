========================
Calc Plugin
========================

PyDM uses Data Plugins as sources of information to be displayed at the widgets.
Calc Plugin allows users to create and use mathematical expressions.

The Calc Plugin takes in data from given channels and then applies a mathematical expression, the result is broadcast to all the listeners connected to this particular calc channel.

By default, as soon as any widgets gets connected to the same channel variable, they will get the results from the mathematical expression defined in the channel's address. These widgets can receive any updates when the calc channel's output changes.
For example, if the user has added a calc channel to a PyDMLabel, then the PyDMLabel will update whenever a new value from one of the channels listed by the calc plugin is pushed to the calc plugin.

General Calc Plugin channel syntax::

    calc://my_variable_name?expr_var_name=channel://address&expr_var_name_two=channel://address&expr=math expression

.. note:: Once a calc channel is created, multiple widgets can be connected to the same channel by providing the name of the variable, like so:
    ::

        calc://my_variable_name

.. note:: The calc functions uses url formatting. Where the name attribute is separated by the ? symbol and all other attributes are separated by the & symbol.
    ::

-------------


Required Attributes
-------------------


In order to be able to properly create a calc channel, all the :ref:`required attributes<required attributes table>` must be provided in the channel's address.



.. _required attributes table:

The table below explains the attributes that are required to create a local plugin channel:

=========== ================================================== ========================
Attributes  Description                                        Format Example
=========== ================================================== ========================
**calc**    protocol name for Calc Plugin                      `calc://`
**name**    | the identifier for the mathematical expression   `my_expr_name`
            | user's choice
**var**     | variable mapped to an address for the expr       `var=channel://address`
            | attribute.
**expr**    | mathematical expression                          `expr=math expression`
=========== ================================================== ========================


Here is a simple example of a channel address format with the required attributes:
::

    "calc://circ?var=ca://DEMO:ANGLE&expr=math.sin(math.radians(var))"

------------

.. _Extra Attributes:

Extra Attributes
----------------

Along with the :ref:`required attributes<Required Attributes>`, the Local Data Plugin can also accept some optional attributes to configure the Local Variables with. These attributes should be provided in the `"extras"` dictionary.
The optional attributes are described in the :ref:`extra attributes<extra attributes table>` table below:



.. _extra attributes table:

The table below explains the optional attributes that can go in the *extras*:

=========== ================================================== ========================
Attributes      Description                         Type         Format Example
=========== ================================================== ========================
**update**  | The calc function will update when one of the    `update=[var, var_two]`
            | variables in the update list receives a new
            | value optional. If nothing is given, the calc
            | function will run anytime one of the variables
            | updates.
=========== ================================================== ========================


.. note:: The "extras" Attributes are all optional, any number of desired attributes can be specified, or none.

Here is a simple example of a channel address format with some optional attributes:
::

    calc://circ?var=ca://DEMO:ANGLE&var_two=loc://int_var&expr=var_two*var&update=[var_two]

-------------

Simple Calc Plugin Example
---------------------------------


The picture below represents an example of using the Calc Plugin.
Calc addresses given in the channels of the Wavefrom Curve Editor of a PYDMWavefromPlot::

    calc://circleX?angle=ca://DEMO:ANGLE&expr=-1*math.cos(math.radians(180-angle))
    calc://circley?angle=ca://DEMO:ANGLE&expr=math.sin(math.radians(180-angle))

Calc address given in the channels of the Wavefrom Curve Editor of a PYDMWavefromPlot to get the Tangent::

    calc://tanval?angle=ca://DEMO:ANGLE&expr=tan(radians(angle)) if angle not in [90, 270] else None


*Values for TAN*

.. image:: ../_static/data_plugins/calc_example.gif
    :width: 600 pt
    :align: center

---------------

Miscellaneous
-------------

* See https://docs.python.org/3/library/math.html for mathematical operations which can be used in the given expression.
* NumPy is a valid library for the mathematical expression