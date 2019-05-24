===============
Migration Guide
===============

Not often we break code at PyDM but sometimes we gotta break the eggs to make
a tasteful omelette.

In this section we will try to minimize the pain to migrate to newer versions
of the code when we do break an existing API.


Changes from PyDM 1.x to 2.x
============================

PyDM 2.x introduces the concept of structured data which drove a major refactor
at the Data Plugins. Part of this refactor allow developers to create new data
plugins with fewer lines of code since most of the administrative tasks are
handled by the base classes now.

Also, now the Data Plugins will be able to hint to widgets where to find the
data for key components such as ``value``, ``connection status``, ``write access status``, and others,
by providing an introspection dictionary which points the widgets for keys in the data dictionary
that is provided by this data plugin.

Data Plugins
------------

The multiple signals (``connection_state_signal``, ``new_value_signal``,
``new_severity_signal`` and others) are now deprecated in favor of the new :ref: `data_store`.
Existing Data Plugins must be modified to no longer emit signals but instead add the proper information into the
``data`` dictionary.



Example
++++++++

.. code-block:: python

    self.new_value_signal[np.ndarray].emit(value)
    # becomes:
    self.data[DataKeys.VALUE] = value

