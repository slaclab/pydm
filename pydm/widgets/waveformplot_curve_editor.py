from qtpy.QtCore import QModelIndex, QObject, QVariant
from .baseplot_table_model import BasePlotCurvesModel
from .baseplot_curve_editor import (BasePlotCurveEditorDialog, ColorColumnDelegate,
                                    PlotStyleColumnDelegate, RedrawModeColumnDelegate)
from .waveformplot import PyDMWaveformPlot


class PyDMWaveformPlotCurvesModel(BasePlotCurvesModel):
    """ This is the data model used by the waveform plot curve editor.
    It basically acts as a go-between for the curves in a plot, and
    QTableView items.
    """

    def __init__(self, plot, parent=None):
        super(PyDMWaveformPlotCurvesModel, self).__init__(plot, parent=parent)
        self._column_names = ('Y Channel', 'X Channel', 'Style') + self._column_names
        self._column_names += ('Redraw Mode',)

    def get_data(self, column_name, curve):
        if column_name == "Y Channel":
            if curve.y_address is None:
                return QVariant()
            return str(curve.y_address)
        elif column_name == "X Channel":
            if curve.x_address is None:
                return QVariant()
            return str(curve.x_address)
        elif column_name == "Style":
            return curve.plot_style
#        elif column_name == "Bar Width":
#            return curve.bar_width
#        elif column_name == "Upper Threshold":
#            return curve.upper_threshold
#        elif column_name == "Lower Threshold":
#            return curve.lower_threshold
        elif column_name == "Redraw Mode":
            return curve.redraw_mode
        return super(PyDMWaveformPlotCurvesModel, self).get_data(
            column_name, curve)

    def set_data(self, column_name, curve, value):
        if column_name == "Y Channel":
            curve.y_address = str(value)
        elif column_name == "X Channel":
            curve.x_address = str(value)
        elif column_name == "Style":
            curve.plot_style = str(value)
        elif column_name == "Redraw Mode":
            curve.redraw_mode = int(value)
        else:
            return super(PyDMWaveformPlotCurvesModel, self).set_data(
                column_name=column_name, curve=curve, value=value)
        return True

    def append(self, y_address=None, x_address=None, name=None, color=None):
        self.beginInsertRows(QModelIndex(), len(self._plot._curves),
                             len(self._plot._curves))
        self._plot.addChannel(y_address, x_address, name, color)
        self.endInsertRows()

    def removeAtIndex(self, index):
        self.beginRemoveRows(QModelIndex(), index.row(), index.row())
        self._plot.removeChannelAtIndex(index.row())
        self.endRemoveRows()


class WaveformPlotCurveEditorDialog(BasePlotCurveEditorDialog):
    """WaveformPlotCurveEditorDialog is a QDialog that is used in Qt Designer
    to edit the properties of the curves in a waveform plot.  This dialog is
    shown when you double-click the plot, or when you right click it and
    choose 'edit curves'.

    This thing is mostly just a wrapper for a table view, with a couple
    buttons to add and remove curves, and a button to save the changes."""
    TABLE_MODEL_CLASS = PyDMWaveformPlotCurvesModel

    def __init__(self, plot: PyDMWaveformPlot, parent: QObject = None):
        super().__init__(plot, parent)

        redraw_mode_delegate = RedrawModeColumnDelegate(self)
        self.table_view.setItemDelegateForColumn(self.table_model.getColumnIndex("Redraw Mode"), redraw_mode_delegate)

        threshold_color_delegate = ColorColumnDelegate(self)
        self.table_view.setItemDelegateForColumn(self.table_model.getColumnIndex('Threshold Color'),
                                                 threshold_color_delegate)

        plot_style_delegate = PlotStyleColumnDelegate(self, self.table_model, self.table_view)
        self.table_view.setItemDelegateForColumn(self.table_model.getColumnIndex("Style"), plot_style_delegate)

        plot_style_delegate.toggleColumnVisibility()
#        plot_style_delegate.hideColumns(hide_line_columns=True, hide_bar_columns=True)
#        if len(plot.curves) > 0:
#            for curve in plot.curves:
#                plot_style = self.table_model.get_data("Style", curve)
#                if plot_style is None or plot_style != 'Line':
#                    plot_style_delegate.hideColumns(hide_line_columns=False)
#                elif plot_style == 'Bar':
#                    plot_style_delegate.hideColumns(hide_bar_columns=False)
#        else:
#            plot_style_delegate.hideColumns(False, True)  # Show line columns as a default
