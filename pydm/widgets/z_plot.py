import typing
import logging
import pyqtgraph as pg
from functools import partial
from qtpy.QtWidgets import QWidget, QLabel, QVBoxLayout
from pydm.widgets import PyDMScatterPlot
from .channel import PyDMChannel

logger = logging.getLogger(__name__)


class PyDMZPlot(QWidget):
    """
      The PyDMZPlot, is a plotting widget that couples a PyDMScatterPlot and a pyqtgraph PlotWidget to create a plot
      widget that has a corresponding dynamic diagram that can represent a positional direction of a machine
      or facility.

      Parameters
      ----------
      parent : QWidget
          The parent widget for the plot
      y_axis_channels : str, optional
          The channels to be used by the widget.
      x_axis_channels : str, optional
          The channels to be used by the widget.
      symbol_list : list, optional
          The symbols to be used by the data points in the diagram.
      y_axis_symbol : str, optional
          The symbol to be used by the y-axis data points.
      """

    def __init__(self, parent=None, y_axis_channels=None, x_axis_channels=None, symbol_list=[], y_axis_symbol='o'):
        super().__init__()
        if y_axis_channels is not None:
            self._y_axis_channels = y_axis_channels
        else:
            self._y_axis_channels = list()

        if x_axis_channels is not None:
            self._x_axis_channels = x_axis_channels
        else:
            self._x_axis_channels = list()

        self._symbol_list = symbol_list
        self._y_axis_symbol = y_axis_symbol
        self.z_values = []
        self.x_points_table = {}
        self.x_points = []
        self.y_points = []

        # ui elements
        self.text = None
        self.label = None
        self.z_plot = None
        self.accelerator_diagram = None

        # build ui
        self.ui_components()
        self.show()

    def ui_components(self):
        """
        creates the layout and widgets for the z-plot
        """
        self.setGeometry(100, 100, 800, 500)
        self.text = 'z-plot'
        self.label = QLabel(self.text)
        self.label.setMinimumWidth(130)
        self.label.setWordWrap(True)

        pg.setConfigOptions(antialias=True)

        self.z_plot = PyDMScatterPlot()

        for i in range(0, len(self.y_axis_channels)):
            self.z_plot.addChannel(y_channel=self._y_axis_channels[i],
                                   x_channel=self._x_axis_channels[i], symbol=self._y_axis_symbol)

        self.accelerator_diagram = pg.PlotWidget()
        self.accelerator_diagram.setMouseEnabled(x=True, y=False)
        self.accelerator_diagram.getPlotItem().hideAxis('left')
        self.accelerator_diagram.getPlotItem().hideAxis('bottom')

        for view in self.z_plot.plotItem.stackedViews:
            view.setXLink(self.accelerator_diagram)

        # Get values from the x channels and populate the data into the accelerator diagram
        self.establish_channel_connections()

        z_plot_layout = QVBoxLayout()
        z_plot_layout.setContentsMargins(0, 0, 0, 0)
        z_plot_layout.setSpacing(0)

        z_plot_layout.addWidget(self.z_plot, stretch=3)
        z_plot_layout.addWidget(self.accelerator_diagram, stretch=1)
        #z_plot_layout.addWidget(self.label)

        self.setLayout(z_plot_layout)

    def establish_channel_connections(self):
        """
        Sets up the pydm channels for the given x_axis addresses.
        """
        channels = []
        for address in self._x_axis_channels:
            new_channel = PyDMChannel(address=address, value_slot=partial(self.update_x_values, address))
            new_channel.connect()
            channels.append(new_channel)

        return channels

    def update_x_values(self, new_value, address):
        """
        Update the x values of the self.accelerator_diagram (pyqtgraph PlotWidget) plot.
        """
        self.x_points_table.update({address: new_value})
        self.x_points.clear()

        for value in self.x_points_table:
            self.x_points.append(value)

        self.y_points = [1] * len(self.x_points)

        if len(self._symbol_list) == len(self.x_points):
            symbols = self._symbol_list
        else:
            logger.debug("The length of the list of symbols did not match the "
                         "number of x points so the default symbol was set.")
            symbols = 's'

        self.accelerator_diagram.clear()
        self.accelerator_diagram.plot(y=self.y_points, x=self.x_points, symbol=symbols, symbolSizes=14)

    @property
    def y_axis_channels(self):
        """
        list of channels to be plotted.

        Returns
        -------
        list of strings
        """

        return self._y_axis_channels

    @y_axis_channels.setter
    def y_axis_channels(self, channels):
        """
        list of channels to be plotted.

        Parameters
        -------
        channels : list of strings
        """

        if self._y_axis_channels != channels:
            self._y_axis_channels = channels

            if len(self._y_axis_channels) == len(self.x_axis_channels):
                self.z_plot.clearCurves()
                for i in range(0, len(self.y_axis_channels)):
                    self.z_plot.addChannel(y_channel=self._y_axis_channels[i],
                                           x_channel=self._x_axis_channels[i], symbol=self._y_axis_symbol)

                for view in self.z_plot.plotItem.stackedViews:
                    view.setXLink(self.accelerator_diagram)

    @property
    def x_axis_channels(self):
        """
        list of channels to be plotted.

        Returns
        -------
        list of strings
        """

        return self._x_axis_channels

    @x_axis_channels.setter
    def x_axis_channels(self, channels):
        """
        list of channels to be plotted.

        Parameters
        -------
        channels : list of strings
        """

        if self._x_axis_channels != channels:
            self._x_axis_channels = channels

            # update the accelerator diagram
            self.establish_channel_connections()

            # update the z plot graph if both the x and y list are the same size.
            if len(self._y_axis_channels) == len(self.x_axis_channels):
                self.z_plot.clearCurves()
                for i in range(0, len(self.y_axis_channels)):
                    self.z_plot.addChannel(y_channel=self._y_axis_channels[i],
                                           x_channel=self._x_axis_channels[i], symbol=self._y_axis_symbol)

                for view in self.z_plot.plotItem.stackedViews:
                    view.setXLink(self.accelerator_diagram)

    @property
    def symbol_list(self):
        """
        list of symbols to be passed to the self.accelerator_diagram (pyqtgraph PlotWidget) plot.

        Returns
        -------
        list of strings
        """

        return self._symbol_list

    @symbol_list.setter
    def symbol_list(self, symbols):
        """
        list of symbols to be passed to the self.accelerator_diagram (pyqtgraph PlotWidget) plot.

        Parameters
        -------
        symbols : list of strings
        """

        if self._symbol_list != symbols:
            self._symbol_list = symbols
