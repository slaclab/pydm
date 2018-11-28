import logging

from pydm.data_plugins import plugin_for_address
from pydm.utilities import is_qt_designer
from pydm import config

logger = logging.getLogger(__name__)


class PyDMChannel(object):
    """
    Object to hold signals and slots for a PyDM Widget interface to an
    external plugin

    The purpose of this class is to create a templated slot and signals
    list that can be sent to an external plugin. The type of plugin is
    determined by the PyDMApplication based on the identifier placed at
    the beginning of the :attr:`.address` attribute. This allows a generic
    way to connect slots and signals to functionality within your PyDM
    Widget. Slots should be connected to functions on your created widget
    that perform actions upon changes. For instance, the :attr:`.value_slot`
    will be automatically called every time a new value is found by the
    plugin. This should probably linked to a function that updates the
    display to report the new value. Signals perform the reverse operation.
    These should be used to send new values back to the plugin to update
    the source.

    Using this structure to interface with plugins allows your created PyDM
    Widget a greater flexibility in choosing its underlying source. For
    instance, returning to the example of the :attr:`.value_slot`,
    getting a value to display from channel access or from the EPICS Archiver
    are very different operations. However, actually displaying the value
    should be identical. By simply attaching your PyDM Widget's display
    functionality to the :attr:`.value_slot` you have created a
    Widget that can do either interchangeably, all the user has to do is
    specify the correct address signature and the rest of the work is done
    by the underlying plugins.

    Parameters
    ----------
    address : str, optional
        The name of the address to be used by the plugin. This
        should usually be a user inputted field when a specific
        PyDM widget is initialized

    connection_slot : Slot, optional
        A function to be run when the connection state
        changes

    value_slot : Slot, optional
        A function to be run when the value updates

    severity_slot : Slot, optional
        A function to be run when the severity changes

    write_access_slot : Slot, optional
        A function to be run when the write access changes

    enum_strings_slot : Slot, optional
        A function to be run when the enum_strings change

    unit_slot : Slot, optional
        A function to be run when the unit changes

    prec_slot : Slot, optional
        A function to be run when the precision value changes

    value_signal : Signal, optional
        Attach a signal here that emits a desired value to be sent
        through the plugin

    """
    def __init__(self, address=None, connection_slot=None, value_slot=None,
                 severity_slot=None, write_access_slot=None,
                 enum_strings_slot=None, unit_slot=None, prec_slot=None,
                 upper_ctrl_limit_slot=None, lower_ctrl_limit_slot=None,
                 value_signal=None):
        self.address = address

        self.connection_slot = connection_slot
        self.value_slot = value_slot
        self.severity_slot = severity_slot
        self.write_access_slot = write_access_slot
        self.enum_strings_slot = enum_strings_slot
        self.unit_slot = unit_slot
        self.prec_slot = prec_slot

        self.upper_ctrl_limit_slot = upper_ctrl_limit_slot
        self.lower_ctrl_limit_slot = lower_ctrl_limit_slot

        self.value_signal = value_signal

    def connect(self):
        """
        Connect a PyDMChannel to the proper PyDMPlugin
        """
        if is_qt_designer() and not config.DESIGNER_ONLINE:
            return
        logger.debug("Connecting %r", self.address)
        # Connect to proper PyDMPlugin
        try:
            plugin = plugin_for_address(self.address)
            plugin.add_connection(self)
        except Exception:
            logger.exception("Unable to make proper connection "
                             "for %r", self)

    def disconnect(self, destroying=False):
        """
        Disconnect a PyDMChannel
        """
        if is_qt_designer() and not config.DESIGNER_ONLINE:
            return
        try:
            plugin = plugin_for_address(self.address)
            if not plugin:
                return
            plugin.remove_connection(self, destroying=destroying)
        except Exception as exc:
            logger.exception("Unable to remove connection "
                             "for %r", self)

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            address_matched = self.address == other.address
            connection_slot_matched = self.connection_slot == other.connection_slot
            value_slot_matched = self.value_slot == other.value_slot
            severity_slot_matched = self.severity_slot == other.severity_slot
            enum_strings_slot_matched = self.enum_strings_slot == other.enum_strings_slot
            unit_slot_matched = self.unit_slot == other.unit_slot
            prec_slot_matched = self.prec_slot == other.prec_slot
            upper_ctrl_slot_matched = self.upper_ctrl_limit_slot == other.upper_ctrl_limit_slot
            lower_ctrl_slot_matched = self.lower_ctrl_limit_slot == other.lower_ctrl_limit_slot
            write_access_slot_matched = self.write_access_slot == other.write_access_slot

            value_signal_matched = True
            if self.value_signal and other.value_signal:
                value_signal_matched = self.value_signal.signal == other.value_signal.signal

            return (address_matched and
                    connection_slot_matched and
                    value_slot_matched and
                    severity_slot_matched and
                    enum_strings_slot_matched and
                    unit_slot_matched and
                    prec_slot_matched and
                    upper_ctrl_slot_matched and
                    lower_ctrl_slot_matched and
                    write_access_slot_matched and
                    value_signal_matched)

        return NotImplemented

    def __ne__(self, other):
        equality_result = self.__eq__(other)
        if equality_result is not NotImplemented:
            return not equality_result
        return NotImplemented

    def __hash__(self):
        return id(self)

    def __repr__(self):
        return '<PyDMChannel ({:})>'.format(self.address)
