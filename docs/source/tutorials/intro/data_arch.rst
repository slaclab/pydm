.. _DataArchitecture:

Data Architecture
=================

* PyDM widgets are data-source agnostic, and communicate with the PyDM Application through Qt signals and slots.

* The PyDM application routes data between the widgets and data source plugins.

* A data source plugin speaks to a particular source of data (EPICS, HTTP, modbus, databases, etc).

* This system makes it possible to mix-and-match different data sources within the same display, using the same widget set.

.. figure:: /_static/tutorials/intro/architecture.png
   :scale: 25 %
   :align: center
   :alt: PyDM Data Plugin Architecture