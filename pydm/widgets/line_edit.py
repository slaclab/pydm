import locale
from functools import partial
import numpy as np

import logging
logger = logging.getLogger(__name__)

from qtpy.QtWidgets import QLineEdit, QMenu, QApplication
from qtpy.QtCore import Property, Q_ENUMS
from .. import utilities
from .base import PyDMWritableWidget
from .display_format import DisplayFormat, parse_value_for_display


class PyDMLineEdit(QLineEdit, PyDMWritableWidget, DisplayFormat):
    Q_ENUMS(DisplayFormat)
    DisplayFormat = DisplayFormat
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

    def __init__(self, parent=None, init_channel=None):
        QLineEdit.__init__(self, parent)
        PyDMWritableWidget.__init__(self, init_channel=init_channel)
        self.app = QApplication.instance()
        self._display = None
        self._scale = 1

        self.returnPressed.connect(self.send_value)
        self.setEnabled(False)
        self.unitMenu = QMenu('Convert Units', self)
        self.create_unit_options()
        self._display_format_type = self.DisplayFormat.Default
        self._string_encoding = "utf_8"
        if utilities.is_pydm_app():
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
        super(PyDMLineEdit, self).value_changed(new_val)
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
            send_value = send_value[:-len(self._unit)].strip()
        try:
            if self.channeltype not in [str, np.ndarray]:
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

                num_value = num_value / scale
                self.send_value_signal[self.channeltype].emit(num_value)
            elif self.channeltype == np.ndarray:
                # Arrays will be in the [1.2 3.4 22.214] format
                if self._display_format_type == DisplayFormat.String:
                    self.send_value_signal[str].emit(send_value)
                else:
                    arr_value = list(filter(None, send_value.replace("[", "").replace("]", "").split(" ")))
                    arr_value = np.array(arr_value, dtype=self.subtype)
                    self.send_value_signal[np.ndarray].emit(arr_value)
            else:
                # Channel Type is String
                # Lets just send what we have after all
                self.send_value_signal[str].emit(send_value)
        except ValueError:
            logger.exception("Error trying to set data '{0}' with type '{1}' and format '{2}' at widget '{3}'."
                         .format(self.text(), self.channeltype, self._display_format_type, self.objectName()))

        self.clearFocus()
        self.set_display()

    def write_access_changed(self, new_write_access):
        """
        Change the PyDMLineEdit to read only if write access is denied
        """
        super(PyDMLineEdit, self).write_access_changed(new_write_access)
        self.setEnabled(True)
        self.setReadOnly(not new_write_access)

    def unit_changed(self, new_unit):
        """
        Accept a unit to display with a channel's value

        The unit may or may not be displayed based on the :attr:`showUnits`
        attribute. Receiving a new value for the unit causes the display to
        reset.
        """
        super(PyDMLineEdit, self).unit_changed(new_unit)
        self._scale = 1
        self.create_unit_options()

    def create_unit_options(self):
        """
        Create the menu for displaying possible unit values

        The menu is filled with possible unit conversions based on the
        current PyDMLineEdit. If either the unit is not found in the by
        the :func:`utilities.find_unit_options` function, or, the
        :attr:`.showUnits` attribute is set to False, the menu will tell
        the user that there are no available conversions
        """
        self.unitMenu.clear()
        units = utilities.find_unit_options(self._unit)
        if units and self._show_units:
            for choice in units:
                self.unitMenu.addAction(choice,
                                        partial(
                                            self.apply_conversion,
                                            choice
                                            )
                                        )
        else:
            self.unitMenu.addAction('No Unit Conversions found')

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
            logging.warning("Warning: Attempting to convert PyDMLineEdit unit, but '{0}' can not be converted to '{1}'."
                            .format(self._unit, unit))

    def widget_ctx_menu(self):
        """
        Fetch the Widget specific context menu which will be populated with additional tools by `assemble_tools_menu`.

        Returns
        -------
        QMenu or None
            If the return of this method is None a new QMenu will be created by `assemble_tools_menu`.
        """
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

        if self._display_format_type in [DisplayFormat.Default,
                                         DisplayFormat.Decimal,
                                         DisplayFormat.Exponential,
                                         DisplayFormat.Hex,
                                         DisplayFormat.Binary]:
            if not isinstance(new_value, (str, np.ndarray)):
                try:
                    new_value *= self.channeltype(self._scale)
                except TypeError:
                    logger.error("Cannot convert the value '{0}', for channel '{1}', to type '{2}'. ".format(
                        self._scale, self._channel, self.channeltype))

        new_value = parse_value_for_display(value=new_value,  precision=self._prec,
                                            display_format_type=self._display_format_type,
                                            string_encoding=self._string_encoding,
                                            widget=self)

        self._display = str(new_value)

        if self._display_format_type == DisplayFormat.Default:
            if isinstance(new_value, (int, float)):
                self._display = str(self.format_string.format(new_value))
                self.setText(self._display)
                return

        if self._show_units:
            self._display += " {}".format(self._unit)

        self.setText(self._display)

    def focusOutEvent(self, event):
        """
        Overwrites the function called when a user leaves a PyDMLineEdit
        without pressing return.  Resets the value of the text field to the
        current channel value.
        """
        if self._display is not None:
            self.setText(self._display)
        super(PyDMLineEdit, self).focusOutEvent(event)
