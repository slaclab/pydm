from qtpy.QtCore import QModelIndex, QVariant
from .baseplot_table_model import BasePlotCurvesModel
from .baseplot_curve_editor import (BasePlotCurveEditorDialog,
                                    RedrawModeColumnDelegate)


class PyDMWaveformPlotCurvesModel(BasePlotCurvesModel):
    """ This is the data model used by the waveform plot curve editor.
    It basically acts as a go-between for the curves in a plot, and
    QTableView items.
    """

    def __init__(self, plot, parent=None):
        super(PyDMWaveformPlotCurvesModel, self).__init__(plot, parent=parent)
        self._column_names = ('Y Channel', 'X Channel') + self._column_names
        self._column_names += ('Redraw Mode', )

    def get_data(self, column_name, curve):
        if column_name == "Y Channel":
            if curve.y_address is None:
                return QVariant()
            return str(curve.y_address)
        elif column_name == "X Channel":
            if curve.x_address is None:
                return QVariant()
            return str(curve.x_address)
        elif column_name == "Redraw Mode":
            return curve.redraw_mode
        return super(PyDMWaveformPlotCurvesModel, self).get_data(
            column_name, curve)

    def set_data(self, column_name, curve, value):
        if column_name == "Y Channel":
            curve.y_address = str(value)
        elif column_name == "X Channel":
            curve.x_address = str(value)
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

    def __init__(self, plot, parent=None):
        super(WaveformPlotCurveEditorDialog, self).__init__(plot, parent)

        self.setup_delegate_columns(index=3)
        redraw_mode_delegate = RedrawModeColumnDelegate(self)
        self.table_view.setItemDelegateForColumn(8, redraw_mode_delegate)
