import logging

from .qtplugin_base import qtplugin_factory, WidgetCategory
from .qtplugin_extensions import (RulesExtension, WaveformCurveEditorExtension,
                                  TimeCurveEditorExtension,
                                  ScatterCurveEditorExtension, SymbolExtension)
from .tab_bar_qtplugin import TabWidgetPlugin
from .byte import PyDMByteIndicator

from .checkbox import PyDMCheckbox
from .datetime import (PyDMDateTimeEdit, PyDMDateTimeLabel)
from .drawing import (PyDMDrawingLine, PyDMDrawingRectangle,
                      PyDMDrawingTriangle,
                      PyDMDrawingEllipse, PyDMDrawingCircle, PyDMDrawingArc,
                      PyDMDrawingPie, PyDMDrawingChord, PyDMDrawingImage,
                      PyDMDrawingPolygon, PyDMDrawingPolyline)

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
from .template_repeater import PyDMTemplateRepeater
from .terminator import PyDMTerminator

from ..utilities.iconfont import IconFont

logger = logging.getLogger(__name__)

ifont = IconFont()

BASE_EXTENSIONS = [RulesExtension]

# Label plugin
PyDMLabelPlugin = qtplugin_factory(PyDMLabel, group=WidgetCategory.DISPLAY,
                                   extensions=BASE_EXTENSIONS,
                                   icon=ifont.icon("tag"))

# Time Plot plugin
PyDMTimePlotPlugin = qtplugin_factory(PyDMTimePlot, group=WidgetCategory.PLOT,
                                      extensions=[TimeCurveEditorExtension,
                                                  RulesExtension],
                                      icon=ifont.icon("chart-line"))

# Waveform Plot plugin
PyDMWaveformPlotPlugin = qtplugin_factory(PyDMWaveformPlot,
                                          group=WidgetCategory.PLOT,
                                          extensions=[
                                              WaveformCurveEditorExtension,
                                              RulesExtension],
                                          icon=ifont.icon("wave-square"))

# Scatter Plot plugin
PyDMScatterPlotPlugin = qtplugin_factory(PyDMScatterPlot,
                                         group=WidgetCategory.PLOT,
                                         extensions=[
                                             ScatterCurveEditorExtension,
                                             RulesExtension],
                                         icon=ifont.icon("project-diagram"))

# Byte plugin
PyDMByteIndicatorPlugin = qtplugin_factory(PyDMByteIndicator,
                                           group=WidgetCategory.DISPLAY,
                                           extensions=BASE_EXTENSIONS,
                                           icon=ifont.icon("ellipsis-v"))

# Checkbox plugin
PyDMCheckboxPlugin = qtplugin_factory(PyDMCheckbox, group=WidgetCategory.INPUT,
                                      extensions=BASE_EXTENSIONS,
                                      icon=ifont.icon("check-square"))

# Date/Time plugins
PyDMDateTimeEditPlugin = qtplugin_factory(PyDMDateTimeEdit,
                                          group=WidgetCategory.INPUT,
                                          extensions=BASE_EXTENSIONS,
                                          icon=ifont.icon("calendar-minus"))

PyDMDateTimeLabelPlugin = qtplugin_factory(PyDMDateTimeLabel,
                                           group=WidgetCategory.DISPLAY,
                                           extensions=BASE_EXTENSIONS,
                                           icon=ifont.icon("calendar-alt"))
# Drawing plugins
PyDMDrawingArcPlugin = qtplugin_factory(PyDMDrawingArc,
                                        group=WidgetCategory.DRAWING,
                                        extensions=BASE_EXTENSIONS,
                                        icon=ifont.icon("circle-notch"))
PyDMDrawingChordPlugin = qtplugin_factory(PyDMDrawingChord,
                                          group=WidgetCategory.DRAWING,
                                          extensions=BASE_EXTENSIONS,
                                          icon=ifont.icon("moon"))
PyDMDrawingCirclePlugin = qtplugin_factory(PyDMDrawingCircle,
                                           group=WidgetCategory.DRAWING,
                                           extensions=BASE_EXTENSIONS,
                                           icon=ifont.icon("circle"))
PyDMDrawingEllipsePlugin = qtplugin_factory(PyDMDrawingEllipse,
                                            group=WidgetCategory.DRAWING,
                                            extensions=BASE_EXTENSIONS,
                                            icon=ifont.icon("ellipsis-h"))
PyDMDrawingImagePlugin = qtplugin_factory(PyDMDrawingImage,
                                          group=WidgetCategory.DRAWING,
                                          extensions=BASE_EXTENSIONS,
                                          icon=ifont.icon("image"))
PyDMDrawingLinePlugin = qtplugin_factory(PyDMDrawingLine,
                                         group=WidgetCategory.DRAWING,
                                         extensions=BASE_EXTENSIONS,
                                         icon=ifont.icon("minus"))
PyDMDrawingPiePlugin = qtplugin_factory(PyDMDrawingPie,
                                        group=WidgetCategory.DRAWING,
                                        extensions=BASE_EXTENSIONS,
                                        icon=ifont.icon("pizza-slice"))

PyDMDrawingRectanglePlugin = qtplugin_factory(PyDMDrawingRectangle,
                                              group=WidgetCategory.DRAWING,
                                              extensions=BASE_EXTENSIONS,
                                              icon=ifont.icon("border-style"))
PyDMDrawingTrianglePlugin = qtplugin_factory(PyDMDrawingTriangle,
                                             group=WidgetCategory.DRAWING,
                                             extensions=BASE_EXTENSIONS,
                                             icon=ifont.icon("caret-up"))

PyDMDrawingPolygonPlugin = qtplugin_factory(PyDMDrawingPolygon,
                                            group=WidgetCategory.DRAWING,
                                            extensions=BASE_EXTENSIONS,
                                            icon=ifont.icon("draw-polygon"))

PyDMDrawingPolylinePlugin = qtplugin_factory(PyDMDrawingPolyline,
                                            group=WidgetCategory.DRAWING,
                                            extensions=BASE_EXTENSIONS,
                                            icon=ifont.icon("share-alt"))

# Embedded Display plugin
PyDMEmbeddedDisplayPlugin = qtplugin_factory(PyDMEmbeddedDisplay,
                                             group=WidgetCategory.CONTAINER,
                                             extensions=BASE_EXTENSIONS,
                                             icon=ifont.icon("layer-group"))

# Enum Button plugin
PyDMEnumButtonPlugin = qtplugin_factory(PyDMEnumButton,
                                        group=WidgetCategory.INPUT,
                                        extensions=BASE_EXTENSIONS,
                                        icon=ifont.icon("bars"))

# Enum Combobox plugin
PyDMEnumComboBoxPlugin = qtplugin_factory(PyDMEnumComboBox,
                                          group=WidgetCategory.INPUT,
                                          extensions=BASE_EXTENSIONS,
                                          icon=ifont.icon("list-ol"))

# Frame plugin
PyDMFramePlugin = qtplugin_factory(PyDMFrame, group=WidgetCategory.CONTAINER,
                                   is_container=True,
                                   extensions=BASE_EXTENSIONS,
                                   icon=ifont.icon("expand"))

# Image plugin
PyDMImageViewPlugin = qtplugin_factory(PyDMImageView,
                                       group=WidgetCategory.DISPLAY,
                                       extensions=BASE_EXTENSIONS,
                                       icon=ifont.icon("camera"))

# Line Edit plugin
PyDMLineEditPlugin = qtplugin_factory(PyDMLineEdit, group=WidgetCategory.INPUT,
                                      extensions=BASE_EXTENSIONS,
                                      icon=ifont.icon("edit"))

# Log Viewer
PyDMLogDisplayPlugin = qtplugin_factory(PyDMLogDisplay,
                                        group=WidgetCategory.DISPLAY,
                                        extensions=BASE_EXTENSIONS,
                                        icon=ifont.icon("clipboard"))

# Push Button plugin
PyDMPushButtonPlugin = qtplugin_factory(PyDMPushButton,
                                        group=WidgetCategory.INPUT,
                                        extensions=BASE_EXTENSIONS,
                                        icon=ifont.icon("mouse"))

# Related Display Button plugin
PyDMRelatedDisplayButtonPlugin = qtplugin_factory(PyDMRelatedDisplayButton,
                                                  group=WidgetCategory.DISPLAY,
                                                  extensions=BASE_EXTENSIONS,
                                                  icon=ifont.icon(
                                                      "window-maximize"))

# Shell Command plugin
PyDMShellCommandPlugin = qtplugin_factory(PyDMShellCommand,
                                          group=WidgetCategory.INPUT,
                                          extensions=BASE_EXTENSIONS,
                                          icon=ifont.icon("terminal"))

# Slider plugin
PyDMSliderPlugin = qtplugin_factory(PyDMSlider, group=WidgetCategory.INPUT,
                                    extensions=BASE_EXTENSIONS,
                                    icon=ifont.icon("sliders-h"))

# Spinbox plugin
PyDMSpinboxplugin = qtplugin_factory(PyDMSpinbox, group=WidgetCategory.INPUT,
                                     extensions=BASE_EXTENSIONS,
                                     icon=ifont.icon("sort-numeric-up"))

# Scale Indicator plugin
PyDMScaleIndicatorPlugin = qtplugin_factory(PyDMScaleIndicator,
                                            group=WidgetCategory.DISPLAY,
                                            extensions=BASE_EXTENSIONS,
                                            icon=ifont.icon("level-up-alt")
                                            )

# Symbol plugin
PyDMSymbolPlugin = qtplugin_factory(PyDMSymbol, group=WidgetCategory.DISPLAY,
                                    extensions=[SymbolExtension,
                                                RulesExtension],
                                    icon=ifont.icon("icons"))

# Waveform Table plugin
PyDMWaveformTablePlugin = qtplugin_factory(PyDMWaveformTable,
                                           group=WidgetCategory.INPUT,
                                           extensions=BASE_EXTENSIONS,
                                           icon=ifont.icon("table"))

# Tab Widget plugin
PyDMTabWidgetPlugin = TabWidgetPlugin(extensions=BASE_EXTENSIONS)

# Template Repeater plugin
PyDMTemplateRepeaterPlugin = qtplugin_factory(PyDMTemplateRepeater,
                                              group=WidgetCategory.CONTAINER,
                                              extensions=BASE_EXTENSIONS,
                                              icon=ifont.icon("align-justify"))

# Terminator Widget plugin
PyDMTerminatorPlugin = qtplugin_factory(PyDMTerminator,
                                        group=WidgetCategory.MISC,
                                        extensions=BASE_EXTENSIONS)
