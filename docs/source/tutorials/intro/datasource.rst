Data Sources
============

PyDM is shipped with a couple of data plugins:

- EPICS
- Archiver

EPICS
-----

This plugin is used to allow PyDM Widgets to access to Channel Access process variables and interact with them.

========    ==============  ================
Protocol    Address Format  Example
========    ==============  ================
ca          ca://<PV NAME>  ca://MTEST:Float
========    ==============  ================


For this particular data plugin, three options are available for the Python interface to Channel Access.

- PyEpics: http://pyepics.github.io/pyepics/

- pyca: https://github.com/slaclab/pyca

- caproto: https://nsls-ii.github.io/caproto/

.. warning::
   By default, PyEpics is selected unless configured through the ``PYDM_EPICS_LIB`` environment variable.

   Possible values are ``PYEPICS``,  ``PYCA``, and ``CAPROTO``.

Archiver
--------

This plugin is used to allow PyDM Widgets to read data from Archiver Appliance.

While still crude, this data plugin works and has been tested against a real instance of the Archiver.

Basically a HTTP request is sent to the archiver appliance and the address is used to form the parameters for the data
retrieval.  Warning: The request is sent synchronously, meaning it will block your application until the request is
complete.  This limitation will be removed in a future version.

========    ===================  ====================================
Protocol    Address Format       Example
========    ===================  ====================================
archiver    archiver://<PARAMS>  archiver://pv=test:pv:123&donotchunk
========    ===================  ====================================

.. warning::
   Different facilities must set the ``PYDM_ARCHIVER_URL`` environment variable to point to their Archiver Appliance
   location or the retrieval application. If not set, this variable will point to SLAC's Archiver Appliance URL, which
   is almost certainly not what you want.

   If your Archiver Retrieval is hosted under the following address ``http://lcls-archapp.slac.stanford.edu/retrieval/...``
   set the variable to ``http://lcls-archapp.slac.stanford.edu``.

   The remaining parts of the URL will be dealt with at the Data Plugin level and should not be a concern.

