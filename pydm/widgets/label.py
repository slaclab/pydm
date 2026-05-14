from datetime import datetime
from qtpy.QtCore import Qt, QTimer
from qtpy.QtWidgets import QLabel, QApplication

from pydm import config
from pydm.utilities import is_pydm_app, is_qt_designer, ACTIVE_QT_WRAPPER, QtWrapperTypes
from pydm.widgets.base import only_if_channel_set

from .base import PyDMWidget, TextFormatter, str_types, PostParentClassInitSetup
from .display_format import DisplayFormat, parse_value_for_display

if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYSIDE6:
    from PySide6.QtCore import Property
else:
    from PyQt5.QtCore import pyqtProperty as Property

_labelRuleProperties = {"Text": ["value_changed", str]}


class PyDMLabel(QLabel, TextFormatter, PyDMWidget):
    """
    A QLabel with support for setting the text via a PyDM Channel, or
    through the PyDM Rules system.

    .. note::
        If a PyDMLabel is configured to use a Channel, and also with a rule which changes
        the 'Text' property, the behavior is undefined. Use either the Channel *or* a
        text rule, but not both.

    **System Time Display Mode**:
    The widget can also display the current system time instead of the channel value.
    Set `showCurrentTime` to `True` to enable this mode. The time format can be
    customized via the `timeFormat` property, which supports standard `strftime`
    directives plus `%A` (full weekday name) and `%f` (milliseconds, 3 digits).
    The update interval is automatically adjusted: 10 ms when `%f` is present,
    otherwise 1 second.

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

        # ---------- System time display attributes ----------
        self._show_current_time = False
        self._time_format = "%Y-%m-%d %H:%M:%S.%f %A"
        self._time_update_timer = QTimer(self)
        self._time_update_timer.timeout.connect(self._update_current_time)

        # English weekday names (Monday = 0, Sunday = 6)
        self._weekday_map_en = {
            0: "Monday",
            1: "Tuesday",
            2: "Wednesday",
            3: "Thursday",
            4: "Friday",
            5: "Saturday",
            6: "Sunday",
        }
        # ---------------------------------------------------

        if is_pydm_app():
            self._string_encoding = self.app.get_string_encoding()

        PostParentClassInitSetup(self)

    def eventFilter(self, obj, event):
        """Filter events for the widget."""
        return PyDMWidget.eventFilter(self, obj, event)

    # ----------------------------------------------------------------------
    # Rich text property
    # ----------------------------------------------------------------------
    def readEnableRichText(self):
        """Return whether rich text is enabled."""
        return self._enable_rich_text

    def setEnableRichText(self, new_value):
        """Enable or disable rich text display."""
        if self._enable_rich_text == new_value:
            return
        self._enable_rich_text = new_value

        if self._enable_rich_text:
            self.setTextFormat(Qt.RichText)
        else:
            self.setTextFormat(Qt.PlainText)

        # If system time mode is active, refresh the display to apply the new format.
        if self._show_current_time:
            self._update_current_time()
        else:
            self.value_changed(self.value)

    enableRichText = Property(bool, readEnableRichText, setEnableRichText)

    # ----------------------------------------------------------------------
    # Display format property
    # ----------------------------------------------------------------------
    def readDisplayFormat(self):
        """
        Display format property.

        :getter: Returns the displayFormat
        :setter: Sets the displayFormat
        :type: int
        """
        return self._display_format_type

    def setDisplayFormat(self, new_type):
        """Set the display format for numeric values."""
        if self._display_format_type == new_type:
            return
        self._display_format_type = new_type
        if not is_qt_designer() or config.DESIGNER_ONLINE:
            self.value_changed(self.value)

    displayFormat = Property(DisplayFormat, readDisplayFormat, setDisplayFormat)

    # ----------------------------------------------------------------------
    # System time display properties and methods
    # ----------------------------------------------------------------------
    def readShowCurrentTime(self):
        """
        Whether to show the current system time instead of the channel value.

        :getter: Returns True if system time is shown.
        :setter: Sets whether to show system time.
        :type: bool
        """
        return self._show_current_time

    def setShowCurrentTime(self, show):
        """
        Enable or disable system time display mode.

        When enabled, the label ignores the channel value and displays a
        continuously updated clock. When disabled, it reverts to showing
        the channel value (if any).

        Parameters
        ----------
        show : bool
            True -> show system time; False -> show channel value.
        """
        if self._show_current_time == show:
            return

        self._show_current_time = show

        if self._show_current_time:
            self._update_timer_interval()
            self._update_current_time()
        else:
            self._time_update_timer.stop()
            # Force an update of the channel value display using the latest cached value.
            self.value_changed(self.value)

    showCurrentTime = Property(bool, readShowCurrentTime, setShowCurrentTime)

    def readTimeFormat(self):
        """
        Format string for system time display.

        :getter: Returns the time format string.
        :setter: Sets the time format string.
        :type: str
        """
        return self._time_format

    def setTimeFormat(self, time_format):
        """
        Set the time display format.

        Supports standard ``strftime`` directives, plus:
        - ``%A`` : full weekday name in English (Monday, Tuesday, ...)
        - ``%f`` : milliseconds as a three-digit number (000-999)

        If the format string contains ``%f``, the update interval is set to 10 ms
        to achieve millisecond precision; otherwise it is set to 1 second.

        Parameters
        ----------
        time_format : str
            Format string, e.g. "%Y-%m-%d %H:%M:%S" or "%Y-%m-%d %H:%M:%S.%f %A"
        """
        if self._time_format == time_format:
            return

        self._time_format = time_format
        if self._show_current_time:
            self._update_timer_interval()
            self._update_current_time()

    timeFormat = Property(str, readTimeFormat, setTimeFormat)

    def _update_timer_interval(self):
        """Adjust the timer interval based on whether milliseconds are requested."""
        self._time_update_timer.stop()
        if "%f" in self._time_format:
            self._time_update_timer.start(10)  # 10 ms for millisecond precision
        else:
            self._time_update_timer.start(1000)  # 1 second otherwise

    def _update_current_time(self):
        """
        Update the label text with the current system time.

        Handles the custom placeholders ``%A`` (weekday name) and ``%f`` (milliseconds)
        before passing the string to `strftime`. In case of an error (e.g., invalid
        format), an error message is displayed.
        """
        if not self._show_current_time:
            return

        try:
            now = datetime.now()
            time_str = self._time_format

            # Replace weekday placeholder with English name
            if "%A" in time_str:
                weekday = now.weekday()  # Monday = 0, Sunday = 6
                weekday_str = self._weekday_map_en.get(weekday, "")
                time_str = time_str.replace("%A", weekday_str)

            # Replace millisecond placeholder with three-digit number
            if "%f" in time_str:
                milliseconds = now.microsecond // 1000
                time_str = time_str.replace("%f", f"{milliseconds:03d}")

            # Standard strftime for remaining directives
            formatted = now.strftime(time_str)

            # Avoid unnecessary text change signals if the text hasn't changed
            if self.text() != formatted:
                self.setText(formatted)
        except Exception as e:
            self.setText(f"Time Format Error: {str(e)}")

    # ----------------------------------------------------------------------
    # PyDMWidget overrides
    # ----------------------------------------------------------------------
    def value_changed(self, new_value):
        """
        Callback invoked when the Channel value changes.

        The internal state is always updated via the base class.
        If system time display is active, the label text is not updated;
        otherwise, the value is formatted and displayed according to the
        current display format, units, and enumeration strings.

        Parameters
        ----------
        new_value : str, int, float, bool or np.ndarray
            The new value from the channel.
        """
        # Always update the cached value in the base class.
        super().value_changed(new_value)

        # Do not update the displayed text when in system time mode.
        if self._show_current_time:
            return

        # Format the value for display.
        new_value = parse_value_for_display(
            value=new_value,
            precision=self.precision,
            display_format_type=self._display_format_type,
            string_encoding=self._string_encoding,
            widget=self,
        )

        if isinstance(new_value, str_types):
            if self._show_units and self._unit != "":
                new_value = "{} {}".format(new_value, self._unit)
            self.setText(new_value)
            return

        if self.enum_strings is not None and isinstance(new_value, int):
            try:
                self.setText(self.enum_strings[new_value])
            except IndexError:
                self.setText("**INVALID**")
            return

        if isinstance(new_value, (int, float)):
            self.setText(self.format_string.format(new_value))
            return

        self.setText(str(new_value))

    @only_if_channel_set
    def check_enable_state(self):
        """
        Overridden to prevent displaying the channel name when system time mode is active.
        """
        if self._show_current_time:
            # Still need to call base class to maintain internal state.
            super().check_enable_state()
            return

        if not self._connected:
            self.setText(self.channel)
        super().check_enable_state()
