from .base import PyDMWidget
from qtpy.QtWidgets import QLabel, QApplication
from qtpy.QtCore import Qt, Property, Q_ENUMS
from .display_format import DisplayFormat, parse_value_for_display
from pydm.utilities import is_pydm_app


class PyDMLabel(QLabel, PyDMWidget, DisplayFormat):
    Q_ENUMS(DisplayFormat)
    DisplayFormat = DisplayFormat
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
        self.app = QApplication.instance()
        self.setTextFormat(Qt.PlainText)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setText("PyDMLabel")
        self._display_format_type = self.DisplayFormat.Default
        self._string_encoding = "utf_8"
        if is_pydm_app():
            self._string_encoding = self.app.get_string_encoding()

    @Property(DisplayFormat)
    def displayFormat(self):
        return self._display_format_type

    @displayFormat.setter
    def displayFormat(self, new_type):
        if self._display_format_type != new_type:
            self._display_format_type = new_type
            # Trigger the update of display format
            self.value_changed(self.value)

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
        new_value = parse_value_for_display(value=new_value, precision=self._prec,
                                            display_format_type=self._display_format_type,
                                            string_encoding=self._string_encoding,
                                            widget=self)
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
    
    # The methods for precisionFromPV, precision, and showUnits are
    # all defined in PyDMWidget, but we don't expose them as properties there,
    # because not all widgets necessarily need them.
    # A future version of PyDM may move the methods out of PyDMWidget entirely.
    precisionFromPV = Property(bool, PyDMWidget.precisionFromPV,
                          PyDMWidget.setPrecisionFromPV,
                          doc="""
    If True, the widget will use the precision information
    from the Channel, if available.
    """)

    precision = Property(int, PyDMWidget.precision,
                          PyDMWidget.setPrecision,
                          doc="""
    The precision to be used when formatting the output of the PV.
    """)
    
    showUnits = Property(bool, PyDMWidget.showUnits,
                          PyDMWidget.setShowUnits,
                          doc="""
    If set to True, the units given in the channel will be displayed
    with the value. If using an EPICS channel, this will automatically
    be linked to the EGU field of the PV.
    """)
