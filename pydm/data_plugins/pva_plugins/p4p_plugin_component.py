import logging
from collections import OrderedDict

from p4p.client.thread import Context, Disconnected
from qtpy.QtCore import Slot

from pydm.utilities.channel import parse_channel_config

from pydm.data_store import DataKeys
from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection

from .pva_helper import pre_process, nt_introspection

logger = logging.getLogger(__name__)


class PVAContext(object):
    """
    Singleton class responsible for holding the pva context.
    """
    __instance = None

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        self.context = Context('pva', maxsize=2, unwrap=False)

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(PVAContext)
            cls.__instance.__initialized = False
        return cls.__instance


class Connection(PyDMConnection):

    def __init__(self, channel, address, protocol=None, parent=None):
        super(Connection, self).__init__(channel, address, protocol, parent)
        conn = parse_channel_config(address, force_dict=True)
        address = conn.get('parameters', {}).get('address')
        self.nt_id = None
        self.monitor = PVAContext().context.monitor(name=address,
                                                    cb=self.send_new_value,
                                                    notify_disconnect=True)
        self._introspection_set = False

    def send_new_value(self, payload):
        if isinstance(payload, Disconnected):
            self.data = {'CONNECTION': False}
        else:
            self.data = payload.todict(None, OrderedDict)
            if self.nt_id != payload.getID():
                self.nt_id = payload.getID()
                intro_keys = nt_introspection.get(self.nt_id, None)
                if intro_keys is not None:
                    self.introspection = DataKeys.generate_introspection_for(
                        **intro_keys
                    )
            pre_process(self.data, payload.getID())
            self.data['CONNECTION'] = True
            self.data['WRITE_ACCESS'] = True
        self.send_to_channel()

    @Slot(dict)
    def receive_from_channel(self, payload):
        try:
            PVAContext().context.put(self.monitor.name, payload)
        except Exception as e:
            logger.exception("Unable to put %s to %s.  Exception: %s",
                             payload, self.monitor.name, str(e))

    def close(self):
        self.monitor.close()
        super(Connection, self).close()


class P4PPlugin(PyDMPlugin):
    # NOTE: protocol is intentionally "None" to keep this plugin from getting directly imported.
    # If this plugin is chosen as the One True PVA Plugin in pva_plugin.py, the protocol will
    # be properly set before it is used.
    protocol = None
    connection_class = Connection
