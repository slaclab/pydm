==========
P4P Plugin
==========

The P4P data plugin is defined in ``pydm/data_plugins/p4p_plugin_component.py`` and supports the pvAccess
protocol using the `P4P package`_.

.. _P4P package: https://mdavidsaver.github.io/p4p/

Usage
-----

The P4P plugin is the default pvAccess plugin, so any address using the "pva://" protocol will be
routed to it as in the example below::

    pva://MTEST:Voltage:LI30


P4P is not currently specified as a required package of PyDM, and as such, will not be automatically included
alongside PyDM when installing it into an environment. P4P must therefore be installed manually. The versions
on conda-forge and PyPI are both supported, so feel free to choose whichever is most convenient::

    conda install -c conda-forge p4p
    pip install p4p

The choice of plugin to use can be controlled with the ``PYDM_PVA_LIB`` environment variable. As of now
P4P is the only option (and will be chosen automatically if this variable is not set) but more may be added
in the future.

Supported Types
===============

Currently this data plugin supports all `normative types`_. The values and control variables are pulled out of
the data received and sent through the existing PyDM signals to be read by widgets via the channels they are
connected to.

In order to support compatibility with all existing signals and widgets, full structured data support is not
currently possible in this version of the plugin. For example, defining a group PV using Q:Group will not
result in the named fields being sent to the widgets. Full support for structured data is planned to be supported
as part of a future release.

NTTables
--------

The plugin accepts NTTables. It will convert NTTables in python dictionaries which are then passed to the pydm widgets. 
Not all widgets will accept a dictionary (or the whole NTTable) as an input. 
A specified section of the NTTable can be passed to a those pydm widgets which do not accept dictionaries.
If the PV is passing an NTTable and the user wants to pass only a specific subfield of the NTTable this can be achieved via appending a ``/`` 
followed by the key or name of the column header of the subfield of the NTTable.
For example::

    pva://MTEST/subfield

multiple layers of subfields also works::

    pva://MTEST/sub-field/subfield_of_a_subfield

Note: subfields can be used to read and write to a subset of data from a NTTable 
so long as the type of the subset of data is accepted by the widget in question. 

Image decompression
-------------------

Image decompression is performed when image data is specified using an ``NTNDArray`` with the ``codec`` field set.
The decompression algorithm to apply will be determined by what the ``codec`` field is set to. In order
for decompression to happen, the python package for the associated codec must be installed in the environment
PyDM is running in. Since we do not want to require all of these packages to be installed alongside PyDM when they
may not all be used in many cases, they must be installed manually as needed in the same way as P4P. Each package
is available on both conda-forge and PyPI and may be installed from either.

::

    Pillow (for jpeg), blosc, lz4, bitshuffle (for bslz4)

.. _normative types: https://github.com/epics-base/normativeTypesCPP/wiki/Normative+Types+Specification


Examples
--------

A small pva testing ioc is included under ``examples/testing/pva_testing_ioc.py``. This can be run in order to
generate a couple of test PVs, which can be connected to using the example .ui file under
``examples/pva/pva.ui``.


RPC
---

The P4P data plugin also supports **remote method calls** (RPC) addresses.

RPC addresses allow for calling methods on a target IOC, and receiving back the method's result.
RPC addresses must contain arguments matching the name and data-type of those defined in the target's method.
These arguments are static and set in the widget's channel address.

RPCs can be set using a pva address in the following format::

    pva://<address>?<arg_1_name>=<arg_1_value>&<arg_2_name>=<arg_2_value>&...(pydm_pollrate=<poll_rate_float>)

"pydm_pollrate" is an optional parameter, but when included must be placed after the arg name/value pairs in the address.
When "pydm_pollrate" is not used, the last arg name/value pair must still end with a "&" character. 
(when not used, the RPC will be called once and not be polled)

Arguments are also optional. When not used, end the address with the "&" character (followed by the optional "pydm_pollrate")::

    pva://<address>&(pydm_pollrate=<poll_rate_float>)

Example RPC addresses:
    
    pva://my_address?arg1=value1&
    pva://my_address?arg1=value1&arg2=value2&pydm_pollrate=10.5
    pva://KLYS:LI12:11:ATTN_CUR&
    pva://KLYS:LI12:11:ATTN_CUR&pydm_pollrate=2.0

Additional examples of using RPCs with PyDMLabels are provided in ``examples/rpc/rpc_labels.py``.
To run examples, first make sure ``python examples/testing_ioc/rpc_testing_ioc.py`` is actively
running in another terminal.