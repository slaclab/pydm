from ..widgets.qtplugin_base import qtplugin_factory


def test_import_byte_plugin():
    # Byte plugin
    from ..widgets.byte import PyDMByteIndicator

    qtplugin_factory(PyDMByteIndicator)


def test_import_checkbox_plugin():
    # Checkbox plugin
    from ..widgets.checkbox import PyDMCheckbox

    qtplugin_factory(PyDMCheckbox)


def test_import_drawing_plugins():
    # Drawing plugins
    from ..widgets.drawing import (
        PyDMDrawingLine,
        PyDMDrawingRectangle,
        PyDMDrawingTriangle,
        PyDMDrawingEllipse,
        PyDMDrawingCircle,
        PyDMDrawingArc,
        PyDMDrawingPie,
        PyDMDrawingChord,
        PyDMDrawingImage,
        PyDMDrawingPolygon,
        PyDMDrawingPolyline,
        PyDMDrawingIrregularPolygon,
    )

    qtplugin_factory(PyDMDrawingImage)
    qtplugin_factory(PyDMDrawingLine)
    qtplugin_factory(PyDMDrawingRectangle)
    qtplugin_factory(PyDMDrawingTriangle)
    qtplugin_factory(PyDMDrawingEllipse)
    qtplugin_factory(PyDMDrawingCircle)
    qtplugin_factory(PyDMDrawingArc)
    qtplugin_factory(PyDMDrawingPie)
    qtplugin_factory(PyDMDrawingChord)
    qtplugin_factory(PyDMDrawingPolygon)
    qtplugin_factory(PyDMDrawingPolyline)
    qtplugin_factory(PyDMDrawingIrregularPolygon)


def test_import_embedded_display_plugin():
    # Embedded Display plugin
    from ..widgets.embedded_display import PyDMEmbeddedDisplay

    qtplugin_factory(PyDMEmbeddedDisplay)


def test_import_frame_plugin():
    # Frame plugin
    from ..widgets.frame import PyDMFrame

    qtplugin_factory(PyDMFrame, is_container=True)


def test_import_window_plugin():
    # Window plugin
    from ..widgets.window import PyDMWindow

    qtplugin_factory(PyDMWindow, is_container=True)


def test_import_enum_button_plugin():
    # Enum Button plugin
    from ..widgets.enum_button import PyDMEnumButton

    qtplugin_factory(PyDMEnumButton)


def test_import_combobox_plugin():
    # Enum Combobox plugin
    from ..widgets.enum_combo_box import PyDMEnumComboBox

    qtplugin_factory(PyDMEnumComboBox)


def test_import_image_plugin():
    # Image plugin
    from ..widgets.image import PyDMImageView

    qtplugin_factory(PyDMImageView)


def test_import_label_plugin():
    # Label plugin
    from ..widgets.label import PyDMLabel

    qtplugin_factory(PyDMLabel)


def test_import_line_edit_plugin():
    # Line Edit plugin
    from ..widgets.line_edit import PyDMLineEdit

    qtplugin_factory(PyDMLineEdit)


def test_import_pushbutton_plugin():
    # Push Button plugin
    from ..widgets.pushbutton import PyDMPushButton

    qtplugin_factory(PyDMPushButton)


def test_import_related_display_plugin():
    # Related Display Button plugin
    from ..widgets.related_display_button import PyDMRelatedDisplayButton

    qtplugin_factory(PyDMRelatedDisplayButton)


def test_import_scale_indicator_plugin():
    # Scale Indicator plugin
    from ..widgets.scale import PyDMScaleIndicator

    qtplugin_factory(PyDMScaleIndicator)


def test_import_shellcmd_plugin():
    # Shell Command plugin
    from ..widgets.shell_command import PyDMShellCommand

    qtplugin_factory(PyDMShellCommand)


def test_import_slider_plugin():
    # Slider plugin
    from ..widgets.slider import PyDMSlider

    qtplugin_factory(PyDMSlider)


def test_import_spinbox_plugin():
    # Spinbox plugin
    from ..widgets.spinbox import PyDMSpinbox

    qtplugin_factory(PyDMSpinbox)


def test_import_symbol_plugin():
    # Symbol plugin
    from ..widgets.symbol import PyDMSymbol

    qtplugin_factory(PyDMSymbol)


def test_import_waveform_table_plugin():
    # Waveform Table plugin
    from ..widgets.waveformtable import PyDMWaveformTable

    qtplugin_factory(PyDMWaveformTable)


def test_import_timeplot_plugin():
    # Time Plot plugin
    from ..widgets.timeplot import PyDMTimePlot
    from ..widgets.timeplot_curve_editor import TimePlotCurveEditorDialog

    # Time Plot plugin
    qtplugin_factory(PyDMTimePlot, TimePlotCurveEditorDialog)


def test_import_waveformplot_plugin():
    # Time Plot plugin
    from ..widgets.waveformplot import PyDMWaveformPlot
    from ..widgets.waveformplot_curve_editor import WaveformPlotCurveEditorDialog

    # Waveform Plot plugin
    qtplugin_factory(PyDMWaveformPlot, WaveformPlotCurveEditorDialog)


def test_import_scatterplot_plugin():
    from ..widgets.scatterplot import PyDMScatterPlot
    from ..widgets.scatterplot_curve_editor import ScatterPlotCurveEditorDialog

    # Scatter Plot plugin
    qtplugin_factory(PyDMScatterPlot, ScatterPlotCurveEditorDialog)


def test_import_tab_widget_plugin():
    # Symbol plugin
    from ..widgets.tab_bar_qtplugin import TabWidgetPlugin

    TabWidgetPlugin()
