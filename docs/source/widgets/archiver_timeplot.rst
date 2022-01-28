#######################
Archiver Appliance Enabled Time Plots
#######################

Time plots can be augmented with the ability to automatically request archived data from an instance
of the EPICS archiver appliance if such an instance is available to the user.

In order to use this functionality, the environment variable PYDM_ARCHIVER_URL must be set to point to
the archiver appliance instance. For example:
::
    export PYDM_ARCHIVER_URL=http://lcls-archapp.slac.stanford.edu

Archiver time plots will then be able to be created in designer through the usual drag and drop flow. The
curve editor can be used to select which curves to plot archived data using the archive data drop-down.
These plots can also be created via python code directly.

#######################
PyDMArchiverTimePlot
#######################

.. autoclass:: pydm.widgets.archiver_time_plot.PyDMArchiverTimePlot
   :members:
   :inherited-members:
   :show-inheritance:

#######################
ArchivePlotCurveItem
#######################

.. autoclass:: pydm.widgets.archiver_time_plot.ArchivePlotCurveItem
   :members:
   :inherited-members:
   :show-inheritance:
