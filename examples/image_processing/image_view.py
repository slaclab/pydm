from pydm import Display
import threading
from os import path
from skimage.feature import blob_doh
from marker import ImageMarker
from pyqtgraph import mkPen


class ImageViewer(Display):

    def __init__(self, parent=None, args=None):
        super(ImageViewer, self).__init__(parent=parent, args=args)
        self.markers_lock = threading.Lock()
        self.ui.imageView.process_image = self.process_image
        self.ui.imageView.newImageSignal.connect(self.draw_markers)
        self.markers = list()
        self.blobs = list()

    def ui_filename(self):
        return 'image_view.ui'

    def draw_markers(self, *args, **kwargs):
        with self.markers_lock:
            for m in self.markers:
                if m in self.ui.imageView.getView().addedItems:
                    self.ui.imageView.getView().removeItem(m)

            for blob in self.blobs:
                x, y, size = blob
                m = ImageMarker((y, x), size=size, pen=mkPen((100, 100, 255), width=3))
                self.markers.append(m)
                self.ui.imageView.getView().addItem(m)

            self.ui.numBlobsLabel.setText(str(len(self.blobs)))

    def process_image(self, new_image):
        # Find blobs in the image with scikit-image
        self.blobs = blob_doh(new_image, max_sigma=512, min_sigma=64, threshold=.02)

        # Send the original image data to the image widget
        return new_image


intelclass = ImageViewer
