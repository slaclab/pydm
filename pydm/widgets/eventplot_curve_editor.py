from qtpy.QtCore import QModelIndex
from .baseplot_table_model import BasePlotCurvesModel
from .baseplot_curve_editor import BasePlotCurveEditorDialog, PlotStyleColumnDelegate


class PyDMEventPlotCurvesModel(BasePlotCurvesModel):
    """This is the data model used by the waveform plot curve editor.
    It basically acts as a go-between for the curves in a plot, and
    QTableView items.
    """

    def __init__(self, plot, parent=None):
        super().__init__(plot, parent=parent)
        self._column_names = ("Channel", "Y Index", "X Index") + self._column_names
        self._column_names += ("Buffer Size", "Buffer Size Channel")

    def get_data(self, column_name, curve):
        if column_name == "Channel":
            if curve.address is None:
                return None
            return str(curve.address)
        elif column_name == "Y Index":
            if curve.y_idx is None:
                return None
            return curve.y_idx
        elif column_name == "X Index":
            if curve.x_idx is None:
                return None
            return curve.x_idx
        elif column_name == "Buffer Size":
            return curve.getBufferSize()
        elif column_name == "Buffer Size Channel":
            return curve.bufferSizeChannelAddress or ""
        return super().get_data(column_name, curve)

    def set_data(self, column_name, curve, value):
        if column_name == "Channel":
            curve.address = str(value)
        elif column_name == "Y Index":
            curve.y_idx = value
        elif column_name == "X Index":
            curve.x_idx = value
        elif column_name == "Buffer Size":
            curve.setBufferSize(int(value))
        elif column_name == "Buffer Size Channel":
            if len(str(value).strip()) < 1:
                value = None
            curve.bufferSizeChannelAddress = str(value)
        else:
            return super().set_data(column_name=column_name, curve=curve, value=value)
        return True

    def append(self, channel=None, y_idx=None, x_idx=None, name=None, color=None):
        self.beginInsertRows(QModelIndex(), len(self._plot._curves), len(self._plot._curves))
        self._plot.addChannel(channel, y_idx, x_idx, name, color)
        self.endInsertRows()

    def removeAtIndex(self, index):
        self.beginRemoveRows(QModelIndex(), index.row(), index.row())
        self._plot.removeChannelAtIndex(index.row())
        self.endRemoveRows()


class EventPlotCurveEditorDialog(BasePlotCurveEditorDialog):
    """EventPlotCurveEditorDialog is a QDialog that is used in Qt Designer
    to edit the properties of the curves in a waveform plot.  This dialog is
    shown when you double-click the plot, or when you right click it and
    choose 'edit curves'.

    This thing is mostly just a wrapper for a table view, with a couple
    buttons to add and remove curves, and a button to save the changes."""

    TABLE_MODEL_CLASS = PyDMEventPlotCurvesModel

    def __init__(self, plot, parent=None):
        super().__init__(plot, parent)

        plot_style_delegate = PlotStyleColumnDelegate(self, self.table_model, self.table_view)
        plot_style_delegate.hideColumns(hide_line_columns=False, hide_bar_columns=True)
