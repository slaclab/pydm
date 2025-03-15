from qtpy.QtCore import QModelIndex, QObject
from typing import Optional
from .baseplot_table_model import BasePlotCurvesModel
from .baseplot_curve_editor import BasePlotCurveEditorDialog, ColorColumnDelegate, PlotStyleColumnDelegate
from .timeplot import PyDMTimePlot


class PyDMTimePlotCurvesModel(BasePlotCurvesModel):
    def __init__(self, plot, parent=None):
        super().__init__(plot, parent=parent)
        self._column_names = ("Channel", "Style") + self._column_names

    def get_data(self, column_name, curve):
        if column_name == "Channel":
            if curve.address is None:
                return None
            return str(curve.address)
        elif column_name == "Style":
            return curve.plot_style
        return super().get_data(column_name, curve)

    def set_data(self, column_name, curve, value):
        if column_name == "Channel":
            curve.address = str(value)
        elif column_name == "Style":
            curve.plot_style = str(value)
        else:
            return super().set_data(column_name=column_name, curve=curve, value=value)
        return True

    def append(self, address=None, name=None, color=None):
        self.beginInsertRows(QModelIndex(), len(self._plot._curves), len(self._plot._curves))
        self._plot.addYChannel(address, name, color)
        self.endInsertRows()

    def removeAtIndex(self, index):
        self.beginRemoveRows(QModelIndex(), index.row(), index.row())
        self._plot.removeYChannelAtIndex(index.row())
        self.endRemoveRows()


class TimePlotCurveEditorDialog(BasePlotCurveEditorDialog):
    """TimePlotCurveEditorDialog is a QDialog that is used in Qt Designer
    to edit the properties of the curves in a waveform plot.  This dialog is
    shown when you double-click the plot, or when you right click it and
    choose 'edit curves'.

    This thing is mostly just a wrapper for a table view, with a couple
    buttons to add and remove curves, and a button to save the changes."""

    TABLE_MODEL_CLASS = PyDMTimePlotCurvesModel

    def __init__(self, plot: PyDMTimePlot, parent: Optional[QObject] = None):
        super().__init__(plot, parent)

        threshold_color_delegate = ColorColumnDelegate(self)
        self.table_view.setItemDelegateForColumn(
            self.table_model.getColumnIndex("Limit Color"), threshold_color_delegate
        )

        plot_style_delegate = PlotStyleColumnDelegate(self, self.table_model, self.table_view)
        self.table_view.setItemDelegateForColumn(self.table_model.getColumnIndex("Style"), plot_style_delegate)
        plot_style_delegate.toggleColumnVisibility()
