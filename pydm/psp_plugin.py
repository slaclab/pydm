import numpy as np
import psp.Pv as Pv
from PyQt4.QtCore import pyqtSlot,pyqtSignal,Qbject, Qt, QString

from .plugin import PyDMPlugin,PyDMConnection


class PSPConnection(PyDMConnection):
    """
    A PSP Connection to the neccesary signals and slots to inform PyQT Widgets
    in changes in channel access values
    """

    def __init__(self,channel,pv,parent=None):
        super(PSPConnection,self).__init__(channel,pv,parent)
        #Setup PV callbacks
        self.pv      = Pv(pv,initialize=True,monitor=True)
        self.pv.add_connection_callback(self.send_connection_state)
        self.pv.add_monitor_callback(self.send_new_value)
        #Setup Unit callback
        self.unit_pv = Pv('{:}.EGU'.format(pv),initialize=True,monitor=True)
        
        self.add_listener(channel)



    def send_new_value(self,pvname=None):
    
