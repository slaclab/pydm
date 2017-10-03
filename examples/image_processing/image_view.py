from pydm.PyQt.QtCore import QObject, pyqtSlot, pyqtSignal
from pydm.widgets.channel import PyDMChannel
from pydm import Display
import numpy as np
from os import path
from skimage.feature import blob_doh
from marker import ImageMarker
from pyqtgraph import mkPen

class ImageViewer(Display):
    def __init__(self, parent=None, args=None):
        super(ImageViewer, self).__init__(parent=parent, args=args)
        self.image_channel = "ca://MTEST:TwoSpotImage"
        self.image_width_channel = "ca://MTEST:ImageWidth"
        self.ui.imageView.widthChannel = self.image_width_channel
        self.ui.imageView.image_channel = ""
        self.markers = []
        
    def ui_filename(self):
        return 'image_view.ui'
        
    def ui_filepath(self):
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())
    
    @pyqtSlot(np.ndarray)
    def new_image_received(self, new_waveform):
        #Reshape the 1D waveform into 2D
        img = new_waveform.reshape((int(512),-1), order='C')
        #Find blobs in the image with scikit-image
        blobs= blob_doh(img, max_sigma=512, min_sigma=64, threshold=.02)
        #Remove any existing blob markers        
        for m in self.markers:
            self.ui.imageView.getView().removeItem(m)
        self.markers = []
        #For each blob, add a blob marker to the image
        for blob in blobs:
            x, y, size = blob
            m = ImageMarker((y,x), size=size, pen=mkPen((100,100,255), width=3))
            self.ui.imageView.getView().addItem(m)
            self.markers.append(m)
        #Show number of blobs in text label  
        self.ui.numBlobsLabel.setText(str(len(blobs)))
        #Send the original image data to the image widget
        self.ui.imageView.image_value_changed(new_waveform)
    
    def channels(self):
        return [PyDMChannel(address=self.image_channel, value_slot=self.new_image_received)]

intelclass = ImageViewer
