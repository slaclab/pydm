from p4p.client.thread import Context, Disconnected
from p4p.nt import NTNDArray, NTScalar
from p4p.server import Server, ServerOperation
from p4p.server.thread import SharedPV
from p4p.wrapper import Value
import blosc
import numpy as np
import random
import threading
import time
from collections import OrderedDict


class Handler(object):

    def put(self, pv: SharedPV, op: ServerOperation):
        """ Called each time a client issues a put operation on the channel using this handler """
        pv.post(op.value())
#        pv.post(op.value(), timestamp=time.time())  # Note timestamp is valid for p4p > 4.0 only
        op.done()


class PVServer(object):
    """ A simple server created by p4p for making some PVs to read and write test data to """
    def __init__(self):
        self.create_pvs()
        self.context = Context('pva', nt=False)
        self.event = threading.Event()
        self.sim_thread = threading.Thread(target=self.update_pvs)
        self.sim_thread.setDaemon(True)
        self.sim_thread.start()
        print('Creating PV server')
        self.server_thread = threading.Thread(target=self.run_server)
        self.server_thread.setDaemon(True)
        self.server_thread.start()

    def create_pvs(self):
        """ Create a few PVs for interacting with """
        handler = Handler()  # A simple default handler that will just post is sufficient here
        nt = NTScalar("i", display=True, control=True, valueAlarm=True)
        initial = nt.wrap({'value': 5, 'valueAlarm': {'lowAlarmLimit': 2, 'lowWarningLimit': 3, 'highAlarmLimit': 9, 'highWarningLimit': 8}})

        # A simple NTScalar that holds an int
        self.mean_value = SharedPV(handler=handler, nt=NTScalar('i', display=True, control=True, valueAlarm=True), initial=initial)

        # An NTNDArray that will be used to hold image data
        self.image_pv = SharedPV(handler=handler, nt=NTNDArray(), initial=np.zeros(1))

    def run_server(self):
        """ Run the server that will serve the PVs until keyboard interrupt """
        Server.forever(providers=[{'PyDM:TEST:MeanValue': self.mean_value, 'PyDM:TEST:Image': self.image_pv }])

    def gaussian_2d(self, x, y, x0, y0, xsig, ysig):
        return np.exp(-0.5 * (((x - x0) / xsig) ** 2 + ((y - y0) / ysig) ** 2))

    def update_pvs(self):
        """ Constantly update the values of our PVs to simulate an actual environment """
        while True:
            self.event.wait(0.3)
#            self.ctxt.put('PyDM:TEST:MeanValue', random.randint(1, 100))
#            self.ctxt.put('jesseb:temperature', random.randint(0, 150))
            x = np.linspace(-5.0, 5.0, 512)
            y = np.linspace(-5.0, 5.0, 512)
            x0 = 0.5 * (np.random.rand() - 0.5)
            y0 = 0.5 * (np.random.rand() - 0.5)
            xsig = 0.8 - 0.2 * np.random.rand()
            ysig = 0.8 - 0.2 * np.random.rand()
            xgrid, ygrid = np.meshgrid(x, y)
            z = self.gaussian_2d(xgrid, ygrid, x0, y0, xsig, ysig)
            image_data = np.abs(256.0 * (z)).flatten(order='C').astype(np.uint8, copy=False)
            view = memoryview(image_data)
#            compressed_data = blosc.compress(view, typesize=8)
            self.context.put('PyDM:TEST:Image', {'value': image_data, 'dimension': [{'size': 512, 'offset': 0}, {'size': 512, 'offset': 0}]})
            self.context.put('PyDM:TEST:MeanValue', random.randint(1, 100))
#            self.context.put('PyDM:TEST:Image',
#                             {'value': image_data, 'dimension': [{'size': 512, 'offset': 0}, {'size': 512, 'offset': 0}],
#                              'codec': {'name': 'blosc', 'parameters': 1}})



class PVClient(object):

    def __init__(self):
        self.cli_ctxt = Context('pva', nt=False)

    def monitor_pvs(self):
        self.monitor = self.cli_ctxt.monitor(name='PyDM:TEST:Image', cb=self.send_new_value, notify_disconnect=True)
        self.event = threading.Event()
        #self.monitor = self.cli_ctxt.monitor(name='jesseb:temperature', cb=self.send_new_value, notify_disconnect=True)
        #self.monitor = self.cli_ctxt.monitor(name='PyDM:TEST:MeanValue', cb=self.send_new_value, notify_disconnect=True)

    def run_simulation(self):
        while True:
            self.event.wait(1.5)
            result = self.cli_ctxt.get(name='pv:face')
            data = result.value.copy()
            #print(type(data))
            #print(result.value.shape)
            data += 40
            data[data > 255] %= 255
            nt = NTNDArray()
            #self.cli_ctxt.put('pv:face', {'value': data})
            #value = nt.wrap({'value': data, 'dimension': [{'size': 1024, 'offset': 0, 'fullSize': 1024}, {'size': 768, 'offset':0, 'fullsize': 768}]})
            #self.cli_ctxt.put('pv:face', value)
            self.cli_ctxt.put('pv:face', {'value': data, 'dimension': [{'size': 1024, 'offset': 0}, {'size': 768, 'offset': 0}]})

    def send_new_value(self, value: Value):
        if isinstance(value, Disconnected):
            print('Disconnected')
            return
        print(value.changedSet())
#        print(value.dimension)
#        print(value.getID())
#        print(value)
#        print(value.dimension)
#        print(value.dimension[0].size)
        #print(value.value.shape)
#        print(value)
#        print(value.value)
#        print(f'\n TYPE IS: {type(value.value)}\n')
#        print(value.alarm.severity)
#        print('\n\n\n\n\n')
#        print(value.todict(None, OrderedDict))
#        print('\n\n\n\n\n')
#        print(value.asSet())
##        print(value.changed('value'))
 #       print(value.changed('alarm'))
 #       print(value.changed('alarm.severity'))


if __name__ == '__main__':
    try:
        print('Starting testing-ioc')
        server = PVServer()
#        client = PVClient()
#        client.monitor_pvs()
        #client.run_simulation()
        while True:
            pass
    except KeyboardInterrupt:
        print('\nInterrupted... finishing testing-ioc')
