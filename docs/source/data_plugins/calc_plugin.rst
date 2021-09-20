========================
Calc Plugin
========================

PyDM uses Data Plugins as sources of information to be displayed at the widgets.
Calc Plugin allows users to create and use mathematical expressions.

The Calc Plugin takes in data from given channels and then applies a mathematical expression, the result is broadcast to all the listeners connected to this particular calc channel.

By default, as soon as any widgets gets connected to the same channel variable, they will get the results from the mathematical expression defined in the channel's address. These widgets can receive any updates when the calc channel's output changes.
For example, if the user has added a calc channel to a PyDMLabel, then the PyDMLabel will update whenever a new value from one of the channels listed by the calc plugin is pushed to the calc plugin.

General Calc Plugin channel syntax::

	calc://{"name":"my_variable_name","channels":{"var":"channel://address"}, "expr":"math expression"}

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
**update**  | The calc function will update when one of the    `"update":["var", "var_two"]`
            | variables in the update list receives a new value
            | optional. If nothing is given, the calc function
            | will run anytime one of the variables updates
=========== ================================================== ========================


Here is a simple example of a channel address format with the required attributes:
::

	"calc://{"name":"circ","channels":{"var":"ca://DEMO:ANGLE"},"expr":"math.sin(math.radians(var))"}"



------------


Simple Calc Plugin Example
---------------------------------


The picture below represents an example of using the Calc Plugin, where ::

    calc addresses given in the channels of the Wavefrom Curve Editor of a PYDMWavefromPlot :
    calc://{"name":"circleX", "channels":{"angle":"ca://DEMO:ANGLE"}, "expr":"-1*math.cos(math.radians(180-angle))"}
	calc://{"name":"circley", "channels":{"angle":"ca://DEMO:ANGLE"}, "expr":"math.sin(math.radians(180-angle))"}

    calc address given in the channels of the Wavefrom Curve Editor of a PYDMWavefromPlot to get the Tangent:
	calc://{"name":"tanval", "channels":{"angle":"ca://DEMO:ANGLE"}, "expr":"tan(radians(angle)) if angle not in [90, 270] else None"}

Right below the Waveform Curve Editor widget, there are two other widgets connected to the 'x' and 'y' local variable respectively::


	Solution: "calc://{\"name\":\"circ\"}"

Data can be updated in the two X and Y-values widgets and the Waveform Curve Editor will receive the new data and change the curve accordingly, like seen in the picture below:

*Values for TAN*

.. image:: ../_static/data_plugins/calc_example.gif
   :width: 600 pt
   :align: center

---------------

Miscellaneous
-------------

* setting a local plugin channel for a calc variable in a python file can be tricky, you will need \\\" for the quotes inside the {} of the local variable address, here is an example: "calc://{\"name\":\"num\",\"channels\":{\"var\":\"loc://{\\\"name\\\":\\\"loc_var\\\"}\"},\"expr\":\"var\"}"
* setting a local plugin channel for a calc variable in Designer you will need \" for the quotes inside the {} of the local variable address, here is an example: calc://{"name":"num","channels":{"var":"ca://DEMO:ANGLE","varTwo":"loc://{\"name\":\"int_var\"}"},"expr":"var*varTwo"}
* See `validate json <https://jsonlint.com>`_ to help validate a channel address.
* See https://docs.python.org/3/library/math.html for mathematical operations which can be used in the given expression.
* NumPy is a valid library for the mathematical expression