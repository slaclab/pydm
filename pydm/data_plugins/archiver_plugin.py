import requests
import numpy as np
import os

from pydm.data_store import DataKeys
from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection


class Connection(PyDMConnection):
    def __init__(self, channel, address, protocol=None, parent=None):
        super(Connection, self).__init__(channel, address, protocol, parent)

        self.data[DataKeys.CONNECTION] = False
        self.data[DataKeys.WRITE_ACCESS] = False
        self.data[DataKeys.VALUE] = None
        self.send_to_channel()

        base_url = os.getenv("PYDM_ARCHIVER_URL", "http://lcls-archapp.slac.stanford.edu")
        url_string = "{base}/retrieval/data/getData.json?{params}".format(base=base_url, params=address)
        r = requests.get(url_string)  # blocking.  BAD!
        if r.status_code == 200 and r.headers['content-type'] == 'application/json':
            self.connected = True
            self.connection_state_signal.emit(True)
            data_dict = r.json()
            # x_data not used so commented out... maybe return it with y_data?
            # x_data = np.array([point["secs"] for point in data_dict[0]["data"]])
            y_data = np.array([point["val"] for point in data_dict[0]["data"]])
            self.data[DataKeys.VALUE] = y_data
            self.send_to_channel()


class ArchiverPlugin(PyDMPlugin):
    protocol = "archiver"
    connection_class = Connection
