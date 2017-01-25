from .plugin import PyDMPlugin, PyDMConnection
from ..PyQt.QtCore import pyqtSlot, pyqtSignal, QObject, Qt
import requests
import json
import numpy as np
import time
class Connection(PyDMConnection):
    protocol = "archiver://"
    def __init__(self, channel_name, parent=None):
        super(Connection, self).__init__(channel_name, parent)
        url_string = "http://lcls-archapp.slac.stanford.edu/retrieval/data/getData.json?{params}".format(params=self.address)
        r = requests.get(url_string) #blocking.  BAD!
        if r.status_code == 200 and r.headers['content-type'] == 'application/json':
            data_dict = r.json()
            x_data = np.array([point["secs"] for point in data_dict[0]["data"]])
            y_data = np.array([point["val"] for point in data_dict[0]["data"]])
            self.data_message_signal.emit(self.new_value_message(y_data, time.time()))

class ArchiverPlugin(PyDMPlugin):
    protocol = "archiver://"
    connection_class = Connection