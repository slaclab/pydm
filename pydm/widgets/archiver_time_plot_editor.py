from typing import Any, Optional
from qtpy.QtCore import Qt, QModelIndex, QObject
from qtpy.QtGui import QColor
from .archiver_time_plot import ArchivePlotCurveItem
from .baseplot import BasePlot, BasePlotCurveItem
from .baseplot_table_model import BasePlotCurvesModel
from .baseplot_curve_editor import BasePlotCurveEditorDialog, PlotStyleColumnDelegate


class PyDMArchiverTimePlotCurvesModel(BasePlotCurvesModel):
    """Model used in designer for editing archiver time plot curves."""

    def __init__(self, plot: BasePlot, parent: Optional[QObject] = None):
        super().__init__(plot, parent=parent)
        self._column_names = ("Channel", "Live Data", "Archive Data") + self._column_names

        self.checkable_cols = {self.getColumnIndex("Live Data"), self.getColumnIndex("Archive Data")}

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Return flags that determine how users can interact with the items in the table"""
        if not index.isValid():
            return Qt.NoItemFlags

        flags = super().flags(index)
        if index.column() in self.checkable_cols:
            flags = Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable
        return flags

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.CheckStateRole and index.column() in self.checkable_cols:
            value = super().data(index, Qt.DisplayRole)
            return Qt.Checked if value else Qt.Unchecked
        elif index.column() not in self.checkable_cols:
            return super().data(index, role)
        return None

    def get_data(self, column_name: str, curve: BasePlotCurveItem) -> Any:
        """Get data for the input column name"""
        if column_name == "Channel":
            if hasattr(curve, "address"):
                return curve.address
            elif hasattr(curve, "formula"):
                return curve.formula
            # We are either a Formula or a PV (for now at leasts)
            else:
                return None

        elif column_name == "Live Data":
            return bool(curve.liveData)
        elif column_name == "Archive Data":
            return bool(curve.use_archive_data)
        return super().get_data(column_name, curve)

    def setData(self, index, value, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        elif role == Qt.CheckStateRole and index.column() in self.checkable_cols:
            return super().setData(index, value, Qt.EditRole)
        elif index.column() not in self.checkable_cols:
            return super().setData(index, value, role)
        return None

    def set_data(self, column_name: str, curve: ArchivePlotCurveItem, value: Any) -> bool:
        """Set data on the input curve for the given name and value. Return true if successful."""
        if column_name == "Channel":
            curve.address = str(value)
        elif column_name == "Live Data":
            curve.liveData = bool(value)
        elif column_name == "Archive Data":
            curve.use_archive_data = bool(value)
        else:
            return super().set_data(column_name=column_name, curve=curve, value=value)
        return True

    def append(self, address: Optional[str] = None, name: Optional[str] = None, color: Optional[QColor] = None) -> None:
        """Add a row for a curve with the input address"""
        self.beginInsertRows(QModelIndex(), len(self._plot._curves), len(self._plot._curves))
        self._plot.addYChannel(address, name, color)
        self.endInsertRows()

    def removeAtIndex(self, index: QModelIndex):
        """Remove the row at the input index"""
        self.beginRemoveRows(QModelIndex(), index.row(), index.row())
        self._plot.removeYChannelAtIndex(index.row())
        self.endRemoveRows()


class ArchiverTimePlotCurveEditorDialog(BasePlotCurveEditorDialog):
    """ArchiverTimePlotCurveEditorDialog is a QDialog that is used in Qt Designer
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
