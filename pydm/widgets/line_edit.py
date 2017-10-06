from functools import partial
from ..PyQt.QtGui import QLineEdit, QMenu
from ..PyQt.QtCore import Qt
from .. import utilities
from .base import PyDMWritableWidget

class PyDMLineEdit(QLineEdit, PyDMWritableWidget):
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
        self._display = None
        self._scale = 1

        self.returnPressed.connect(self.send_value)
        self.setEnabled(False)

        # Create Context Menu upon Right Click
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.launch_menu)
        self.menu = QMenu(self)
        self.unitMenu = self.menu.addMenu('Convert Units')
        self.create_unit_options()

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
        if self._unit:
            send_value = send_value.replace(self._unit, '')

        # Remove scale factor
        if self._scale and self.channeltype != type(""):
            send_value = (self.channeltype(send_value)
                          / self.channeltype(self._scale))

        self.send_value_signal[self.channeltype].emit(self.channeltype(send_value))
        self.clearFocus()
        self.set_display()

    def write_access_changed(self, new_write_access):
        """
        Change the PyDMLineEdit to read only if write access is denied
        """
        super(PyDMLineEdit, self).write_access_changed(new_write_access)
        self.setEnabled(True)
        self.setReadOnly(not new_write_access)

    def precision_changed(self, new_precision):
        super(PyDMLineEdit, self).precision_changed(new_precision)
        self.set_display()

    def unit_changed(self, new_unit):
        """
        Accept a unit to display with a channel's value

        The unit may or may not be displayed based on the :attr:`showUnits`
        attribute. Receiving a new value for the unit causes the display to
        reset.
        """
        super(PyDMLineEdit, self).unit_changed(new_unit)
        self._scale = 1
        self.set_display()
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
            print('Warning: Attempting to convert PyDMLineEdit unit, '\
                           'but no initial units supplied')
            return None

        scale = utilities.convert(str(self._unit), unit)
        if scale:
            self._scale = scale * float(self._scale)
            self._unit = unit
            self.update_format_string()
            self.clearFocus()
            self.set_display()
        else:
            print('Warning: Attempting to convert PyDMLineEdit unit, but {:} '\
                           'can not be converted to {:}'.format(self._units, unit))

    def launch_menu(self, point):
        """
        Launch the context menu with the appropriate unit conversions.

        Parameters
        ----------
        point : QPoint
        """
        return self.menu.exec_(self.mapToGlobal(point))

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
        value = self.value
        if not isinstance(value, str):
            if self._scale and value:
                value *= self.channeltype(self._scale)

        if self.format_string:
            value = self.format_string.format(value)

        self._display = str(value)

        if not self.hasFocus():
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
