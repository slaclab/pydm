from ..widgets.qtplugin_base import qtplugin_factory

def test_import_byte_plugin():
    # Byte plugin
    from ..widgets.byte import PyDMByteIndicator
    PyDMByteIndicatorPlugin = qtplugin_factory(PyDMByteIndicator)

def test_import_checkbox_plugin():
    # Checkbox plugin
    from ..widgets.checkbox import PyDMCheckbox
    PyDMCheckboxPlugin = qtplugin_factory(PyDMCheckbox)

def test_import_drawing_plugins():
    # Drawing plugins
    from ..widgets.drawing import (PyDMDrawingLine, PyDMDrawingRectangle, PyDMDrawingTriangle,
                                  PyDMDrawingEllipse, PyDMDrawingCircle, PyDMDrawingArc,
                                  PyDMDrawingPie, PyDMDrawingChord, PyDMDrawingImage)

    PyDMDrawingImagePlugin = qtplugin_factory(PyDMDrawingImage)
    PyDMDrawingLinePlugin = qtplugin_factory(PyDMDrawingLine)
    PyDMDrawingRectanglePlugin = qtplugin_factory(PyDMDrawingRectangle)
    PyDMDrawingTrianglePlugin = qtplugin_factory(PyDMDrawingTriangle)
    PyDMDrawingEllipsePlugin = qtplugin_factory(PyDMDrawingEllipse)
    PyDMDrawingCirclePlugin = qtplugin_factory(PyDMDrawingCircle)
    PyDMDrawingArcPlugin = qtplugin_factory(PyDMDrawingArc)
    PyDMDrawingPiePlugin = qtplugin_factory(PyDMDrawingPie)
    PyDMDrawingChordPlugin = qtplugin_factory(PyDMDrawingChord)

def test_import_embedded_display_plugin():
    # Embedded Display plugin
    from ..widgets.embedded_display import PyDMEmbeddedDisplay
    PyDMEmbeddedDisplayPlugin = qtplugin_factory(PyDMEmbeddedDisplay)

def test_import_combobox_plugin():
    # Enum Combobox plugin
    from ..widgets.enum_combo_box import PyDMEnumComboBox
    PyDMEnumComboBoxPlugin = qtplugin_factory(PyDMEnumComboBox)

def test_image_plugin():
    # Image plugin
    from ..widgets.image import PyDMImageView
    PyDMImageViewPlugin = qtplugin_factory(PyDMImageView)

def test_indicator_plugin():
    # Indicator plugin
    from ..widgets.indicator import PyDMIndicator
    PyDMIndicatorPlugin = qtplugin_factory(PyDMIndicator)

def test_label_plugin():
    # Label plugin
    from ..widgets.label import PyDMLabel
    PyDMLabelPlugin = qtplugin_factory(PyDMLabel)

def test_line_edit_plugin():
    # Line Edit plugin
    from ..widgets.line_edit import PyDMLineEdit
    PyDMLineEditPlugin = qtplugin_factory(PyDMLineEdit)

def test_pushbutton_plugin():
    # Push Button plugin
    from ..widgets.pushbutton import PyDMPushButton
    PyDMPushButtonPlugin = qtplugin_factory(PyDMPushButton)

def test_related_display_plugin():
    # Related Display Button plugin
    from ..widgets.related_display_button import PyDMRelatedDisplayButton
    PyDMRelatedDisplayButtonPlugin = qtplugin_factory(PyDMRelatedDisplayButton)

def test_shellcmd_plugin():
    # Shell Command plugin
    from ..widgets.shell_command import PyDMShellCommand
    PyDMShellCommandPlugin = qtplugin_factory(PyDMShellCommand)

def test_slider_plugin():
    # Slider plugin
    from ..widgets.slider import PyDMSlider
    PyDMSliderPlugin = qtplugin_factory(PyDMSlider)

def test_spinbox_plugin():
    # Spinbox plugin
    from ..widgets.spinbox import PyDMSpinbox
    PyDMSpinboxplugin = qtplugin_factory(PyDMSpinbox)

def test_symbol_plugin():
    # Symbol plugin
    from ..widgets.symbol import PyDMSymbol
    PyDMSymbolPlugin = qtplugin_factory(PyDMSymbol)

def test_waveform_table_plugin():
    # Waveform Table plugin
    from ..widgets.waveformtable import PyDMWaveformTable
    PyDMWaveformTablePlugin = qtplugin_factory(PyDMWaveformTable)

def test_timeplot_plugin():
    # Time Plot plugin
    from ..widgets.timeplot_qtplugin import PyDMTimePlotPlugin

def test_waveformplot_plugin():
    # Waveform Plot plugin
    from ..widgets.waveformplot_qtplugin import PyDMWaveformPlotPlugin
