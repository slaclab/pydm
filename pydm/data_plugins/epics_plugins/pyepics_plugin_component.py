import logging

import epics
from epics import dbr
from qtpy.QtCore import Slot

from pydm.utilities.channel import parse_channel_config

from pydm.data_plugins import is_read_only
from pydm.data_store import DataKeys
from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection

logger = logging.getLogger(__name__)


class Connection(PyDMConnection):

    def __init__(self, channel, address, protocol=None, parent=None):
        super(Connection, self).__init__(channel, address, protocol, parent)
        conn = parse_channel_config(address, force_dict=True)['connection']
        address = conn.get('parameters', {}).get('address')
        monitor_mask = dbr.DBE_VALUE | dbr.DBE_ALARM | dbr.DBE_PROPERTY
        self.pv = epics.PV(address, form='ctrl', auto_monitor=monitor_mask,
                           access_callback=self.send_access_state,
                           connection_callback=self.send_connection_state)
        self.pv.add_callback(self.send_new_value, with_ctrlvars=True)

    def send_new_value(self, value=None, **kws):
        self.update_ctrl_vars(**kws)

        if value is not None:
            self.data[DataKeys.VALUE] = value

        self.send_to_channel()

    def update_ctrl_vars(self, units=None, enum_strs=None, severity=None,
                         upper_ctrl_limit=None, lower_ctrl_limit=None,
                         precision=None, *args, **kws):
        if severity is not None:
            self.data[DataKeys.SEVERITY] = severity
        if precision is not None:
            self.data[DataKeys.PRECISION] = precision
        if enum_strs is not None:
            try:
                enum_strs = tuple(
                    b.decode(encoding='ascii') for b in enum_strs)
            except AttributeError:
                pass
            self.data[DataKeys.ENUM_STRINGS] = enum_strs
        if units is not None and len(units) > 0:
            if type(units) == bytes:
                units = units.decode()
            self.data[DataKeys.UNIT] = units
        if upper_ctrl_limit is not None:
            self.data[DataKeys.UPPER_LIMIT] = upper_ctrl_limit
        if lower_ctrl_limit is not None:
            self.data[DataKeys.LOWER_LIMIT] = lower_ctrl_limit

    def send_access_state(self, read_access, write_access, *args, **kws):
        if is_read_only():
            self.data[DataKeys.WRITE_ACCESS] = False
            return

        if write_access is not None:
            self.data[DataKeys.WRITE_ACCESS] = write_access
        self.send_to_channel()

    def reload_access_state(self):
        read_access = epics.ca.read_access(self.pv.chid)
        write_access = epics.ca.write_access(self.pv.chid)
        self.send_access_state(read_access, write_access)

    def send_connection_state(self, conn=None, *args, **kws):
        self.data[DataKeys.CONNECTION] = conn
        if conn:
            if hasattr(self, 'pv'):
                self.reload_access_state()
                self.pv.run_callbacks()
        self.send_to_channel()

    @Slot(dict)
    def receive_from_channel(self, payload):
        new_val = payload.get(DataKeys.VALUE, None)
        if new_val is None:
            logger.warning("Could not write to PV. No new value for key %s."
                           "PV: %s",
                           DataKeys.VALUE, self.pv.pvname)
            return

        if not self.pv.write_access:
            logger.warning("Could not write to PV. Write access denied for "
                           "PV: %s", self.pv.pvname)
            return

        try:
            self.pv.put(new_val)
        except Exception as e:
            logger.exception("Unable to put %s to %s.  Exception: %s",
                             new_val, self.pv.pvname, str(e))

    def close(self):
        self.pv.disconnect()
        super(Connection, self).close()


class PyEPICSPlugin(PyDMPlugin):
    # NOTE: protocol is intentionally "None" to keep this plugin from getting
    # directly imported.
    # If this plugin is chosen as the One True EPICS Plugin in epics_plugin.py,
    # the protocol will be properly set before it is used.
    protocol = None
    connection_class = Connection
