from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection
import requests
import numpy as np
import os


class Connection(PyDMConnection):

    def __init__(self, channel, address, protocol=None, parent=None):
        super(Connection, self).__init__(channel, address, protocol, parent)
        self.add_listener(channel)
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
            self.new_waveform_signal.emit(y_data)


class ArchiverPlugin(PyDMPlugin):
    protocol = "archiver"
    connection_class = Connection
