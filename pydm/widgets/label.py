from .base import PyDMWidget
from ..PyQt.QtGui import QLabel
from ..PyQt.QtCore import Qt, pyqtProperty, Q_ENUMS

try:
    # unichr is not available on Py3+
    unichr(1)
except NameError:
    unichr = chr

class PyDMLabel(QLabel, PyDMWidget):
    class DisplayFormat:
        DEFAULT = 0
        STRING = 1
        DECIMAL = 2
        EXPONENTIAL = 3
        HEX = 4
        BINARY = 5
    
    Q_ENUMS(DisplayFormat)
    
    """
    A QLabel with support for Channels and more from PyDM

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """
    def __init__(self, parent=None, init_channel=None):
        QLabel.__init__(self, parent)
        PyDMWidget.__init__(self, init_channel=init_channel)
        self.setTextFormat(Qt.PlainText)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setText("PyDMLabel")
        self._display_format_type = self.DisplayFormat.DEFAULT

    @pyqtProperty(DisplayFormat)
    def displayFormat(self):
        return self._display_format_type

    @displayFormat.setter
    def displayFormat(self, new_type):
        if self._display_format_type != new_type:
            self._display_format_type = new_type

    def parse_value_for_display(self, new_value):
        if self._display_format_type == self.DisplayFormat.DEFAULT:
            return new_value
        elif self._display_format_type == self.DisplayFormat.STRING:
            if isinstance(new_value, str):
                return new_value
            fmt_string = "{}"*len(new_value)
            r = fmt_string.format(*[unichr(x) for x in new_value])
            return r
        elif self._display_format_type == self.DisplayFormat.DECIMAL:
            # This case is taken care by the current string formatting 
            # routine
            return r
        elif self._display_format_type == self.DisplayFormat.EXPONENTIAL:
            fmt_string = "{"+":.{}e".format(self._prec)+"}"
            try:
                r = fmt_string.format(new_value)
            except ValueError:
                print("Could not format value {} to exponential.".format(new_value))
                r = new_value
            return r
        elif self._display_format_type == self.DisplayFormat.HEX:
            # TODO: Implement Hexadecimal formating
            fmt_string = "{:#0X}"
            try:
                r = fmt_string.format(new_value)
            except ValueError:
                print("Could not format value {} to hex.".format(new_value))
                r = new_value
            return r

    def value_changed(self, new_value):
        """
        Callback invoked when the Channel value is changed.
        Sets the value of new_value accordingly at the Label.

        Parameters
        ----------
        new_value : str, int, float, bool or np.ndarray
            The new value from the channel. The type depends on the channel.
        """
        super(PyDMLabel, self).value_changed(new_value)
        # If the value is a string, just display it as-is, no formatting
        # needed.
        if isinstance(new_value, str):
            self.setText(new_value)
            return
        # If the value is an enum, display the appropriate enum string for
        # the value.
        if self.enum_strings is not None and isinstance(new_value, int):
            try:
                self.setText(self.enum_strings[new_value])
            except IndexError:
                self.setText("**INVALID**")
            return
        # If the value is a number (float or int), display it using a
        # format string if necessary.
        if isinstance(new_value, (int, float)):
            self.setText(self.format_string.format(new_value))
            return
        # If you made it this far, just turn whatever the heck the value
        # is into a string and display it.
        self.setText(str(new_value))
