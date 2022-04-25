from p4p.client.thread import Context, Disconnected
from p4p.nt import NTNDArray, NTScalar
from p4p.server import Server, ServerOperation
from p4p.server.thread import SharedPV
from p4p.wrapper import Value
import numpy as np
import random
import threading


class Handler(object):

    def put(self, pv: SharedPV, op: ServerOperation):
        """ Called each time a client issues a put operation on the channel using this handler """
        pv.post(op.value())
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
        self.server_thread.start()

    def create_pvs(self):
        """ Create a few PVs for interacting with """
        handler = Handler()  # A simple default handler that will just post is sufficient here
        nt = NTScalar("i", display=True, control=True, valueAlarm=True)
        initial = nt.wrap({'value': 5, 'valueAlarm': {'lowAlarmLimit': 2, 'lowWarningLimit': 3,
                                                      'highAlarmLimit': 9, 'highWarningLimit': 8}})

        # A simple NTScalar that holds an int
        self.mean_value = SharedPV(handler=handler,
                                   nt=NTScalar('i', display=True, control=True, valueAlarm=True),
                                   initial=initial)
        # An NTNDArray that will be used to hold image data
        self.image_pv = SharedPV(handler=handler, nt=NTNDArray(), initial=np.zeros(1))

    def run_server(self):
        """ Run the server that will serve the PVs until keyboard interrupt """
        Server.forever(providers=[{'PyDM:TEST:MeanValue': self.mean_value, 'PyDM:TEST:Image': self.image_pv}])

    def gaussian_2d(self, x, y, x0, y0, xsig, ysig):
        return np.exp(-0.5 * (((x - x0) / xsig) ** 2 + ((y - y0) / ysig) ** 2))

    def update_pvs(self):
        """ Continually update the value of the PVs """
        while True:
            self.event.wait(0.3)
            x = np.linspace(-5.0, 5.0, 512)
            y = np.linspace(-5.0, 5.0, 512)
            x0 = 0.5 * (np.random.rand() - 0.5)
            y0 = 0.5 * (np.random.rand() - 0.5)
            xsig = 0.8 - 0.2 * np.random.rand()
            ysig = 0.8 - 0.2 * np.random.rand()
            xgrid, ygrid = np.meshgrid(x, y)
            z = self.gaussian_2d(xgrid, ygrid, x0, y0, xsig, ysig)
            image_data = np.abs(256.0 * (z)).flatten(order='C').astype(np.uint8, copy=False)
            self.context.put('PyDM:TEST:Image', {'value': image_data, 'dimension': [{'size': 512, 'offset': 0}, {'size': 512, 'offset': 0}]})
            self.context.put('PyDM:TEST:MeanValue', random.randint(1, 100))


if __name__ == '__main__':
    try:
        print('Starting testing-ioc')
        server = PVServer()
#        while True:
#            pass
    except KeyboardInterrupt:
        print('\nInterrupted... finishing pva_testing_ioc')
