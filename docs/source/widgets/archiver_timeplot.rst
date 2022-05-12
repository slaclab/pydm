#####################################
Archiver Appliance Enabled Time Plots
#####################################

Time plots can be augmented with the ability to automatically request archived data from an instance
of the EPICS archiver appliance if such an instance is available to the user.

In order to use this functionality, the environment variable PYDM_ARCHIVER_URL must be set to point to
the archiver appliance instance. For example:

::
    export PYDM_ARCHIVER_URL=http://lcls-archapp.slac.stanford.edu

Archiver time plots will then be able to be created in designer through the usual drag and drop flow. Upon
opening designer, you will notice that the time plot is now called PyDMArchiverTimePlot indicating it can
be used with the archiver appliance. The channel connections can be created in the same way as a regular
time plot, no need to preface anything with "archiver://", the requests to archiver will happen
automatically upon running the plot and panning the x-axis to the left, or zooming out.


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
