from qtpy.QtWidgets import QTableView
from pydm.widgets.baseplot import BasePlot
from pydm.widgets.baseplot_curve_editor import (
    AxisColumnDelegate,
    ColorColumnDelegate,
    LineColumnDelegate,
    SymbolColumnDelegate,
    RedrawModeColumnDelegate,
    PlotStyleColumnDelegate,
)
from pydm.widgets import PyDMArchiverTimePlot
from pydm.widgets.axis_table_model import BasePlotAxesModel
from pydm.widgets.baseplot_table_model import BasePlotCurvesModel
from pydm.widgets.archiver_time_plot_editor import PyDMArchiverTimePlotCurvesModel
from pydm.widgets.scatterplot_curve_editor import ScatterPlotCurveEditorDialog
from pydm.widgets.timeplot_curve_editor import TimePlotCurveEditorDialog
from pydm.widgets.waveformplot import WaveformCurveItem
from pydm.widgets.waveformplot_curve_editor import WaveformPlotCurveEditorDialog


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
    color_index = table_model.getColumnIndex("Color")
    line_style_index = table_model.getColumnIndex("Line Style")
    symbol_index = table_model.getColumnIndex("Symbol")
    redraw_mode_index = table_model.getColumnIndex("Redraw Mode")
    plot_style_index = table_model.getColumnIndex("Style")

    assert type(table_view.itemDelegateForColumn(color_index)) is ColorColumnDelegate
    assert type(table_view.itemDelegateForColumn(line_style_index)) is LineColumnDelegate
    assert type(table_view.itemDelegateForColumn(symbol_index)) is SymbolColumnDelegate
    assert type(table_view.itemDelegateForColumn(redraw_mode_index)) is RedrawModeColumnDelegate
    assert type(table_view.itemDelegateForColumn(plot_style_index)) is PlotStyleColumnDelegate


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
    color_index = table_model.getColumnIndex("Color")
    line_style_index = table_model.getColumnIndex("Line Style")
    symbol_index = table_model.getColumnIndex("Symbol")
    plot_style_index = table_model.getColumnIndex("Style")

    assert type(table_view.itemDelegateForColumn(color_index)) is ColorColumnDelegate
    assert type(table_view.itemDelegateForColumn(line_style_index)) is LineColumnDelegate
    assert type(table_view.itemDelegateForColumn(symbol_index)) is SymbolColumnDelegate
    assert type(table_view.itemDelegateForColumn(plot_style_index)) is PlotStyleColumnDelegate


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
    color_index = table_model.getColumnIndex("Color")
    line_style_index = table_model.getColumnIndex("Line Style")
    symbol_index = table_model.getColumnIndex("Symbol")
    redraw_mode_index = table_model.getColumnIndex("Redraw Mode")

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
    axis_orientation_index = axis_model._column_names.index("Y-Axis Orientation")
    assert type(axis_view.itemDelegateForColumn(axis_orientation_index)) is AxisColumnDelegate


def test_axis_table_model(qtmodeltester):
    """Check the validity of the BasePlotAxesModel with pytest-qt"""
    base_plot = BasePlot()
    axis_model = BasePlotAxesModel(plot=base_plot)
    axis_model.append("FooBar")

    qtmodeltester.check(axis_model, force_py=True)


def test_curves_table_model(qtmodeltester):
    """Check the validity of the BasePlotCurvesModel with pytest-qt"""
    base_plot = BasePlot()
    curves_model = BasePlotCurvesModel(plot=base_plot)
    curves_model.append()

    qtmodeltester.check(curves_model, force_py=True)


def test_archive_table_model(qtmodeltester):
    """Check the validity of the PyDMArchiverTimePlotCurvesModel with pytest-qt"""
    archiver_plot = PyDMArchiverTimePlot()
    archive_model = PyDMArchiverTimePlotCurvesModel(plot=archiver_plot)
    archive_model.append()

    qtmodeltester.check(archive_model, force_py=True)


def test_plot_style_column_delegate(qtbot):
    """Verify the functionality of the show/hide column feature"""

    # Set up a plot with three data items. Two will be plotted as lines, and one as bars.
    base_plot = BasePlot()
    qtbot.addWidget(base_plot)
    line_item_1 = WaveformCurveItem()
    line_item_2 = WaveformCurveItem()
    bar_item = WaveformCurveItem(plot_style="Bar")
    plot_curves_model = BasePlotCurvesModel(plot=base_plot)
    table_view = QTableView()
    table_view.setModel(plot_curves_model)
    plot_style_column_delegate = PlotStyleColumnDelegate(
        parent=base_plot, table_model=plot_curves_model, table_view=table_view
    )

    base_plot.addCurve(line_item_1)
    plot_style_column_delegate.toggleColumnVisibility()

    # With only the line style curve displayed the four line columns should be shown
    for column in plot_style_column_delegate.line_columns_to_toggle:
        assert not table_view.isColumnHidden(plot_curves_model.getColumnIndex(column))
    # And the four bar columns should be hidden
    for column in plot_style_column_delegate.bar_columns_to_toggle:
        assert table_view.isColumnHidden(plot_curves_model.getColumnIndex(column))

    # Now add an additional line curve and a bar curve. All 8 columns should now be visible since it's a mixed plot
    base_plot.addCurve(line_item_2)
    base_plot.addCurve(bar_item)

    plot_style_column_delegate.toggleColumnVisibility()
    for column in plot_style_column_delegate.line_columns_to_toggle:
        assert not table_view.isColumnHidden(plot_curves_model.getColumnIndex(column))
    for column in plot_style_column_delegate.bar_columns_to_toggle:
        assert not table_view.isColumnHidden(plot_curves_model.getColumnIndex(column))

    # Finally remove both line curves to test the last option, nothing but bar style curves. All line options should
    # be hidden, while the bar options should still be shown
    base_plot.removeCurve(line_item_1)
    base_plot.removeCurve(line_item_2)

    plot_style_column_delegate.toggleColumnVisibility()
    for column in plot_style_column_delegate.line_columns_to_toggle:
        assert table_view.isColumnHidden(plot_curves_model.getColumnIndex(column))
    for column in plot_style_column_delegate.bar_columns_to_toggle:
        assert not table_view.isColumnHidden(plot_curves_model.getColumnIndex(column))
