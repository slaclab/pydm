import logging
logger = logging.getLogger(__name__)

from .qtplugin_base import qtplugin_factory, WidgetCategory
from .qtplugin_extensions import (RulesExtension, WaveformCurveEditorExtension,
                                  TimeCurveEditorExtension,
                                  ScatterCurveEditorExtension)
from .tab_bar_qtplugin import TabWidgetPlugin
from .byte import PyDMByteIndicator

from .checkbox import PyDMCheckbox
from .drawing import (PyDMDrawingLine, PyDMDrawingRectangle,
                      PyDMDrawingTriangle,
                      PyDMDrawingEllipse, PyDMDrawingCircle, PyDMDrawingArc,
                      PyDMDrawingPie, PyDMDrawingChord, PyDMDrawingImage,
                      PyDMDrawingPolygon)

from .embedded_display import PyDMEmbeddedDisplay
from .enum_button import PyDMEnumButton
from .enum_combo_box import PyDMEnumComboBox
from .frame import PyDMFrame
from .image import PyDMImageView
from .label import PyDMLabel
from .line_edit import PyDMLineEdit
from .logdisplay import PyDMLogDisplay
from .pushbutton import PyDMPushButton
from .related_display_button import PyDMRelatedDisplayButton
from .shell_command import PyDMShellCommand
from .slider import PyDMSlider
from .spinbox import PyDMSpinbox
from .symbol import PyDMSymbol
from .waveformtable import PyDMWaveformTable
from .scale import PyDMScaleIndicator
from .timeplot import PyDMTimePlot
from .waveformplot import PyDMWaveformPlot
from .scatterplot import PyDMScatterPlot


BASE_EXTENSIONS = [RulesExtension]

# Label plugin
PyDMLabelPlugin = qtplugin_factory(PyDMLabel, group=WidgetCategory.DISPLAY,
                                   extensions=BASE_EXTENSIONS)
# Time Plot plugin
PyDMTimePlotPlugin = qtplugin_factory(PyDMTimePlot, group=WidgetCategory.PLOT,
                                      extensions=[TimeCurveEditorExtension,
                                                  RulesExtension])

# Waveform Plot plugin
PyDMWaveformPlotPlugin = qtplugin_factory(PyDMWaveformPlot,
                                          group=WidgetCategory.PLOT,
                                          extensions=[
                                              WaveformCurveEditorExtension,
                                              RulesExtension])

# Scatter Plot plugin
PyDMScatterPlotPlugin = qtplugin_factory(PyDMScatterPlot,
                                         group=WidgetCategory.PLOT,
                                         extensions=[
                                             ScatterCurveEditorExtension,
                                             RulesExtension])

# Byte plugin
PyDMByteIndicatorPlugin = qtplugin_factory(PyDMByteIndicator,
                                           group=WidgetCategory.DISPLAY,
                                           extensions=BASE_EXTENSIONS)

# Checkbox plugin
PyDMCheckboxPlugin = qtplugin_factory(PyDMCheckbox, group=WidgetCategory.INPUT,
                                      extensions=BASE_EXTENSIONS)

# Drawing plugins
PyDMDrawingArcPlugin = qtplugin_factory(PyDMDrawingArc,
                                        group=WidgetCategory.DRAWING,
                                        extensions=BASE_EXTENSIONS)
PyDMDrawingChordPlugin = qtplugin_factory(PyDMDrawingChord,
                                          group=WidgetCategory.DRAWING,
                                          extensions=BASE_EXTENSIONS)
PyDMDrawingCirclePlugin = qtplugin_factory(PyDMDrawingCircle,
                                           group=WidgetCategory.DRAWING,
                                           extensions=BASE_EXTENSIONS)
PyDMDrawingEllipsePlugin = qtplugin_factory(PyDMDrawingEllipse,
                                            group=WidgetCategory.DRAWING,
                                            extensions=BASE_EXTENSIONS)
PyDMDrawingImagePlugin = qtplugin_factory(PyDMDrawingImage,
                                          group=WidgetCategory.DRAWING,
                                          extensions=BASE_EXTENSIONS)
PyDMDrawingLinePlugin = qtplugin_factory(PyDMDrawingLine,
                                         group=WidgetCategory.DRAWING,
                                         extensions=BASE_EXTENSIONS)
PyDMDrawingPiePlugin = qtplugin_factory(PyDMDrawingPie,
                                        group=WidgetCategory.DRAWING,
                                        extensions=BASE_EXTENSIONS)
PyDMDrawingRectanglePlugin = qtplugin_factory(PyDMDrawingRectangle,
                                              group=WidgetCategory.DRAWING,
                                              extensions=BASE_EXTENSIONS)
PyDMDrawingTrianglePlugin = qtplugin_factory(PyDMDrawingTriangle,
                                             group=WidgetCategory.DRAWING,
                                             extensions=BASE_EXTENSIONS)

PyDMDrawingPolygonPlugin = qtplugin_factory(PyDMDrawingPolygon,
                                            group=WidgetCategory.DRAWING,
                                            extensions=BASE_EXTENSIONS)

# Embedded Display plugin
PyDMEmbeddedDisplayPlugin = qtplugin_factory(PyDMEmbeddedDisplay,
                                             group=WidgetCategory.CONTAINER,
                                             extensions=BASE_EXTENSIONS)

# Enum Button plugin
PyDMEnumButtonPlugin = qtplugin_factory(PyDMEnumButton,
                                        group=WidgetCategory.INPUT,
                                        extensions=BASE_EXTENSIONS)

# Enum Combobox plugin
PyDMEnumComboBoxPlugin = qtplugin_factory(PyDMEnumComboBox,
                                          group=WidgetCategory.INPUT,
                                          extensions=BASE_EXTENSIONS)

# Frame plugin
PyDMFramePlugin = qtplugin_factory(PyDMFrame, group=WidgetCategory.CONTAINER,
                                   is_container=True,
                                   extensions=BASE_EXTENSIONS)

# Image plugin
PyDMImageViewPlugin = qtplugin_factory(PyDMImageView,
                                       group=WidgetCategory.DISPLAY,
                                       extensions=BASE_EXTENSIONS)

# Line Edit plugin
PyDMLineEditPlugin = qtplugin_factory(PyDMLineEdit, group=WidgetCategory.INPUT,
                                      extensions=BASE_EXTENSIONS)

# Log Viewer
PyDMLogDisplayPlugin = qtplugin_factory(PyDMLogDisplay,
                                        group=WidgetCategory.DISPLAY,
                                        extensions=BASE_EXTENSIONS)

# Push Button plugin
PyDMPushButtonPlugin = qtplugin_factory(PyDMPushButton,
                                        group=WidgetCategory.INPUT,
                                        extensions=BASE_EXTENSIONS)

# Related Display Button plugin
PyDMRelatedDisplayButtonPlugin = qtplugin_factory(PyDMRelatedDisplayButton,
                                                  group=WidgetCategory.DISPLAY,
                                                  extensions=BASE_EXTENSIONS)

# Shell Command plugin
PyDMShellCommandPlugin = qtplugin_factory(PyDMShellCommand,
                                          group=WidgetCategory.INPUT,
                                          extensions=BASE_EXTENSIONS)

# Slider plugin
PyDMSliderPlugin = qtplugin_factory(PyDMSlider, group=WidgetCategory.INPUT,
                                    extensions=BASE_EXTENSIONS)

# Spinbox plugin
PyDMSpinboxplugin = qtplugin_factory(PyDMSpinbox, group=WidgetCategory.INPUT,
                                     extensions=BASE_EXTENSIONS)

# Scale Indicator plugin
PyDMScaleIndicatorPlugin = qtplugin_factory(PyDMScaleIndicator,
                                            group=WidgetCategory.DISPLAY,
                                            extensions=BASE_EXTENSIONS)

# Symbol plugin
PyDMSymbolPlugin = qtplugin_factory(PyDMSymbol, group=WidgetCategory.DISPLAY,
                                    extensions=BASE_EXTENSIONS)

# Waveform Table plugin
PyDMWaveformTablePlugin = qtplugin_factory(PyDMWaveformTable,
                                           group=WidgetCategory.INPUT,
                                           extensions=BASE_EXTENSIONS)

# Tab Widget plugin
PyDMTabWidgetPlugin = TabWidgetPlugin(extensions=BASE_EXTENSIONS)
