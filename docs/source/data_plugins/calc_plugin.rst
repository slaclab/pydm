========================
Calc Plugin
========================

PyDM uses Data Plugins as sources of information to be displayed at the widgets.
Calc Plugin allows users to create and use mathematical expressions.

The Calc Plugin takes in data from given channels and then applies a mathematical expressions, the result is broadcast to all the listeners connected to this particular calc channel.

By default, as soon as any widgets gets connected to the same channel variable, they will get the results from the mathematical expression defined in the channel's address. These widgets can receive any updates when the calc channel's output changes.
For example, if the user has added a calc channel to a PyDMLabel, then the PyDMLabel will update whenever a new value from one of the channels listed by the calc plugin is pushed to the calc plugin.

General Calc Plugin channel syntax::

	calc://{"name":"my_variable_name","channels":[ca//address], "expr":"math expression"}

.. note:: Once a calc channel is created, multiple widgets can be connected to the same channel by providing the name of the variable, like so:
	::

		calc://{"name":"my_variable_name"}

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
**name**    | the identifier for the mathematical expression   `"name":"my_expr_name"`
            | user's choice
**channels** | dictionary with variable and address pairs      `"channels":{"var":"channel://address"}`
**expr**    mathematical expression to be used                 `"expr":"math expression"`
=========== ================================================== ========================


Here is a simple example of a channel address format with the required attributes:
::

	"calc://{"name":"circ","channels":{"var":"ca://DEMO:ANGLE"},"expr":"math.sin(math.radians(var))"}"



------------


Simple Calc Plugin Example
---------------------------------


The picture below represents a simple example using the Local Data Plugin, where a Waveform Curve Editor has two local data plugin channels::

	loc://{"name":"y", "type":"array","init":[1,2,3,4,5,6], "extras": {"dtype":"float64"}}

	loc://{"name":"x", "type":"array","init":[1,2,3,4,5,6], "extras": {"dtype":"float64"}}

Right below the Waveform Curve Editor widget, there are two other widgets connected to the 'x' and 'y' local variable respectively::


	X-values: loc://{"name":"x"}
	Y-values: loc://{"name":"y"}

Data can be updated in the two X and Y-values widgets and the Waveform Curve Editor will receive the new data and change the curve accordingly, like seen in the picture below:



*Waveform Curve Example with ndarrays fro X and Y values*

.. image:: ../_static/data_plugins/waveform_curve_local_plugin.png
   :width: 600 pt
   :align: center