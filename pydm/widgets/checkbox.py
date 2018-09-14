from qtpy.QtWidgets import QCheckBox
from .base import PyDMWritableWidget


class PyDMCheckbox(QCheckBox, PyDMWritableWidget):
    """
    A QCheckbox with support for Channels and more from PyDM

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.

    """
    def __init__(self, parent=None, init_channel=None):
        QCheckBox.__init__(self, parent)
        PyDMWritableWidget.__init__(self, init_channel=init_channel)
        self.clicked.connect(self.send_value)

    def value_changed(self, new_val):
        """
        Callback invoked when the Channel value is changed.
        Sets the checkbox checked or not based on the new value.

        Parameters
        ----------
        new_val : int
            The new value from the channel.
        """
        super(PyDMCheckbox, self).value_changed(new_val)
        if new_val is None:
            return
        if new_val > 0:
            self.setChecked(True)
        else:
            self.setChecked(False)

    def send_value(self, checked):
        """
        Method that emit the signal to notify the Channel that a new
        value was written at the widget.

        Parameters
        ----------
        checked : bool
            True in case the checkbox was checked, False otherwise.
        """
        if checked:
            self.send_value_signal.emit(1)
        else:
            self.send_value_signal.emit(0)
