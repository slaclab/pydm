import logging
import os

from pydm.utilities.iconfont import IconFont
from .archiver_time_plot import PyDMArchiverTimePlot
from .byte import PyDMByteIndicator
from .byte import PyDMMultiStateIndicator
from .checkbox import PyDMCheckbox
from .datetime import PyDMDateTimeEdit, PyDMDateTimeLabel
from .drawing import (
    PyDMDrawingArc,
    PyDMDrawingChord,
    PyDMDrawingCircle,
    PyDMDrawingEllipse,
    PyDMDrawingImage,
    PyDMDrawingIrregularPolygon,
    PyDMDrawingLine,
    PyDMDrawingPie,
    PyDMDrawingPolygon,
    PyDMDrawingPolyline,
    PyDMDrawingRectangle,
    PyDMDrawingTriangle,
)
from .embedded_display import PyDMEmbeddedDisplay
from .enum_button import PyDMEnumButton
from .enum_combo_box import PyDMEnumComboBox
from .frame import PyDMFrame
from .image import PyDMImageView
from .label import PyDMLabel
from .line_edit import PyDMLineEdit
from .logdisplay import PyDMLogDisplay
from .pushbutton import PyDMPushButton
from .qtplugin_base import WidgetCategory, get_widgets_from_entrypoints, qtplugin_factory
from .qtplugin_extensions import (
    ArchiveTimeCurveEditorExtension,
    BasicSettingsExtension,
    RulesExtension,
    ScatterCurveEditorExtension,
    EventCurveEditorExtension,
    SymbolExtension,
    TimeCurveEditorExtension,
    WaveformCurveEditorExtension,
)
from .related_display_button import PyDMRelatedDisplayButton
from .scale import PyDMScaleIndicator
from .scatterplot import PyDMScatterPlot
from .shell_command import PyDMShellCommand
from .slider import PyDMSlider
from .spinbox import PyDMSpinbox
from .symbol import PyDMSymbol
from .waveformtable import PyDMWaveformTable
from .analog_indicator import PyDMAnalogIndicator
from .timeplot import PyDMTimePlot
from .waveformplot import PyDMWaveformPlot
from .eventplot import PyDMEventPlot
from .tab_bar_qtplugin import TabWidgetPlugin
from .template_repeater import PyDMTemplateRepeater
from .terminator import PyDMTerminator
from .nt_table import PyDMNTTable

logger = logging.getLogger(__name__)

ifont = IconFont()

BASE_EXTENSIONS = [BasicSettingsExtension, RulesExtension]


# Label plugin
PyDMLabelPlugin = qtplugin_factory(
    PyDMLabel, group=WidgetCategory.DISPLAY, extensions=BASE_EXTENSIONS, icon=ifont.icon("tag")
)

# Time Plot plugin
PyDMTimePlotPlugin = qtplugin_factory(
    PyDMTimePlot,
    group=WidgetCategory.PLOT,
    extensions=[TimeCurveEditorExtension, RulesExtension],
    icon=ifont.icon("chart-line"),
)

# In order to keep the archiver functionality invisible to users who do not have access to an instance of the
# archiver appliance, only load this if the user has the associated environment variable set
if "PYDM_ARCHIVER_URL" in os.environ:
    # Time Plot with archiver appliance support plugin
    PyDMArchiverTimePlotPlugin = qtplugin_factory(
        PyDMArchiverTimePlot,
        group=WidgetCategory.PLOT,
        extensions=[ArchiveTimeCurveEditorExtension, RulesExtension],
        icon=ifont.icon("chart-line"),
    )

# Waveform Plot plugin
PyDMWaveformPlotPlugin = qtplugin_factory(
    PyDMWaveformPlot,
    group=WidgetCategory.PLOT,
    extensions=[WaveformCurveEditorExtension, RulesExtension],
    icon=ifont.icon("wave-square"),
)

# Scatter Plot plugin
PyDMScatterPlotPlugin = qtplugin_factory(
    PyDMScatterPlot,
    group=WidgetCategory.PLOT,
    extensions=[ScatterCurveEditorExtension, RulesExtension],
    icon=ifont.icon("project-diagram"),
)

# Event Plot plugin
PyDMEventPlotPlugin = qtplugin_factory(
    PyDMEventPlot,
    group=WidgetCategory.PLOT,
    extensions=[EventCurveEditorExtension, RulesExtension],
    icon=ifont.icon("project-diagram"),
)

# Byte plugin
PyDMByteIndicatorPlugin = qtplugin_factory(
    PyDMByteIndicator, group=WidgetCategory.DISPLAY, extensions=BASE_EXTENSIONS, icon=ifont.icon("ellipsis-v")
)

# Multi-state plugin
PyDMMultiStateLEDIndicatorPlugin = qtplugin_factory(
    PyDMMultiStateIndicator, group=WidgetCategory.DISPLAY, extensions=BASE_EXTENSIONS, icon=ifont.icon("ellipsis-v")
)

# Checkbox plugin
PyDMCheckboxPlugin = qtplugin_factory(
    PyDMCheckbox, group=WidgetCategory.INPUT, extensions=BASE_EXTENSIONS, icon=ifont.icon("check-square")
)

# Date/Time plugins
PyDMDateTimeEditPlugin = qtplugin_factory(
    PyDMDateTimeEdit, group=WidgetCategory.INPUT, extensions=BASE_EXTENSIONS, icon=ifont.icon("calendar-minus")
)

PyDMDateTimeLabelPlugin = qtplugin_factory(
    PyDMDateTimeLabel, group=WidgetCategory.DISPLAY, extensions=BASE_EXTENSIONS, icon=ifont.icon("calendar-alt")
)
# Drawing plugins
PyDMDrawingArcPlugin = qtplugin_factory(
    PyDMDrawingArc, group=WidgetCategory.DRAWING, extensions=BASE_EXTENSIONS, icon=ifont.icon("circle-notch")
)
PyDMDrawingChordPlugin = qtplugin_factory(
    PyDMDrawingChord, group=WidgetCategory.DRAWING, extensions=BASE_EXTENSIONS, icon=ifont.icon("moon")
)
PyDMDrawingCirclePlugin = qtplugin_factory(
    PyDMDrawingCircle, group=WidgetCategory.DRAWING, extensions=BASE_EXTENSIONS, icon=ifont.icon("circle")
)
PyDMDrawingEllipsePlugin = qtplugin_factory(
    PyDMDrawingEllipse, group=WidgetCategory.DRAWING, extensions=BASE_EXTENSIONS, icon=ifont.icon("ellipsis-h")
)
PyDMDrawingImagePlugin = qtplugin_factory(
    PyDMDrawingImage, group=WidgetCategory.DRAWING, extensions=BASE_EXTENSIONS, icon=ifont.icon("image")
)
PyDMDrawingLinePlugin = qtplugin_factory(
    PyDMDrawingLine, group=WidgetCategory.DRAWING, extensions=BASE_EXTENSIONS, icon=ifont.icon("minus")
)
PyDMDrawingPiePlugin = qtplugin_factory(
    PyDMDrawingPie, group=WidgetCategory.DRAWING, extensions=BASE_EXTENSIONS, icon=ifont.icon("pizza-slice")
)

PyDMDrawingRectanglePlugin = qtplugin_factory(
    PyDMDrawingRectangle, group=WidgetCategory.DRAWING, extensions=BASE_EXTENSIONS, icon=ifont.icon("border-style")
)
PyDMDrawingTrianglePlugin = qtplugin_factory(
    PyDMDrawingTriangle, group=WidgetCategory.DRAWING, extensions=BASE_EXTENSIONS, icon=ifont.icon("caret-up")
)

PyDMDrawingPolygonPlugin = qtplugin_factory(
    PyDMDrawingPolygon, group=WidgetCategory.DRAWING, extensions=BASE_EXTENSIONS, icon=ifont.icon("draw-polygon")
)

PyDMDrawingPolylinePlugin = qtplugin_factory(
    PyDMDrawingPolyline, group=WidgetCategory.DRAWING, extensions=BASE_EXTENSIONS, icon=ifont.icon("share-alt")
)

PyDMDrawingIrregularPolygonPlugin = qtplugin_factory(
    PyDMDrawingIrregularPolygon,
    group=WidgetCategory.DRAWING,
    extensions=BASE_EXTENSIONS,
    icon=ifont.icon("draw-polygon"),
)

# Embedded Display plugin
PyDMEmbeddedDisplayPlugin = qtplugin_factory(
    PyDMEmbeddedDisplay, group=WidgetCategory.CONTAINER, extensions=BASE_EXTENSIONS, icon=ifont.icon("layer-group")
)

# Enum Button plugin
PyDMEnumButtonPlugin = qtplugin_factory(
    PyDMEnumButton, group=WidgetCategory.INPUT, extensions=BASE_EXTENSIONS, icon=ifont.icon("bars")
)

# Enum Combobox plugin
PyDMEnumComboBoxPlugin = qtplugin_factory(
    PyDMEnumComboBox, group=WidgetCategory.INPUT, extensions=BASE_EXTENSIONS, icon=ifont.icon("list-ol")
)

# Frame plugin
PyDMFramePlugin = qtplugin_factory(
    PyDMFrame, group=WidgetCategory.CONTAINER, is_container=True, extensions=BASE_EXTENSIONS, icon=ifont.icon("expand")
)

# Image plugin
PyDMImageViewPlugin = qtplugin_factory(
    PyDMImageView, group=WidgetCategory.DISPLAY, extensions=BASE_EXTENSIONS, icon=ifont.icon("camera")
)

# Line Edit plugin
PyDMLineEditPlugin = qtplugin_factory(
    PyDMLineEdit, group=WidgetCategory.INPUT, extensions=BASE_EXTENSIONS, icon=ifont.icon("edit")
)

# Log Viewer
PyDMLogDisplayPlugin = qtplugin_factory(
    PyDMLogDisplay, group=WidgetCategory.DISPLAY, extensions=BASE_EXTENSIONS, icon=ifont.icon("clipboard")
)

# Push Button plugin
PyDMPushButtonPlugin = qtplugin_factory(
    PyDMPushButton, group=WidgetCategory.INPUT, extensions=BASE_EXTENSIONS, icon=ifont.icon("mouse")
)

# Related Display Button plugin
PyDMRelatedDisplayButtonPlugin = qtplugin_factory(
    PyDMRelatedDisplayButton,
    group=WidgetCategory.DISPLAY,
    extensions=BASE_EXTENSIONS,
    icon=ifont.icon("window-maximize"),
)

# Shell Command plugin
PyDMShellCommandPlugin = qtplugin_factory(
    PyDMShellCommand, group=WidgetCategory.INPUT, extensions=BASE_EXTENSIONS, icon=ifont.icon("terminal")
)

# Slider plugin
PyDMSliderPlugin = qtplugin_factory(
    PyDMSlider, group=WidgetCategory.INPUT, extensions=BASE_EXTENSIONS, icon=ifont.icon("sliders-h")
)

# Spinbox plugin
PyDMSpinboxplugin = qtplugin_factory(
    PyDMSpinbox, group=WidgetCategory.INPUT, extensions=BASE_EXTENSIONS, icon=ifont.icon("sort-numeric-up")
)

# Scale Indicator plugin
PyDMScaleIndicatorPlugin = qtplugin_factory(
    PyDMScaleIndicator, group=WidgetCategory.DISPLAY, extensions=BASE_EXTENSIONS, icon=ifont.icon("level-up-alt")
)

# Analog Indicator plugin
PyDMAnalogIndicatorPlugin = qtplugin_factory(
    PyDMAnalogIndicator, group=WidgetCategory.DISPLAY, extensions=BASE_EXTENSIONS, icon=ifont.icon("level-up-alt")
)

# Symbol plugin
PyDMSymbolPlugin = qtplugin_factory(
    PyDMSymbol, group=WidgetCategory.DISPLAY, extensions=[SymbolExtension, RulesExtension], icon=ifont.icon("icons")
)

# Waveform Table plugin
PyDMWaveformTablePlugin = qtplugin_factory(
    PyDMWaveformTable, group=WidgetCategory.INPUT, extensions=BASE_EXTENSIONS, icon=ifont.icon("table")
)
# NTTable plugin
PyDMNTTable = qtplugin_factory(
    PyDMNTTable, group=WidgetCategory.INPUT, extensions=BASE_EXTENSIONS, icon=ifont.icon("table")
)

# Tab Widget plugin
PyDMTabWidgetPlugin = TabWidgetPlugin(extensions=BASE_EXTENSIONS)

# Template Repeater plugin
PyDMTemplateRepeaterPlugin = qtplugin_factory(
    PyDMTemplateRepeater, group=WidgetCategory.CONTAINER, extensions=BASE_EXTENSIONS, icon=ifont.icon("align-justify")
)

# Terminator Widget plugin
PyDMTerminatorPlugin = qtplugin_factory(PyDMTerminator, group=WidgetCategory.MISC, extensions=BASE_EXTENSIONS)

# **********************************************
# NOTE: Add in new PyDM widgets above this line.
# **********************************************

# Add in designer widget plugins from other classes via entrypoints:
globals().update(**get_widgets_from_entrypoints())
