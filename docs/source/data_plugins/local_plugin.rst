========================
Local Plugin
========================

PyDM uses Data Plugins as sources of information to be displayed at the widgets. 
Local Data Plugin allows users to create and use local variables.

The Local Data Plugin stores the data that is sent by the widgets through a channel, and broadcasts it to all the listeners connected to this particular local variable channel.

By default, as soon as any widgets get connected to the same channel variable, they will get the initial values that were defined in the channel address. These widgets can receive any updates when the data changes, or, they can send data back.
For example, if the user has added a Local Variable channel to a PyDMEditLine, then all the widgets connected to this Local Variable, will get the values that are updated by the user in the PyDMEditLine.

General Local Plugin channel syntax::

	loc://{"name":"my_variable_name","type":"variable_type", "init":"initial_values"}

.. note:: Once a Local Variable channel is created, multiple widgets can be connected to the same channel by providing the name of the variable, like so:
	::

		loc://{"name":"my_variable_name"}

-------------

.. _Required Attributes:

Required Attributes
-------------------

In order to be able to properly create a Local Variable connection, all the :ref:`required attributes<required attributes table>` must be provided in the channel address.



.. _required attributes table:

The table below explains the attributes that are required to create a local plugin channel:

=========== =================================== ========================
Attributes  Description                         Format Example
=========== =================================== ========================
**loc**     protocol name for Local Data Plugin `loc://`
**name**    the identifier for a local variable `"name":"my_ndarray_var"`
**type**    data-type for this variable         `"type":"np.array"`
**init**    initial values to be used           `"init":[1,2,3,4]`
=========== =================================== ========================


Here is a simple example of a channel address format with the required attributes:
::
	
	loc://{"name":"my_np.array","type":"np.array","init":[1,2,3,4]}



.. note:: Please reference :ref:`Extras for Types<Variable Types>` section for more information about local variables types.

-------------

.. _Extra Attributes:

Extra Attributes
----------------

Along with the :ref:`required attributes<Required Attributes>`, the Local Data Plugin can also accept some optional attributes to configure the Local Variables with. These attributes should be provided in the `"extras"` dictionary. 
The optional attributes are described in the :ref:`extra attributes<extra attributes table>` table below: 



.. _extra attributes table: 

The table below explains the optional attributes that can go in the *extras*:
                                                             

=============== =================================== ============ =================================
Attributes      Description                         Type         Format Example
=============== =================================== ============ =================================
**precision**   precision of float values           int          `"precision":3`
**unit**        units for the data                  string       `"unit:"V"`
**upper_limit** upper control value limit           float or int `"upper_limit":100`
**lower_limit** lower control value limit           float or int `"lower_limit":-100`
**enum_string** new list of values                  tuple        `"enum_string":['hey', 'hello']`
=============== =================================== ============ =================================

.. note:: The "extras" Attributes are all optional, any number of desired attributes can be specified, or none.

Here is a simple example of a channel address format with some optional attributes:
::
	
	loc://{"name":"my.float","type":"float","init":1, "extras": {"precision":3, "unit":"V"}}

-------------

.. _Variable Types:

Variable Types
----------------

Local Data Plugin supports the following types:

- **int**
- **float**
- **bool**
- **str**
- **numpy.ndarray**



There are a few ways to create a `numpy.ndarray`:

.. note:: Arrays should be constructed using **array**, **zeros** or **empty** (refer to the :ref:`See Also` section below), but there are other built in methods that could be used to construct ndarrays. 

.. _See Also:

See Also
###########


* `array <https://numpy.org/doc/1.18/reference/generated/numpy.array.html#numpy.array>`_ - to construct an array.

* `zeros <https://numpy.org/doc/1.18/reference/generated/numpy.zeros.html#numpy.zeros>`_ - to create an array, each element of which is zero.

* `empty <https://numpy.org/doc/1.18/reference/generated/numpy.empty.html#numpy.empty>`_ - to create an array, but leave its allocated memory unchanged (i.e., it contains "garbage").

* `ones <https://numpy.org/doc/1.18/reference/generated/numpy.ones.html#numpy.ones>`_ to create an array of given shape and type, filled with ones.


* `ndarray <https://numpy.org/doc/1.18/reference/generated/numpy.ndarray.html>`_ instantiate an array using the low-level method ndarray()

* and others...


Using numpy.array built in function:
#####################################

One of the following options must be specified in the "type" value in the channel address:

* `"type":"array"`
* `"type":"np.array"`
* `"type":"numpy.array"`

The following extra attributes can be specified in the "extras" dictionary in the channel address. These attributes will be passed in the `numpy.array` function as parameters when creating the `numpy.ndarray`. If no attributes are specified, the `numpy.array` function will use the default values to create a `numpy.ndarray`. See `numpy.array <https://numpy.org/doc/1.18/reference/generated/numpy.array.html#numpy.array>`_ for more information 


* Extra Attributes for numpy.array:

=============== =================================== ============= =============================
Attributes      Description                         Type          Format Example
=============== =================================== ============= =============================
**dtype**       desired data-type for the array     np.dtype      | `"dtype":"float64"`
                                                                  | `"dtype":"uint8"`
**copy**        if *True* then the object is copied bool          `"copy":true` (*default*)
**order**       memory layout of the array          string        | `"order":"K"` (*default*)
                                                                  | others {'A', 'C', 'F'}
**subok**       | if *True* then sub-classes        bool          `"subok":false` (*default*)
                | will be passed-through               
**ndmin**       minimum number of dimensions        int           `"ndmin":0` (*default*)
=============== =================================== ============= =============================

Here is a simple example with np.array and extras:
::

	 loc://{"name":"my_ndarray","type":"np.array","init":[1,2,3,4],"extras": {"dtype":"float64", "copy":false, "order":"C", "ndmin":0, "subok":true}}



Using `numpy.zeros`, `numpy.empty`, or `numpy.ones` built in functions:
#######################################################################

One of the following options must be specified in the "type" value in the channel address:

* For `numpy.zeros`:

- `"type":"zeros"`
- `"type":"np.zeros"`
- `"type":"numpy.zeros"`

* For `numpy.empty`:

- `"type":"empty"`
- `"type":"np.empty"`
- `"type":"numpy.empty"`

* For `numpy.ones`:

- `"type":"ones"`
- `"type":"np.ones"`
- `"type":"numpy.ones"`

The following extra attributes can be specified in the "extras" dictionary in the channel address. These attributes will be passed in the built in functions: `numpy.zeros`, or `numpy.empty`, or `numpy.ones` as parameters when creating the `numpy.ndarray`. If no attributes are specified, these functions will use their default values to create a `numpy.ndarray`.


* Extra Attributes for numpy.zeros, numpy.empty and numpy.ones - they are the same:

=============== ====================================================== ============== ==============================
Attributes      Description                                            Type           Format Example
=============== ====================================================== ============== ==============================
**shape**       shape of the new array                                 tuple of ints  | `"shape":[2,3]`
                                                                       int            | `"shape":2`
**dtype**       desired data-type for the array                        np.dtype       | `"dtype":"float64"` (*default*)
                                                                                      | `"dtype":"uint8"`
**order**       | where to store multi-dimensional data in 
                | row-major (C-style) or col,umn major (Fortran-style)		      | `"order":"C"` (*default*)
                | order in memory                                      string         | `"order":"F"` 
=============== ====================================================== ============== ==============================

Here are a couple of simple examples with np.zeros and np.ones + extras:
::

	 loc://{"name":"my_ndarray","type":"np.zeros","init":[0],"extras": {"shape":[2,3]}}
	
	 loc://{"name":"my_ndarray","type":"np.ones","init":[1],"extras": {"shape":[2,3]}}



Using numpy.ndarray low-level method:
#######################################

.. note:: This method is not recomended to be used for creating a ndarray. The attributes below will be used for instantiating an array with the numpy.ndarray class.

One of the following options must be specified in the "type" value in the channel address:

* `"type":"ndarray"`
* `"type":"np.ndarray"`
* `"type":"numpy.ndarray"`

The following extra attributes be specified in the "extras" dictionary in the channel address. These attributes will be passed in the low-level method: `numpy.ndarray`as parameters when instantiating a `numpy.ndarray`. If no attributes are specified, this method will use its default values to create a `numpy.ndarray` with random numbers. 

* Extra Attributes for numpy.ndarray:

=============== ====================================================== ================== ==============================
Attributes      Description                                            Type               Format Example
=============== ====================================================== ================== ==============================
**shape**       shape of the new array                                 tuple of ints      | `"shape":[2,3]`
**dtype**       desired data-type for the array                        np.dtype           | `"dtype":"float64"`
**buffer**      | used to fill the array with data                     | object exposing  | `"buffer":[1,2,3]`
                                                                       | buffer interface | the buffer will be 
                                                                                          | converted into an ndarray 
                                                                                          | object internally
**offset**      | offset of array data in buffer                       int                | `"offset":2`
**strides**     | strides of data in memory                            tuple of ints      | `"strides":[2,2]`
**order**       | where to store multi-dimensional data in 
                | row-major (C-style) or col,umn major (Fortran-style)		          | `"order":"C"` (*default*)
                | order in memory                                      string             | `"order":"F"` 
=============== ====================================================== ================== ==============================

Here is a simple example with np.ndarray and extras:
::

	 loc://{"name":"my_ndarray","type":"np.ndarray","init":[1,2,3,4],"extras": {"shape":[2,3],"dtype":"float64", "buffer":[[1,2,3],[1,2,3]]}}


------------


Simple Local Data Plugin Example
---------------------------------


The picture below represents a simple example using the Local Data Plugin, where a Waveform Curve Editor has two local data plugin channels::

	loc://{"name":"y", "type":"np.array","init":[1,2,3,4,5,6]}

	loc://{"name":"x", "type":"np.array","init":[1,2,3,4,5,6]}

Right below the Waveform Curve Editor widget, there are two other widgets connected to the 'x' and 'y' local variable respectively::

	
	X-values: loc://{"name":"x"}
	Y-values: loc://{"name":"y"}

Data can be updated in the two X and Y-values widgets and the Waveform Curve Editor will receive the new data and change the curve accordingly. 



*Waveform Curve Example with ndarrays fro X and Y values*

.. image:: ../_static/data_plugins/waveform_curve_local_plugin.png
   :width: 600pt
   :align: center


---------------

Miscellaneous
-------------

* If precision is not sent through the "extras", and it is set to receive the precision from the PV (Process Variable), the Local Data Plugin will match the precision from the values inserted by the users in the widgets.

* See `validate json <https://jsonlint.com>`_ to help validate a channel address.



