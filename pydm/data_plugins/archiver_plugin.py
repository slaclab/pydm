from .plugin import PyDMPlugin, PyDMConnection
from ..PyQt.QtCore import pyqtSlot, pyqtSignal, QObject, Qt
import requests
import json
import numpy as np

class Connection(PyDMConnection):
  def __init__(self, channel, address, parent=None):
    super(Connection, self).__init__(channel, address, parent)
    self.add_listener(channel)
    url_string = "http://lcls-archapp.slac.stanford.edu/retrieval/data/getData.json?{params}".format(params=address)
    r = requests.get(url_string) #blocking.  BAD!
    if r.status_code == 200 and r.headers['content-type'] == 'application/json':
      data_dict = r.json()
      x_data = np.array([point["secs"] for point in data_dict[0]["data"]])
      y_data = np.array([point["val"] for point in data_dict[0]["data"]])
      self.new_waveform_signal.emit(y_data)
      
class ArchiverPlugin(PyDMPlugin):
  protocol = "archiver"
  connection_class = Connection