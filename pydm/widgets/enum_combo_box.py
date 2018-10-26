import logging
logger = logging.getLogger(__name__)

import six
from qtpy.QtWidgets import QComboBox
from qtpy.QtCore import Slot, Qt
from .base import PyDMWritableWidget
from .. import data_plugins


class PyDMEnumComboBox(QComboBox, PyDMWritableWidget):
    """
    A QComboBox with support for Channels and more from PyDM

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.

    Signals
    -------
    send_value_signal : int, float, str, bool or np.ndarray
        Emitted when the user changes the value.
    activated : int, str
        Emitted when the user chooses an item in the combobox.
    currentIndexChanged : int, str
        Emitted when the index is changed in the combobox.
    highlighted : int, str
        Emitted when an item in the combobox popup list is highlighted
        by the user.
    """
    def __init__(self, parent=None, init_channel=None):
        QComboBox.__init__(self, parent)
        PyDMWritableWidget.__init__(self, init_channel=init_channel)
        self._has_enums = False
        self.activated[int].connect(self.internal_combo_box_activated_int)
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.contextMenuEvent = self.open_context_menu

    # Internal methods
    def set_items(self, enums):
        """
        Internal method to fill the ComboBox items based on a list
        of strings.

        Parameters
        ----------
        enums : tuple
            The new list of values
        """
        if not enums:
            logger.error("Invalid enum value '{0}'. The value is expected to be a valid list of string values."
                         .format(enums))
            return

        self.clear()
        for e_str in enums:
            if e_str is None:
                logger.error("Invalid enum type '{0}'. The expected type is 'string'.".format(type(e_str)))
                return

            try:
                self.addItem(e_str)
            except TypeError as error:
                logger.error(
                    "Invalid enum type '{0}'. The expected type is 'string'. Exception: {1}".format(type(e_str), error))
        self._has_enums = True
        self.check_enable_state()

    def check_enable_state(self):
        """
        Checks whether or not the widget should be disable.
        This method also disables the widget and add a Tool Tip
        with the reason why it is disabled.

        """
        status = self._write_access and self._connected and self._has_enums
        tooltip = ""
        if not self._connected:
            tooltip += "PV is disconnected."
        elif not self._write_access:
            if data_plugins.is_read_only():
                tooltip += "Running PyDM on Read-Only mode."
            else:
                tooltip += "Access denied by Channel Access Security."
        elif not self._has_enums:
            tooltip += "Enums not available."

        self.setToolTip(tooltip)
        self.setEnabled(status)

    def enum_strings_changed(self, new_enum_strings):
        """
        Callback invoked when the Channel has new enum values.
        This callback also triggers a value_changed call so the
        new enum values to be broadcasted

        Parameters
        ----------
        new_enum_strings : tuple
            The new list of values
        """
        super(PyDMEnumComboBox, self).enum_strings_changed(new_enum_strings)
        self.set_items(new_enum_strings)

    def value_changed(self, new_val):
        """
        Callback invoked when the Channel value is changed.
        Sets the value of new_value accordingly at the ComboBox.

        Parameters
        ----------
        new_value : str, int, float, bool or np.ndarray
            The new value from the channel. The type depends on the channel.
        """
        if new_val is not None:
            super(PyDMEnumComboBox, self).value_changed(new_val)
            # Integers are straight forward
            if isinstance(new_val, int):
                idx = new_val
            # String values are valid as well, but we need to look up the index
            elif isinstance(new_val, six.text_type):
                idx = self.findText(new_val)
                # findText return -1 when we can not find the text inside the
                # QComboBox
                if idx == -1:
                    logger.error("Can not change value to %r. "
                                 "Not an option in PyDMComboBox",
                                 new_val)
                    return
            # Handle bool, float, and ndarray
            else:
                logger.error("Invalid type for PyDMComboBox %s",
                             type(new_val))
                return
            # Set the index
            self.setCurrentIndex(idx)

    @Slot(int)
    def internal_combo_box_activated_int(self, index):
        """
        PyQT Slot for when the user chooses an item in the combobox.
        This slot triggers the ```send_value_signal```.
        Parameters
        ----------
        index : int

        """
        self.send_value_signal.emit(index)
