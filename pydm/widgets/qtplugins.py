from .qtplugin_base import qtplugin_factory

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

# Time Plot plugin
from .timeplot_qtplugin import PyDMTimePlotPlugin
# Waveform Plot plugin
from .waveformplot_qtplugin import PyDMWaveformPlotPlugin

# Byte plugin
PyDMByteIndicatorPlugin = qtplugin_factory(PyDMByteIndicator)

# Checkbox plugin
PyDMCheckboxPlugin = qtplugin_factory(PyDMCheckbox)

# Drawing plugins
PyDMDrawingImagePlugin = qtplugin_factory(PyDMDrawingImage)
PyDMDrawingLinePlugin = qtplugin_factory(PyDMDrawingLine)
PyDMDrawingRectanglePlugin = qtplugin_factory(PyDMDrawingRectangle)
PyDMDrawingTrianglePlugin = qtplugin_factory(PyDMDrawingTriangle)
PyDMDrawingEllipsePlugin = qtplugin_factory(PyDMDrawingEllipse)
PyDMDrawingCirclePlugin = qtplugin_factory(PyDMDrawingCircle)
PyDMDrawingArcPlugin = qtplugin_factory(PyDMDrawingArc)
PyDMDrawingPiePlugin = qtplugin_factory(PyDMDrawingPie)
PyDMDrawingChordPlugin = qtplugin_factory(PyDMDrawingChord)

# Embedded Display plugin
PyDMEmbeddedDisplayPlugin = qtplugin_factory(PyDMEmbeddedDisplay)

# Enum Combobox plugin
PyDMEnumComboBoxPlugin = qtplugin_factory(PyDMEnumComboBox)


# Image plugin
PyDMImageViewPlugin = qtplugin_factory(PyDMImageView)

# Indicator plugin
PyDMIndicatorPlugin = qtplugin_factory(PyDMIndicator)

# Label plugin
PyDMLabelPlugin = qtplugin_factory(PyDMLabel)

# Line Edit plugin
PyDMLineEditPlugin = qtplugin_factory(PyDMLineEdit)

# Push Button plugin
PyDMPushButtonPlugin = qtplugin_factory(PyDMPushButton)


# Related Display Button plugin
PyDMRelatedDisplayButtonPlugin = qtplugin_factory(PyDMRelatedDisplayButton)

# Shell Command plugin
PyDMShellCommandPlugin = qtplugin_factory(PyDMShellCommand)

# Slider plugin
PyDMSliderPlugin = qtplugin_factory(PyDMSlider)


# Spinbox plugin
PyDMSpinboxplugin = qtplugin_factory(PyDMSpinbox)

# Symbol plugin
PyDMSymbolPlugin = qtplugin_factory(PyDMSymbol)

# Waveform Table plugin
PyDMWaveformTablePlugin = qtplugin_factory(PyDMWaveformTable)
