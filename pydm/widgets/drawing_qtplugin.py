from .qtplugin_base import qtplugin_factory
from .drawing import (PyDMDrawingLine, PyDMDrawingRectangle, PyDMDrawingTriangle,
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
