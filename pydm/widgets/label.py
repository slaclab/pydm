from .base import PyDMWidget, TextFormatter, str_types, PostParentClassInitSetup
from qtpy.QtWidgets import QLabel, QApplication
from qtpy.QtCore import Qt, Property
from .display_format import DisplayFormat, parse_value_for_display
from pydm.utilities import is_pydm_app, is_qt_designer, ACTIVE_QT_WRAPPER, QtWrapperTypes
from pydm import config
from pydm.widgets.base import only_if_channel_set

_labelRuleProperties = {"Text": ["value_changed", str]}


class PyDMLabel(QLabel, TextFormatter, PyDMWidget):
    """
    A QLabel with support for setting the text via a PyDM Channel, or
    through the PyDM Rules system.

    .. note::
        If a PyDMLabel is configured to use a Channel, and also with a rule which changes the 'Text' property,
        the behavior is undefined.  Use either
        the Channel *or* a text rule, but not both.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

    new_properties = _labelRuleProperties

    if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYQT5:
        from PyQt5.QtCore import Q_ENUM

        Q_ENUM(DisplayFormat)

    DisplayFormat = DisplayFormat

    # Make enum definitions known to this class
    Default = DisplayFormat.Default
    String = DisplayFormat.String
    Decimal = DisplayFormat.Decimal
    Exponential = DisplayFormat.Exponential
    Hex = DisplayFormat.Hex
    Binary = DisplayFormat.Binary

    def __init__(self, parent=None, init_channel=None):
        QLabel.__init__(self, parent)
        PyDMWidget.__init__(self, init_channel=init_channel)
        self.app = QApplication.instance()
        self.setTextFormat(Qt.PlainText)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setText("######")
        self._display_format_type = self.DisplayFormat.Default
        self._string_encoding = "utf_8"
        self._enable_rich_text = False
        if is_pydm_app():
            self._string_encoding = self.app.get_string_encoding()
        # Execute setup calls that must be done here in the widget class's __init__,
        # and after it's parent __init__ calls have completed.
        # (so we can avoid pyside6 throwing an error, see func def for more info)
        PostParentClassInitSetup(self)

    # On pyside6, we need to expilcity call pydm's base class's eventFilter() call or events
    # will not propagate to the parent classes properly.
    def eventFilter(self, obj, event):
        return PyDMWidget.eventFilter(self, obj, event)

    @Property(bool)
    def enableRichText(self):
        return self._enable_rich_text

    @enableRichText.setter
    def enableRichText(self, new_value):
        if self._enable_rich_text == new_value:
            return
        self._enable_rich_text = new_value

        if self._enable_rich_text:
            self.setTextFormat(Qt.RichText)
        else:
            self.setTextFormat(Qt.PlainText)

    @Property(DisplayFormat)
    def displayFormat(self):
        """
        displayFormat property.

        :getter: Returns the displayFormat
        :setter: Sets the displayFormat
        :type: int
        """
        return self._display_format_type

    @displayFormat.setter
    def displayFormat(self, new_type):
        if self._display_format_type == new_type:
            return
        self._display_format_type = new_type
        if not is_qt_designer() or config.DESIGNER_ONLINE:
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
        super().value_changed(new_value)
        new_value = parse_value_for_display(
            value=new_value,
            precision=self.precision,
            display_format_type=self._display_format_type,
            string_encoding=self._string_encoding,
            widget=self,
        )
        # If the value is a string, just display it as-is, no formatting
        # needed.
        if isinstance(new_value, str_types):
            if self._show_units and self._unit != "":
                new_value = "{} {}".format(new_value, self._unit)
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

    @only_if_channel_set
    def check_enable_state(self):
        """If the channel this label is connected to becomes disconnected, display only the name of the channel."""
        if not self._connected:
            self.setText(self.channel)
        super().check_enable_state()
