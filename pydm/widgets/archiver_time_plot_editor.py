from typing import Any, Optional
from qtpy.QtCore import QModelIndex, QObject, QVariant
from qtpy.QtGui import QColor
from .archiver_time_plot import ArchivePlotCurveItem
from .baseplot import BasePlot
from .baseplot_table_model import BasePlotCurvesModel
from .baseplot_curve_editor import BasePlotCurveEditorDialog, PlotStyleColumnDelegate


class PyDMArchiverTimePlotCurvesModel(BasePlotCurvesModel):
    """ Model used in designer for editing archiver time plot curves. """

    def __init__(self, plot: BasePlot, parent: Optional[QObject] = None):
        super().__init__(plot, parent=parent)
        self._column_names = ("Channel", "Archive Data") + self._column_names

    def get_data(self, column_name: str, curve: ArchivePlotCurveItem) -> Any:
        """ Get data for the input column name """
        if column_name == "Channel":
            if curve.address is None:
                return QVariant()
            return str(curve.address)
        elif column_name == "Archive Data":
            return bool(curve.use_archive_data)
        return super().get_data(column_name, curve)

    def set_data(self, column_name: str, curve: ArchivePlotCurveItem, value: Any) -> bool:
        """ Set data on the input curve for the given name and value. Return true if successful. """
        if column_name == "Channel":
            curve.address = str(value)
        elif column_name == "Archive Data":
            curve.use_archive_data = bool(value)
        else:
            return super().set_data(column_name=column_name, curve=curve, value=value)
        return True

    def append(self, address: Optional[str] = None, name: Optional[str] = None, color: Optional[QColor] = None) -> None:
        """ Add a row for a curve with the input address """
        self.beginInsertRows(QModelIndex(), len(self._plot._curves), len(self._plot._curves))
        self._plot.addYChannel(address, name, color)
        self.endInsertRows()

    def removeAtIndex(self, index: QModelIndex):
        """ Remove the row at the input index """
        self.beginRemoveRows(QModelIndex(), index.row(), index.row())
        self._plot.removeYChannelAtIndex(index.row())
        self.endRemoveRows()


class ArchiverTimePlotCurveEditorDialog(BasePlotCurveEditorDialog):
    """ ArchiverTimePlotCurveEditorDialog is a QDialog that is used in Qt Designer
    to edit the properties of the curves in a waveform plot.  This dialog is
    shown when you double-click the plot, or when you right click it and
    choose 'edit curves'.

    This thing is mostly just a wrapper for a table view, with a couple
    buttons to add and remove curves, and a button to save the changes."""
    TABLE_MODEL_CLASS = PyDMArchiverTimePlotCurvesModel

    def __init__(self, plot, parent=None):
        super().__init__(plot, parent)

        plot_style_delegate = PlotStyleColumnDelegate(self, self.table_model, self.table_view)
        plot_style_delegate.hideColumns(hide_line_columns=False, hide_bar_columns=True)
