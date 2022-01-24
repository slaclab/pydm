from ...widgets.baseplot import BasePlot
from ...widgets.baseplot_curve_editor import (AxisColumnDelegate, ColorColumnDelegate, LineColumnDelegate,
                                              SymbolColumnDelegate, RedrawModeColumnDelegate)
from ...widgets.scatterplot_curve_editor import ScatterPlotCurveEditorDialog
from ...widgets.timeplot_curve_editor import TimePlotCurveEditorDialog
from ...widgets.waveformplot_curve_editor import WaveformPlotCurveEditorDialog


def test_waveform_curve_editor(qtbot):
    """
    Ensure that the waveform curve editor looks and functions as expected
    """

    # Create waveform plot curve editor along with its associated plot. Ensure it shows.
    base_plot = BasePlot()
    qtbot.addWidget(base_plot)

    curve_editor = WaveformPlotCurveEditorDialog(base_plot)
    qtbot.addWidget(curve_editor)
    curve_editor.show()

    table_model = curve_editor.table_model
    table_view = curve_editor.table_view

    # Verify that the drop downs for columns with non built-in types are all put in the correct place
    # Note: We do need to check these on each individual type of curve editor (see below tests) and not just
    # in the base plot editor since each plot type can have varying numbers of columns
    color_index = table_model.getColumnIndex('Color')
    line_style_index = table_model.getColumnIndex('Line Style')
    symbol_index = table_model.getColumnIndex('Symbol')
    redraw_mode_index = table_model.getColumnIndex('Redraw Mode')

    assert type(table_view.itemDelegateForColumn(color_index)) is ColorColumnDelegate
    assert type(table_view.itemDelegateForColumn(line_style_index)) is LineColumnDelegate
    assert type(table_view.itemDelegateForColumn(symbol_index)) is SymbolColumnDelegate
    assert type(table_view.itemDelegateForColumn(redraw_mode_index)) is RedrawModeColumnDelegate


def test_timeplot_curve_editor(qtbot):
    """
    Ensure that the time plot curve editor looks and functions as expected
    """

    # Create time plot curve editor along with its associated plot. Ensure it shows.
    base_plot = BasePlot()
    qtbot.addWidget(base_plot)

    curve_editor = TimePlotCurveEditorDialog(base_plot)
    qtbot.addWidget(curve_editor)
    curve_editor.show()

    table_model = curve_editor.table_model
    table_view = curve_editor.table_view

    # Verify that the drop downs for columns with non built-in types are all put in the correct place
    color_index = table_model.getColumnIndex('Color')
    line_style_index = table_model.getColumnIndex('Line Style')
    symbol_index = table_model.getColumnIndex('Symbol')

    assert type(table_view.itemDelegateForColumn(color_index)) is ColorColumnDelegate
    assert type(table_view.itemDelegateForColumn(line_style_index)) is LineColumnDelegate
    assert type(table_view.itemDelegateForColumn(symbol_index)) is SymbolColumnDelegate


def test_scatterplot_editor(qtbot):
    """
    Ensure that the scatter plot curve editor looks and functions as expected
    """

    # Create scatter plot curve editor along with its associated plot. Ensure it shows.
    base_plot = BasePlot()
    qtbot.addWidget(base_plot)

    curve_editor = ScatterPlotCurveEditorDialog(base_plot)
    qtbot.addWidget(curve_editor)
    curve_editor.show()

    table_model = curve_editor.table_model
    table_view = curve_editor.table_view

    # Verify that the drop downs for columns with non built-in types are all put in the correct place
    color_index = table_model.getColumnIndex('Color')
    line_style_index = table_model.getColumnIndex('Line Style')
    symbol_index = table_model.getColumnIndex('Symbol')
    redraw_mode_index = table_model.getColumnIndex('Redraw Mode')

    assert type(table_view.itemDelegateForColumn(color_index)) is ColorColumnDelegate
    assert type(table_view.itemDelegateForColumn(line_style_index)) is LineColumnDelegate
    assert type(table_view.itemDelegateForColumn(symbol_index)) is SymbolColumnDelegate
    assert type(table_view.itemDelegateForColumn(redraw_mode_index)) is RedrawModeColumnDelegate


def test_axis_editor(qtbot):
    """
    Ensure that the axis editor tab in the curve editor looks and functions as expected
    """

    base_plot = BasePlot()
    qtbot.addWidget(base_plot)
    curve_editor = WaveformPlotCurveEditorDialog(base_plot)

    axis_model = curve_editor.axis_model
    axis_view = curve_editor.axis_view

    # Verify the column count is correct, and the axis column delegate is placed correctly
    axis_orientation_index = axis_model._column_names.index('Y-Axis Orientation')
    assert type(axis_view.itemDelegateForColumn(axis_orientation_index)) is AxisColumnDelegate
