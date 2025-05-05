import locale
import numpy as np
import ast
import shlex
import logging
from functools import partial
from qtpy.QtWidgets import QLineEdit, QMenu, QApplication
from qtpy.QtCore import Property, Qt
from qtpy.QtGui import QFocusEvent
from .base import PyDMWritableWidget, TextFormatter, str_types, PostParentClassInitSetup
from pydm import utilities
from .display_format import DisplayFormat, parse_value_for_display
from pydm.utilities import ACTIVE_QT_WRAPPER, QtWrapperTypes

logger = logging.getLogger(__name__)


class PyDMLineEdit(QLineEdit, TextFormatter, PyDMWritableWidget):
    """
    A QLineEdit (writable text field) with support for Channels and more
    from PyDM.
    This widget offers an unit conversion menu when users Right Click
    into it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """

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
        QLineEdit.__init__(self, parent)
        PyDMWritableWidget.__init__(self, init_channel=init_channel)
        self.app = QApplication.instance()
        self._display = None
        self._has_displayed_value_yet = False
        self._scale = 1

        self.returnPressed.connect(self.send_value)
        self.unitMenu = None
        self._display_format_type = self.DisplayFormat.Default
        self._string_encoding = "utf_8"
        self._user_set_read_only = False  # Are we *really* read only?
        if utilities.is_pydm_app():
            self._string_encoding = self.app.get_string_encoding()
        # Execute setup calls that must be done here in the widget class's __init__,
        # and after it's parent __init__ calls have completed.
        # (so we can avoid pyside6 throwing an error, see func def for more info)
        PostParentClassInitSetup(self)

    # On pyside6, we need to expilcity call pydm's base class's eventFilter() call or events
    # will not propagate to the parent classes properly.
    def eventFilter(self, obj, event):
        return PyDMWritableWidget.eventFilter(self, obj, event)

    @Property(DisplayFormat)
    def displayFormat(self):
        return self._display_format_type

    @displayFormat.setter
    def displayFormat(self, new_type):
        if self._display_format_type != new_type:
            self._display_format_type = new_type
            # Trigger the update of display format
            self.value_changed(self.value)

    def value_changed(self, new_val):
        """
        Receive and update the PyDMLineEdit for a new channel value

        The actual value of the input is saved as well as the type received.
        This also resets the PyDMLineEdit display text using
        :meth:`.set_display`

        Parameters
        ----------
        value: str, float or int
            The new value of the channel
        """
        super().value_changed(new_val)
        self.set_display()

    def send_value(self):
        """
        Emit a :attr:`send_value_signal` to update channel value.

        The text is cleaned of all units, user-formatting and scale values
        before being sent back to the channel. This function is attached the
        ReturnPressed signal of the PyDMLineEdit
        """
        send_value = str(self.text())
        # Clean text of unit string
        if self._show_units and self._unit and self._unit in send_value:
            send_value = send_value[: -len(self._unit)].strip()
        try:
            if self.channeltype not in [str, np.ndarray, bool]:
                scale = self._scale
                if scale is None or scale == 0:
                    scale = 1.0

                if self._display_format_type in [DisplayFormat.Default, DisplayFormat.String]:
                    if self.channeltype == float:
                        num_value = locale.atof(send_value)
                    else:
                        num_value = self.channeltype(send_value)
                    scale = self.channeltype(scale)
                elif self._display_format_type == DisplayFormat.Hex:
                    num_value = int(send_value, 16)
                elif self._display_format_type == DisplayFormat.Binary:
                    num_value = int(send_value, 2)
                elif self._display_format_type in [DisplayFormat.Exponential, DisplayFormat.Decimal]:
                    num_value = locale.atof(send_value)

                num_value = self.channeltype(num_value / scale)
                self.send_value_signal[self.channeltype].emit(num_value)
            elif self.channeltype == np.ndarray:
                # Arrays will be in the [1.2 3.4 22.214] format
                if self._display_format_type == DisplayFormat.String:
                    self.send_value_signal[str].emit(send_value)
                else:
                    arr_value = list(
                        filter(None, ast.literal_eval(str(shlex.split(send_value.replace("[", "").replace("]", "")))))
                    )
                    arr_value = np.array(arr_value, dtype=self.subtype)
                    self.send_value_signal[np.ndarray].emit(arr_value)
            elif self.channeltype == bool:
                try:
                    val = bool(PyDMLineEdit.strtobool(send_value))
                    self.send_value_signal[bool].emit(val)
                    # might want to add error to application screen
                except ValueError:
                    logger.error("Not a valid boolean: %r", send_value)
            else:
                # Channel Type is String
                # Lets just send what we have after all
                self.send_value_signal[str].emit(send_value)
        except ValueError:
            logger.exception(
                "Error trying to set data '{0}' with type '{1}' and format '{2}' at widget '{3}'.".format(
                    self.text(), self.channeltype, self._display_format_type, self.objectName()
                )
            )

        self.clearFocus()
        self.set_display()

    def setReadOnly(self, readOnly):
        self._user_set_read_only = readOnly
        super().setReadOnly(True if self._user_set_read_only else not self._write_access)

    def write_access_changed(self, new_write_access):
        """
        Change the PyDMLineEdit to read only if write access is denied
        """
        super().write_access_changed(new_write_access)
        if not self._user_set_read_only:
            super().setReadOnly(not new_write_access)

    def unit_changed(self, new_unit):
        """
        Accept a unit to display with a channel's value

        The unit may or may not be displayed based on the :attr:`showUnits`
        attribute. Receiving a new value for the unit causes the display to
        reset.
        """
        super().unit_changed(new_unit)
        self._scale = 1

    def create_unit_options(self):
        """
        Create the menu for displaying possible unit values

        The menu is filled with possible unit conversions based on the
        current PyDMLineEdit. If either the unit is not found in the by
        the :func:`utilities.find_unit_options` function, or, the
        :attr:`.showUnits` attribute is set to False, the menu will tell
        the user that there are no available conversions
        """
        if self.unitMenu is None:
            self.unitMenu = QMenu("Convert Units", self)
        else:
            self.unitMenu.clear()

        units = utilities.find_unit_options(self._unit)
        if units and self._show_units:
            for choice in units:
                self.unitMenu.addAction(choice, partial(self.apply_conversion, choice))
        else:
            self.unitMenu.addAction("No Unit Conversions found")

    def apply_conversion(self, unit):
        """
        Convert the current unit to a different one

        This function will attempt to find a scalar to convert the current
        unit type to the desired one and reset the display with the new
        conversion.

        Parameters
        ----------
        unit : str
            String name of desired units
        """
        if not self._unit:
            logger.warning("Warning: Attempting to convert PyDMLineEdit unit, but no initial units supplied.")
            return None

        scale = utilities.convert(str(self._unit), unit)
        if scale:
            self._scale = scale * float(self._scale)
            self._unit = unit
            self.update_format_string()
            self.clearFocus()
            self.set_display()
        else:
            logging.warning(
                "Warning: Attempting to convert PyDMLineEdit unit, but '{0}' can not be converted to '{1}'.".format(
                    self._unit, unit
                )
            )

    def widget_ctx_menu(self):
        """
        Fetch the Widget specific context menu which will be populated with additional tools by `assemble_tools_menu`.

        Returns
        -------
        QMenu or None
            If the return of this method is None a new QMenu will be created by `assemble_tools_menu`.
        """
        self.create_unit_options()

        menu = self.createStandardContextMenu()
        menu.addSeparator()
        menu.addMenu(self.unitMenu)
        return menu

    def set_display(self):
        """
        Set the text display of the PyDMLineEdit.

        The original value given by the PV is converted to a text entry based
        on the current settings for scale value, precision, a user-defined
        format, and the current units. If the user is currently entering a
        value in the PyDMLineEdit the text will not be changed.
        """
        if self.value is None:
            return

        if self.hasFocus():
            return

        new_value = self.value

        if self._display_format_type in [
            DisplayFormat.Default,
            DisplayFormat.Decimal,
            DisplayFormat.Exponential,
            DisplayFormat.Hex,
            DisplayFormat.Binary,
        ]:
            if self.channeltype not in (str, np.ndarray):
                try:
                    new_value *= self.channeltype(self._scale)
                except TypeError:
                    logger.error(
                        "Cannot convert the value '{0}', for channel '{1}', to type '{2}'. ".format(
                            self._scale, self._channel, self.channeltype
                        )
                    )

        new_value = parse_value_for_display(
            value=new_value,
            precision=self.precision,
            display_format_type=self._display_format_type,
            string_encoding=self._string_encoding,
            widget=self,
        )

        self._has_displayed_value_yet = True
        if type(new_value) in str_types:
            self._display = new_value
        else:
            self._display = str(new_value)

        if isinstance(new_value, (int, float)):
            self._display = str(self.format_string.format(new_value))
            self.setText(self._display)
            return

        if self._show_units:
            self._display = "{} {}".format(self._display, self._unit)

        self.setText(self._display)

    def focusInEvent(self, event: QFocusEvent) -> None:
        """
        Checks to see if the line edit has actually received a value before assigning active window or tab focus to it.
        PyQt will automatically give tab focus to the first tab-enabled widget it can on display load. But for this
        widget this behavior can lead to a race condition where if the widget is given focus before the PV has been
        connected long enough to receive a value, then the widget never loads the initial text from the PV.
        """
        if not self._has_displayed_value_yet and (
            event.reason() == Qt.ActiveWindowFocusReason or event.reason() == Qt.TabFocusReason
        ):
            # Clearing focus ensures that the widget will display the value for the PV
            self.clearFocus()
            return
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        """
        Overwrites the function called when a user leaves a PyDMLineEdit
        without pressing return.  Resets the value of the text field to the
        current channel value.
        """
        if self._display is not None:
            self.setText(self._display)
        super().focusOutEvent(event)

    @staticmethod
    def strtobool(val):
        valid_true = ["Y", "YES", "T", "TRUE", "ON", "1"]
        valid_false = ["N", "NO", "F", "FALSE", "OFF", "0"]

        if val.upper() in valid_true:
            return 1
        elif val.upper() in valid_false:
            return 0
        else:
            raise ValueError("invalid boolean input")
