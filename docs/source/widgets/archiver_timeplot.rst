#####################################
Archiver Appliance Enabled Time Plots
#####################################

Time plots can be augmented with the ability to automatically request archived data from an instance
of the EPICS archiver appliance if such an instance is available to the user.

In order to use this functionality, the environment variable PYDM_ARCHIVER_URL must be set to point to
the archiver appliance instance. For example:

    export PYDM_ARCHIVER_URL=http://lcls-archapp.slac.stanford.edu

These plots can then be created with python code, or using designer.

* Creating in Designer


After setting the above environment variable, archiver time plots will then be able to be created in designer through
the usual drag and drop flow. Upon opening designer, there will now be a plotting widget called PyDMArchiverTimePlot
available for use. The channel connections can be created in the same way as a regular
time plot, no need to preface anything with "archiver://", the requests to archiver will happen
automatically upon running the plot and panning the x-axis to the left, or zooming out.

One property that will be particularly useful to set is the timeSpan. This value (in seconds) will determine how much
data to request from archiver upon plot initialization. For example, setting it to 600 will cause the plot to backfill
with the last 10 minutes worth of data for the plotted values anytime the plot is opened. If more data is needed after
starting up the plot, it can be requested as described below.

.. figure:: /_static/widgets/archiver_time_plot/archiver_time_plot_designer.png
   :scale: 100 %
   :align: center
   :alt: Creating PyDMArchiverTimePlot in Qt Designer


* Plot Usage

Upon opening the plot, it will plot the requested amount of archived data. It will then behave like a regular time plot
with live data being added to the plot. If more archived data would be useful, requests can be made by either panning
the x-axis to the left, or zooming out on the entire plot. This will automatically generate a call to the archiver
appliance that will add data to the plot once it is received.

Note that there is a property on the plot called bufferSize which determines how many data points can be displayed on
the plot at once. If the request for archived data would return an amount greater than that buffer, it will convert
to a request for optimized data which includes the average, min, and max of each data point returned. These will then
be plotted as bars to show the full range of data represented by each point. As an example - with a buffer size
of 365, a request for a year of data for a PV that updates every second would return roughly
365 points each of which will contain the min and max of that day's data to plot the full range represented.

.. figure:: /_static/widgets/archiver_time_plot/archiver_plot.gif
   :scale: 100 %
   :align: center
   :alt: Requesting additional data from a live plot


#######################
PyDMArchiverTimePlot
#######################

.. autoclass:: pydm.widgets.archiver_time_plot.PyDMArchiverTimePlot
   :members:
   :show-inheritance:

#######################
ArchivePlotCurveItem
#######################

.. autoclass:: pydm.widgets.archiver_time_plot.ArchivePlotCurveItem
   :members:
   :show-inheritance:

#######################
FormulaCurveItem
#######################

.. autoclass:: pydm.widgets.archiver_time_plot.FormulaCurveItem
   :members:
   :show-inheritance:
