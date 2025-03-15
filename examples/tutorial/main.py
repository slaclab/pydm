from os import path
from pydm import Display
from scipy.ndimage.measurements import maximum_position


class BeamPositioning(Display):
    def __init__(self, parent=None, args=None):
        super().__init__(parent=parent, args=args)
        # Attach our custom process_image method
        self.ui.imageView.process_image = self.process_image
        # Hook up to the newImageSignal so we can update
        # our widgets after the new image is done
        self.ui.imageView.newImageSignal.connect(self.show_blob)
        # Store blob coordinate
        self.blob = (0, 0)

    def ui_filename(self):
        # Point to our UI file
        return "main.ui"

    def ui_filepath(self):
        # Return the full path to the UI file
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())

    def show_blob(self, *args, **kwargs):
        # If we have a blob, present the coordinates at label
        if self.blob != (0, 0):
            blob_txt = "Blob Found:"
            blob_txt += " ({}, {})".format(self.blob[1], self.blob[0])
        else:
            # If no blob was found, present the "Not Found" message
            blob_txt = "Blob Not Found"
        # Update the label text
        self.ui.lbl_blobs.setText(blob_txt)

    def process_image(self, new_image):
        # Consider the maximum as the Blob since we have only
        # one blob.
        self.blob = maximum_position(new_image)
        # Send the original image data to the image widget
        return new_image
