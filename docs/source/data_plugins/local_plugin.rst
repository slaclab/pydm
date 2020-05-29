========================
Local Plugin
========================

PyDM uses Data Plugins as sources of information to be displayed at the widgets. 
Local Data Plugin allows users to create and use local variables.

The Local Data Plugin stores the data that is sent by the widgets through a channel, and broadcasts it to all the listeners connected to this particular local variable channel.

By default, as soon as any widgets get connected to the same channel variable, they will get the initial values that were defined in the channel address. These widgets can receive any updates when the data changes, or, they can to send data back.
For example, if the user has added a Local Variable channel to a PyDMEditLine, then all the widgets connected to this Local Variable, will get the values that are updated by the user in the PyDMEditLine.

General Local Plugin channel syntax::

	loc://{"name":"my_variable_name","type":"variable_type", "init":"initial_values"}

Once a Local Variable channel is created, multiple widgets can be connected to the same channel by only providing the name of the variable, like so::

	loc://{"name":"my_variable_name"}



**Other things to note:**

* If precision is not sent through the "extras", and it is set to receive the precision from the PV (Process Variable), the Local Data Plugin will match the precision from the values inserted by the users in the widgets.


Required Attributes
-------------------

The table below explains the attributes that are required to create a local plugin channel:

=========== =================================== ========================
Attributes  Description                         Format Example
=========== =================================== ========================
**loc**     protocol name for Local Data Plugin `loc://`
**name**    the identifier for a local variable `"name":"my_ndarray_var"`
**type**    data-type for this variable         `"type":"ndarray"`
**init**    initial values to be used           `"init":"[1,2,3,4]"`
=========== =================================== ========================


.. important:: It is important to spell the attributes correctly and to write the address in the appropriate format including all the attributes from the table above. Here is a good example of how to fomat the channel adress with the required the attributes:
	::
	
		loc://{"name":"my_np.array","type":"ndarray","init":"[1,2,3,4]"}

.. note:: When creating a local variable with a ndarray, "numpy.ndarray" or "np.ndarray" will be acceptable for the type too.

Extra Attributes
----------------

The table below explains the optional attributes that can go in the *extras*:
                                                             

=============== =================================== ============ ==============================
Attributes      Description                         Type         Format Example
=============== =================================== ============ ==============================
**precision**   precision of float values           int          `"precision":"3"`
**unit**        units for the data                  string       `"unit:"V"`
**upper_limit** upper control value limit           float or int `"upper_limit":"100"`
**lower_limit** lower control value limit           float or int `"lower_limit":"-100"`
**enum_string** new list of values                  tuple        `"enum_string":"(hey, hello)"`
**severity**    alarm severity                      int          | `"severity":"0"` (*NO_ALARM*)
						                 | `"severity":"1"` (*MINOR*)
                                                                 | `"severity":"2"` (*MAJOR*)
                                                                 | `"severity":"3"` (*INVALID*)

--------------- ----------------------------------- ------------ ------------------------------

**dtype**       desired data-type for the array     np.dtype     | `"dtype":"float64"`
                                                                 | `"dtype":"uint8"`
**copy**        if *True* then the object is copied bool          `"copy":"True"` (*default*)
**order**       memory layout of the array          string       | `"order":"K"` (*default*)
                                                                 | others {'A', 'C', 'F'}
**subok**       | if *True* then sub-classes        bool          `"subok":"False"` (*default*)
                | will be passed-through               
**ndmin**       minimum number of dimensions        int           `"ndmin":"0"` (*default*)
=============== =================================== ============ ==============================



.. important:: It is important to spell the attributes correctly and to write the address in the appropriate format. Please note that when specifying the dictionary for "extras" there are no quotes around it. Here is a good example of how to fomat the channel adress with all the attributes:
	::
	
	 	loc://{"name":"my_np.array","type":"ndarray","init":"[1,2,3,4]","extras": {"precision":"3", "unit":"V", "lower_limit":"-100", "upper_limit":"100", "enum_string": "(hey, hello)", "severity":"5", "dtype":"float64", "copy":"False", "order":"C", "ndmin":"2", "subok":"True"}}


.. note:: The "extras" Attributes are all optional, any number of desired attributes can be specified, or none. Please note that the second half of the Extras Attributes table above is only related to the creation of a ndarray. See `numpy.array <https://numpy.org/doc/stable/reference/generated/numpy.array.html>`_ for more information.


Simple Local Data Plugin Example
---------------------------------


The picture below represents a simple example using the Local Data Plugin, where a Waveform Curve Editor has two local data plugin channels::

	loc://{"name":"y", "type":"np.ndarray","init":"[1,2,3,4,5,6]"}

	loc://{"name":"x", "type":"np.ndarray","init":"[1,2,3,4,5,6]"}

Right below the Waveform Curve Editor widget, there are two other widgets connected to the 'x' and 'y' local variable respectively::

	
	X-values: loc://{"name":"x"}
	Y-values: loc://{"name":"y"}

Data can be updated in the two X and Y-values widgets and the Waveform Curve Editor will receive the new data and change the curve accordingly. 



*Waveform Curve Example with ndarrays fro X and Y values*

.. image:: ../_static/data_plugins/waveform_curve_local_plugin.png
   :width: 600pt
   :align: center




