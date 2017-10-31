from .qtplugin_base import qtplugin_factory, WidgetCategory
from .baseplot_qtplugin import qtplugin_plot_factory

from .byte import PyDMByteIndicator

from .checkbox import PyDMCheckbox
from .drawing import (PyDMDrawingLine, PyDMDrawingRectangle, PyDMDrawingTriangle,
                      PyDMDrawingEllipse, PyDMDrawingCircle, PyDMDrawingArc,
                      PyDMDrawingPie, PyDMDrawingChord, PyDMDrawingImage)

from .embedded_display import PyDMEmbeddedDisplay
from .enum_combo_box import PyDMEnumComboBox
from .image import PyDMImageView
from .indicator import PyDMIndicator
from .label import PyDMLabel
from .line_edit import PyDMLineEdit
from .pushbutton import PyDMPushButton
from .related_display_button import PyDMRelatedDisplayButton
from .shell_command import PyDMShellCommand
from .slider import PyDMSlider
from .spinbox import PyDMSpinbox
from .symbol import PyDMSymbol
from .waveformtable import PyDMWaveformTable
from .scale import PyDMScaleIndicator
from .timeplot import PyDMTimePlot
from .timeplot_curve_editor import TimePlotCurveEditorDialog
from .waveformplot import PyDMWaveformPlot
from .waveformplot_curve_editor import WaveformPlotCurveEditorDialog
from .scatterplot import PyDMScatterPlot
from .scatterplot_curve_editor import ScatterPlotCurveEditorDialog

# Time Plot plugin
PyDMTimePlotPlugin = qtplugin_plot_factory(
                            PyDMTimePlot, TimePlotCurveEditorDialog)

# Waveform Plot plugin
PyDMWaveformPlotPlugin = qtplugin_plot_factory(
                            PyDMWaveformPlot, WaveformPlotCurveEditorDialog)

# Scatter Plot plugin
PyDMScatterPlotPlugin = qtplugin_plot_factory(
                            PyDMScatterPlot, ScatterPlotCurveEditorDialog)

# Byte plugin
PyDMByteIndicatorPlugin = qtplugin_factory(PyDMByteIndicator, group=WidgetCategory.DISPLAY)

# Checkbox plugin
PyDMCheckboxPlugin = qtplugin_factory(PyDMCheckbox, group=WidgetCategory.INPUT)

# Drawing plugins
PyDMDrawingArcPlugin = qtplugin_factory(PyDMDrawingArc, group=WidgetCategory.DRAWING)
PyDMDrawingChordPlugin = qtplugin_factory(PyDMDrawingChord, group=WidgetCategory.DRAWING)
PyDMDrawingCirclePlugin = qtplugin_factory(PyDMDrawingCircle, group=WidgetCategory.DRAWING)
PyDMDrawingEllipsePlugin = qtplugin_factory(PyDMDrawingEllipse, group=WidgetCategory.DRAWING)
PyDMDrawingImagePlugin = qtplugin_factory(PyDMDrawingImage, group=WidgetCategory.DRAWING)
PyDMDrawingLinePlugin = qtplugin_factory(PyDMDrawingLine, group=WidgetCategory.DRAWING)
PyDMDrawingPiePlugin = qtplugin_factory(PyDMDrawingPie, group=WidgetCategory.DRAWING)
PyDMDrawingRectanglePlugin = qtplugin_factory(PyDMDrawingRectangle, group=WidgetCategory.DRAWING)
PyDMDrawingTrianglePlugin = qtplugin_factory(PyDMDrawingTriangle, group=WidgetCategory.DRAWING)

# Embedded Display plugin
PyDMEmbeddedDisplayPlugin = qtplugin_factory(PyDMEmbeddedDisplay, group=WidgetCategory.DISPLAY)

# Enum Combobox plugin
PyDMEnumComboBoxPlugin = qtplugin_factory(PyDMEnumComboBox, group=WidgetCategory.INPUT)


# Image plugin
PyDMImageViewPlugin = qtplugin_factory(PyDMImageView, group=WidgetCategory.DISPLAY)

# Indicator plugin
PyDMIndicatorPlugin = qtplugin_factory(PyDMIndicator, group=WidgetCategory.DISPLAY)

# Label plugin
PyDMLabelPlugin = qtplugin_factory(PyDMLabel, group=WidgetCategory.DISPLAY)

# Line Edit plugin
PyDMLineEditPlugin = qtplugin_factory(PyDMLineEdit, group=WidgetCategory.INPUT)

# Push Button plugin
PyDMPushButtonPlugin = qtplugin_factory(PyDMPushButton, group=WidgetCategory.INPUT)


# Related Display Button plugin
PyDMRelatedDisplayButtonPlugin = qtplugin_factory(PyDMRelatedDisplayButton, group=WidgetCategory.DISPLAY)

# Shell Command plugin
PyDMShellCommandPlugin = qtplugin_factory(PyDMShellCommand, group=WidgetCategory.INPUT)

# Slider plugin
PyDMSliderPlugin = qtplugin_factory(PyDMSlider, group=WidgetCategory.INPUT)


# Spinbox plugin
PyDMSpinboxplugin = qtplugin_factory(PyDMSpinbox, group=WidgetCategory.INPUT)

# Scale Indicator plugin
PyDMScaleIndicatorPlugin = qtplugin_factory(PyDMScaleIndicator, group=WidgetCategory.DISPLAY)

# Symbol plugin
PyDMSymbolPlugin = qtplugin_factory(PyDMSymbol, group=WidgetCategory.DISPLAY)

# Waveform Table plugin
PyDMWaveformTablePlugin = qtplugin_factory(PyDMWaveformTable, group=WidgetCategory.DISPLAY)
