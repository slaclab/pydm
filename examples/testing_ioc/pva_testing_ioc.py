from p4p.client.thread import Context, Disconnected
from p4p.nt import NTScalar
from p4p.server import Server, ServerOperation
from p4p.server.thread import SharedPV
from p4p.wrapper import Value
import random
import threading
import time
from collections import OrderedDict


class Handler(object):

    def put(self, pv, op: ServerOperation):
        """
        Called each time a client issues a Put
        operation on this Channel.

        :param SharedPV pv: The :py:class:`SharedPV` which this Handler is associated with.
        :param ServerOperation op: The operation being initiated.
        """
        pv.post(op.value(), timestamp=time.time())  # Note p4p > 4.0 only
        op.done()


class PVServer(object):

    def __init__(self):
        self.create_pvs()
        self.ctxt = Context('pva', nt=False)
        self.event = threading.Event()
        self.sim_thread = threading.Thread(target=self.run_simulation)
        self.sim_thread.setDaemon(True)
        self.sim_thread.start()
        print('Creating PV server')
        self.server_thread = threading.Thread(target=self.run_server)
        self.server_thread.setDaemon(True)
        self.server_thread.start()
        #Server.forever(providers=[{'PyDM:TEST:MeanValue': self.mean_value, }])  # runs until KeyboardInterrupt

    def create_pvs(self):
        handler = Handler()
        self.mean_value = SharedPV(handler=handler, nt=NTScalar('d', display=True, control=True, valueAlarm=True), initial=0.0)

    def run_server(self):
        Server.forever(providers=[{'PyDM:TEST:MeanValue': self.mean_value, }])  # runs until KeyboardInterrupt

    def run_simulation(self):
        while True:
            self.event.wait(1)
            self.ctxt.put('PyDM:TEST:MeanValue', random.randint(1, 10))


class PVClient(object):

    def __init__(self):
        self.cli_ctxt = Context('pva', nt=False)

    def monitor_pvs(self):
        self.monitor = self.cli_ctxt.monitor(name='jesseb:temperature', cb=self.send_new_value, notify_disconnect=True)

    def send_new_value(self, value: Value):
        if isinstance(value, Disconnected):
            print('Disconnected')
            return
        print(value)
        print(value.value)
        print(value.alarm.severity)
        print('\n\n\n\n\n')
        print(value.todict(None, OrderedDict))
        print('\n\n\n\n\n')
        print(value.asSet())
        print(value.changed('value'))
        print(value.changed('alarm'))
        print(value.changed('alarm.severity'))
        print(value.changedSet(expand=False, parents=False))


if __name__ == '__main__':
    try:
        print('Starting testing-ioc')
        #server = PVServer()
        client = PVClient()
        client.monitor_pvs()
        while True:
            pass
    except KeyboardInterrupt:
        print('\nInterrupted... finishing testing-ioc')
