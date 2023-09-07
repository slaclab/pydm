from qtpy import QtGui
from pyqtgraph import Point, ROI


class ImageMarker(ROI):
    """A crosshair ROI.  Returns the full image line-out for X and Y at the position of the crosshair."""

    def __init__(self, pos=None, size=None, **kargs):
        if size is None:
            # size = [100e-6,100e-6]
            size = [20, 20]
        if pos is None:
            pos = [0, 0]
        self._shape = None
        ROI.__init__(self, pos, size, **kargs)

        self.sigRegionChanged.connect(self.invalidate)
        self.aspectLocked = True

    def invalidate(self):
        self._shape = None
        self.prepareGeometryChange()

    def boundingRect(self):
        return self.shape().boundingRect()

    def getArrayRegion(self, data, img, axes=(0, 1)):
        # img_point = self.mapToItem(img, self.pos())
        coords = self.getPixelCoords()
        ystrip = data[coords[0], :]
        xstrip = data[:, coords[1]]
        return ([xstrip, ystrip], coords)

    def getPixelCoords(self):
        img_point = self.pos()
        return (int(img_point.x()), int(img_point.y()))

    def shape(self):
        if self._shape is None:
            radius = self.getState()["size"][1]
            p = QtGui.QPainterPath()
            p.moveTo(Point(0, -radius))
            p.lineTo(Point(0, radius))
            p.moveTo(Point(-radius, 0))
            p.lineTo(Point(radius, 0))
            p = self.mapToDevice(p)
            stroker = QtGui.QPainterPathStroker()
            stroker.setWidth(10)
            outline = stroker.createStroke(p)
            self._shape = self.mapFromDevice(outline)
        return self._shape

    def paint(self, p, *args):
        radius = self.getState()["size"][1]
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(self.currentPen)
        p.drawLine(Point(0, -radius), Point(0, radius))
        p.drawLine(Point(-radius, 0), Point(radius, 0))
