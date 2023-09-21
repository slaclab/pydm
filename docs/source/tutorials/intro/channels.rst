.. _Channel:

Channels
========

**Channels** are the bridge between PyDM Widgets and the different Data Plugins
provided.

Usually channels are specified in the following format:

.. code-block:: python

   <protocol>://<channel address>

Where ``protocol`` is a unique identifier for a given Data Plugin used with PyDM
and ``channel address`` will vary depending on the data plugin. Every plugin
should document the expected address format for users.

Here are some examples:

.. code-block:: python

   ca://MTEST:Float

Where ``ca`` means the Channel Access plugin and ``MTEST:Float`` is the PV name in this case.

Another example is the Archiver Appliance plugin in which channels are specified as:

.. code-block:: python

   archiver://pv=test:pv:123&donotchunk

In which everything in the ``channel address`` section is the same as what is sent
to the ``retrieval`` part of the Archiver as specified at the **Retrieving data**
**using other tools** section of the `Archiver Appliance User Guide <https://slacmshankar.github.io/epicsarchiver_docs/userguide.html>`_