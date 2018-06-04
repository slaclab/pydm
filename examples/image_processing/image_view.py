from pydm.PyQt.QtCore import QObject, pyqtSlot, pyqtSignal
from pydm.widgets.channel import PyDMChannel
from pydm import Display
import numpy as np
import threading
from os import path
from skimage.feature import blob_doh
from marker import ImageMarker
from pyqtgraph import mkPen


class ImageViewer(Display):
    signalMarkers = pyqtSignal(dict)

    def __init__(self, parent=None, args=None):
        super(ImageViewer, self).__init__(parent=parent, args=args)
        self.markers_lock = threading.Lock()
        self.ui.imageView.process_image = self.process_image
        self.signalMarkers.connect(self.make_markers)
        self.markers = []

    def ui_filename(self):
        return 'image_view.ui'

    def ui_filepath(self):
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())

    @pyqtSlot(dict)
    def make_markers(self, args):
        delete = args['delete']
        markers = args['markers']
        for m in markers:
            if delete:
                self.ui.imageView.getView().removeItem(m)
                return
            self.ui.imageView.getView().addItem(m)
            # Show number of blobs in text label
            self.ui.numBlobsLabel.setText(str(len(markers)))

    def process_image(self, new_image):
        # Find blobs in the image with scikit-image
        blobs = blob_doh(new_image, max_sigma=512, min_sigma=64, threshold=.02)
        # Remove any existing blob markers
        self.signalMarkers.emit({'delete': True, 'markers': self.markers})
        self.markers = []
        # For each blob, add a blob marker to the image
        for blob in blobs:
            x, y, size = blob
            m = ImageMarker((y, x), size=size, pen=mkPen((100, 100, 255), width=3))
            self.markers.append(m)
        self.signalMarkers.emit({'delete': False, 'markers': self.markers})
        # Send the original image data to the image widget
        return new_image


intelclass = ImageViewer
