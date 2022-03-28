from qtpy.QtCore import QModelIndex, QVariant, Slot
from .baseplot_table_model import BasePlotCurvesModel
from .baseplot_curve_editor import BasePlotCurveEditorDialog


class ArchiverPlotCurvesModel(BasePlotCurvesModel):
    """ This is the data model used by the archiver appliance plot curve editor.
    It basically acts as a go-between for the curves in a plot, and
    QTableView items.
    """

    def __init__(self, plot, parent=None):
        super(ArchiverPlotCurvesModel, self).__init__(plot, parent=parent)
        self._column_names = ("ChannelName", ) + self._column_names

    def get_data(self, column_name, curve):
        if column_name == "ChannelName":
            if curve.channelName is None:
                return QVariant()
            return str(curve.channelName)
        return super(ArchiverPlotCurvesModel, self).get_data(column_name,
                                                             curve)

    def set_data(self, column_name, curve, value):
        if column_name == "ChannelName":
            curve.channelName = str(value)
        else:
            return super(ArchiverPlotCurvesModel, self).set_data(
                column_name=column_name, curve=curve, value=value)
        return True

    def append(self, address=None, name=None, color=None):
        self.beginInsertRows(QModelIndex(), len(self._plot._curves),
                             len(self._plot._curves))
        self._plot.addYChannel(address, name, color)
        self.endInsertRows()

    def removeAtIndex(self, index):
        self.beginRemoveRows(QModelIndex(), index.row(), index.row())
        self._plot.removeChannelAtIndex(index.row())
        self.endRemoveRows()


class ArchiverPlotCurveEditorDialog(BasePlotCurveEditorDialog):
    """ArchiverPlotCurveEditorDialog is a QDialog that is used in Qt Designer
    to edit the properties of the curves in a waveform plot.  This dialog is
    shown when you double-click the plot, or when you right click it and
    choose 'edit curves'.

    This thing is mostly just a wrapper for a table view, with a couple
    buttons to add and remove curves, and a button to save the changes."""
    TABLE_MODEL_CLASS = ArchiverPlotCurvesModel

    def __init__(self, plot, parent=None):
        super(ArchiverPlotCurveEditorDialog, self).__init__(plot, parent)
        self.setup_delegate_columns(index=2)

    @Slot(int)
    def fillAxisData(self, tab_index, axis_name_col_index=3):
        super(ArchiverPlotCurveEditorDialog, self).fillAxisData(tab_index, axis_name_col_index=axis_name_col_index)
