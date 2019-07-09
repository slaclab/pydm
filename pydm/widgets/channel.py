import json
import logging
from functools import partial

from qtpy.QtCore import QObject, Signal, Slot

from .. import config as PYDM_CONFIG
from .. import data_plugins
from ..data_store import DataStore, DataKeys
from ..utilities import is_qt_designer, data_callback
from ..utilities.channel import parse_channel_config, get_plugin_repr

logger = logging.getLogger(__name__)


def clear_channel_address(channel):
    # We must remove spaces, \n, \t and other crap from
    # channel address
    if channel is None:
        return None
    return str(channel).strip()


class PyDMChannel(QObject):
    """
    QObject to hold signals and slots for a PyDM Widget interface to an
    external plugin.

    The purpose of this class is to create a templated slot and signals
    list that can be sent to an external plugin. The type of plugin is
    determined based on the identifier placed at the beginning of the
    :attr:`.address` attribute. This allows a generic  way to connect slots
    and signals to functionality within your PyDM Widget.

    Slots should be connected to functions on your created widget that perform
    actions upon changes. For instance, the :attr:`.value_slot` will be
    automatically called every time a new value is found by the plugin.
    This should probably linked to a function that updates the display to
    report the new value. Signals perform the reverse operation.
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

    callback : callable, optional
        The function or method to be invoked when data changes for this channel

    parent : QObject, optional
        The parent of this PyDMChannel. Defaults to None.
    """
    transmit = Signal([dict])

    def __init__(self, address=None, connection_slot=None, value_slot=None,
                 severity_slot=None, write_access_slot=None,
                 enum_strings_slot=None, unit_slot=None, prec_slot=None,
                 upper_ctrl_limit_slot=None, lower_ctrl_limit_slot=None,
                 value_signal=None, callback=None, parent=None):
        super(PyDMChannel, self).__init__(parent=parent)
        self._connection = ""
        self._address = None
        self._protocol = None
        self._use_introspection = True
        self._introspection = {}
        self._parameters = None
        self._monitors = set()  # Convert to list of WeakMethod in the future
        self._busy = False
        self._connected = False
        if address:
            self.address = address
        if callback:
            self.subscribe(callback)
        self.destroyed.connect(partial(self.disconnect, destroying=True))

        slots = {DataKeys.CONNECTION: connection_slot,
                 DataKeys.VALUE: value_slot,
                 DataKeys.SEVERITY: severity_slot,
                 DataKeys.WRITE_ACCESS: write_access_slot,
                 DataKeys.ENUM_STRINGS: enum_strings_slot,
                 DataKeys.UNIT: unit_slot,
                 DataKeys.PRECISION: prec_slot,
                 DataKeys.UPPER_LIMIT:  upper_ctrl_limit_slot,
                 DataKeys.LOWER_LIMIT: lower_ctrl_limit_slot}

        if any([x is not None for x in slots.values()]):
            default_cb = self._make_callback(slots)
            self.subscribe(default_cb)

        if value_signal is not None:
            value_signal.connect(self._handle_value_signal)

    @Slot()
    def notified(self):
        if self._busy:
            return
        self._busy = True
        data, intro = self.get_with_introspection()
        for mon in self._monitors:
            try:
                mon(data=data, introspection=intro)
            except Exception as ex:
                logger.exception("Error invoking callback for %r", self)
        self._busy = False

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, address):
        if address is None:
            return
        address = clear_channel_address(address)
        config = parse_channel_config(address, force_dict=True)
        self._connection = json.dumps(config.get('connection', {}))
        self._use_introspection = config.get('use_introspection', True)
        self._introspection = config.get('introspection', {})
        self._address = address

    def connected(self):
        return self._connected

    def connect(self):
        """
        Connect a PyDMChannel to the proper PyDMPlugin
        """
        if not self.address:
            return
        if is_qt_designer() and not PYDM_CONFIG.DESIGNER_ONLINE:
            return
        logger.debug("Connecting %r", self.address)
        # Connect to proper PyDMPlugin
        try:
            data_plugins.establish_connection(self)
            self._connected = True
        except Exception:
            logger.exception("Unable to make proper connection for %r", self)

    def disconnect(self, destroying=False):
        """
        Disconnect a PyDMChannel
        """
        if not self.address:
            return
        if is_qt_designer() and not PYDM_CONFIG.DESIGNER_ONLINE:
            return
        try:
            plugin = data_plugins.plugin_for_address(self.address)
            if not plugin:
                return
            plugin.remove_connection(self, destroying=destroying)
        except Exception as exc:
            logger.exception("Unable to remove connection for %r", self)
        self._connected = False

    def get_introspection(self):
        if self._use_introspection:
            return DataStore.introspect(self._connection)
        return self._introspection

    def get_with_introspection(self):
        data, intro = DataStore.fetch_with_introspection(self._connection)
        # In case of user-defined introspection for inner fields
        if not self._use_introspection:
            intro = self._introspection
        return data, intro

    def get(self):
        data = DataStore.fetch(self._connection)
        return data

    def put(self, data):
        self.transmit.emit(data)

    def subscribe(self, callback):
        if callable(callback):
            self._monitors.add(callback)
        else:
            logger.error('Callback for %r must be a callable.', self)

    def unsubscribe(self, callback):
        self._monitors.remove(callback)

    def clear_subscriptions(self):
        self._monitors = set()

    def _handle_value_signal(self, value):
        intro = self.get_introspection()
        key = intro.get(DataKeys.VALUE, DataKeys.VALUE)
        self.put({key: value})

    def _make_callback(self, slots):
        def cb(data=None, introspection=None, *args, **kwargs):
            if data is None or introspection is None:
                return
            data_callback(self, data, introspection, slots)

        return cb

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return (self.address == other.address
                    and self._use_introspection == other._use_introspection
                    and self._introspection == other._introspection)

        return NotImplemented

    def __ne__(self, other):
        equality_result = self.__eq__(other)
        if equality_result is not NotImplemented:
            return not equality_result
        return NotImplemented

    def __hash__(self):
        return id(self)

    def __repr__(self):
        repr = get_plugin_repr(self.address)
        return '<PyDMChannel ({:})>'.format(repr)
