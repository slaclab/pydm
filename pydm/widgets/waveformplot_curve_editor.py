from qtpy.QtCore import QModelIndex, Qt, QVariant
from qtpy.QtWidgets import QComboBox, QStyledItemDelegate
from .baseplot_table_model import BasePlotCurvesModel
from .baseplot_curve_editor import BasePlotCurveEditorDialog, ColorColumnDelegate, RedrawModeColumnDelegate


class PyDMWaveformPlotCurvesModel(BasePlotCurvesModel):
    """ This is the data model used by the waveform plot curve editor.
    It basically acts as a go-between for the curves in a plot, and
    QTableView items.
    """

    def __init__(self, plot, parent=None):
        super(PyDMWaveformPlotCurvesModel, self).__init__(plot, parent=parent)
        self._column_names = ('Y Channel', 'X Channel', 'Style') + self._column_names
        self._column_names += ('Bar Width', 'Upper Threshold', 'Lower Threshold', 'Threshold Color', 'Redraw Mode')

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
        elif column_name == "Bar Width":
            return curve.bar_width
        elif column_name == "Upper Threshold":
            return curve.upper_threshold
        elif column_name == "Lower Threshold":
            return curve.lower_threshold
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
        elif column_name == "Bar Width":
            curve.bar_width = float(value)
        elif column_name == "Upper Threshold":
            curve.upper_threshold = float(value)
        elif column_name == "Lower Threshold":
            curve.lower_threshold = float(value)
        elif column_name == "Threshold Color":
            print(f'setting threshold color to: {value} and: {value.name()}')
            curve.threshold_color = value
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

    line_columns_to_toggle = ('Line Style', 'Line Width', 'Symbol', 'Symbol Size')
    bar_columns_to_toggle = ('Bar Width', 'Upper Threshold', 'Lower Threshold', 'Threshold Color')

    def __init__(self, plot, parent=None):
        super(WaveformPlotCurveEditorDialog, self).__init__(plot, parent)

        redraw_mode_delegate = RedrawModeColumnDelegate(self)
        self.table_view.setItemDelegateForColumn(self.table_model.getColumnIndex("Redraw Mode"), redraw_mode_delegate)

        threshold_color_delegate = ColorColumnDelegate(self)
        self.table_view.setItemDelegateForColumn(self.table_model.getColumnIndex('Threshold Color'),
                                                 threshold_color_delegate)

        plot_style_delegate = WavformPlotStyleColumnDelegate(self, self.table_model, self.table_view,
                                                             self.line_columns_to_toggle, self.bar_columns_to_toggle)
        self.table_view.setItemDelegateForColumn(self.table_model.getColumnIndex("Style"), plot_style_delegate)

        if len(plot.curves) > 0:
            plot_style = self.table_model.get_data("Style", plot.curveAtIndex(0))
            hide_line_columns = plot_style is not None and plot_style != 'Line'
            hide_bar_columns = plot_style != 'Bar'
            for column in self.line_columns_to_toggle:
                self.table_view.setColumnHidden(self.table_model.getColumnIndex(column), hide_line_columns)
            for column in self.bar_columns_to_toggle:
                self.table_view.setColumnHidden(self.table_model.getColumnIndex(column), hide_bar_columns)
        else:
            for column in self.bar_columns_to_toggle:
                self.table_view.setColumnHidden(self.table_model.getColumnIndex(column), True)


class WavformPlotStyleColumnDelegate(QStyledItemDelegate):

    def __init__(self, parent, table_model, table_view, line_columns, bar_columns):
        super(WavformPlotStyleColumnDelegate, self).__init__(parent)
        self.table_model = table_model
        self.table_view = table_view
        self.line_columns_to_toggle = line_columns
        self.bar_columns_to_toggle = bar_columns

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(('Line', 'Bar'))
        return editor

    def setEditorData(self, editor, index):
        val = str(index.model().data(index, Qt.EditRole))
        editor.setCurrentText(val)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)
        if editor.currentText() is not None:
            hide_line_columns = editor.currentText() != 'Line'
            hide_bar_columns = editor.currentText() != 'Bar'
            for column in self.line_columns_to_toggle:
                self.table_view.setColumnHidden(self.table_model.getColumnIndex(column), hide_line_columns)
            for column in self.bar_columns_to_toggle:
                self.table_view.setColumnHidden(self.table_model.getColumnIndex(column), hide_bar_columns)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
