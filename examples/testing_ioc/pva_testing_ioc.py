from p4p.client.thread import Context
from p4p.nt import NTEnum, NTNDArray, NTScalar, NTTable
from p4p.server import Server, ServerOperation
from p4p.server.thread import SharedPV
import numpy as np
import random
import threading


class Handler(object):
    """A handler for dealing with put requests to our test PVs"""

    def put(self, pv: SharedPV, op: ServerOperation) -> None:
        """Called each time a client issues a put operation on the channel using this handler"""
        pv.post(op.value())
        op.done()


class PVServer(object):
    """A simple server created by p4p for making some PVs to read and write test data to"""

    def __init__(self):
        self.create_pvs()
        self.context = Context("pva", nt=False)  # Disable automatic value unwrapping
        self.event = threading.Event()
        print("Creating testing server...")
        self.server_thread = threading.Thread(target=self.run_server)
        self.server_thread.start()
        self.update_thread = threading.Thread(target=self.update_pvs, daemon=True)
        self.update_thread.start()

    def create_pvs(self) -> None:
        """Create a few PVs for interacting with"""
        handler = Handler()  # A simple default handler that will just post PV updates is sufficient here
        # A scalar int value with some alarm limits set
        nt = NTScalar("i", display=True, control=True, valueAlarm=True)
        initial = nt.wrap(
            {
                "value": 5,
                "valueAlarm": {"lowAlarmLimit": 2, "lowWarningLimit": 3, "highAlarmLimit": 9, "highWarningLimit": 8},
            }
        )

        self.int_value = SharedPV(
            handler=handler, nt=NTScalar("i", display=True, control=True, valueAlarm=True), initial=initial
        )
        self.float_value = SharedPV(handler=handler, nt=NTScalar("f"), initial=0.0)
        self.bool_value = SharedPV(handler=handler, nt=NTScalar("?"), initial=False)
        self.byte_value = SharedPV(handler=handler, nt=NTScalar("b"), initial=12)
        self.short_value = SharedPV(handler=handler, nt=NTScalar("h"), initial=1)
        self.string_value = SharedPV(handler=handler, nt=NTScalar("s"), initial="PyDM!")

        self.int_array = SharedPV(handler=handler, nt=NTScalar("ai"), initial=[1, 2, 3, 4, 5])
        self.short_array = SharedPV(handler=handler, nt=NTScalar("ah"), initial=[0, 1, 1, 0, 0, 0, 1, 1])
        self.float_array = SharedPV(handler=handler, nt=NTScalar("af"), initial=[1.5, 2.5, 3.5, 4.5, 5.5])
        self.wave_form = SharedPV(handler=handler, nt=NTScalar("af"), initial=[1.0, 2.0, 3.0, 4.0])
        self.bool_array = SharedPV(handler=handler, nt=NTScalar("a?"), initial=[True, False, True, False])
        self.string_array = SharedPV(handler=handler, nt=NTScalar("as"), initial=["One", "Two", "Three"])

        # An NTNDArray that will be used to hold image data
        self.image_pv = SharedPV(handler=handler, nt=NTNDArray(), initial=np.zeros(1))

        # An NTEnum that supports read/write from PyDM widgets
        self.enum_pv = SharedPV(handler=handler, nt=NTEnum(), initial={"index": 0, "choices": ["YES", "NO", "MAYBE"]})

        # An NTTable that can be displayed via the PyDMNTTable widget
        table_structure = NTTable([("names", "s"), ("floats", "d"), ("booleans", "?")])
        table_strings = ["This", "Is", "A", "PyDM", "Table"]
        table_rows = []
        for i in range(5):
            table_rows.append({"names": table_strings[i], "floats": 0.35 * i, "booleans": i % 2 == 0})
        self.nt_table_pv = SharedPV(handler=handler, nt=table_structure, initial=table_structure.wrap(table_rows))

    def run_server(self) -> None:
        """Run the server that will provide the PVs until keyboard interrupt"""
        Server.forever(
            providers=[
                {
                    "PyDM:PVA:IntValue": self.int_value,
                    "PyDM:PVA:FloatValue": self.float_value,
                    "PyDM:PVA:BoolValue": self.bool_value,
                    "PyDM:PVA:ByteValue": self.byte_value,
                    "PyDM:PVA:ShortValue": self.short_value,
                    "PyDM:PVA:StringValue": self.string_value,
                    "PyDM:PVA:IntArray": self.int_array,
                    "PyDM:PVA:ShortArray": self.short_array,
                    "PyDM:PVA:FloatArray": self.float_array,
                    "PyDM:PVA:Waveform": self.wave_form,
                    "PyDM:PVA:BoolArray": self.bool_array,
                    "PyDM:PVA:StringArray": self.string_array,
                    "PyDM:PVA:Image": self.image_pv,
                    "PyDM:PVA:Enum": self.enum_pv,
                    "PyDM:PVA:Table": self.nt_table_pv,
                }
            ]
        )

    def gaussian_2d(self, x: float, y: float, x0: float, y0: float, xsig: float, ysig: float) -> np.ndarray:
        return np.exp(-0.5 * (((x - x0) / xsig) ** 2 + ((y - y0) / ysig) ** 2))

    def update_pvs(self) -> None:
        """Continually update the value of some PVs"""
        while True:
            self.event.wait(0.7)
            x = np.linspace(-5.0, 5.0, 512)
            y = np.linspace(-5.0, 5.0, 512)
            x0 = 0.5 * (np.random.rand() - 0.5)
            y0 = 0.5 * (np.random.rand() - 0.5)
            xsig = 0.8 - 0.2 * np.random.rand()
            ysig = 0.8 - 0.2 * np.random.rand()
            xgrid, ygrid = np.meshgrid(x, y)
            z = self.gaussian_2d(xgrid, ygrid, x0, y0, xsig, ysig)
            image_data = np.abs(256.0 * (z)).flatten(order="C").astype(np.uint8, copy=False)
            self.context.put(
                "PyDM:PVA:Image",
                {"value": image_data, "dimension": [{"size": 512, "offset": 0}, {"size": 512, "offset": 0}]},
            )
            self.context.put("PyDM:PVA:IntValue", random.randint(1, 100))
            self.context.put("PyDM:PVA:FloatValue", random.uniform(1, 100))
            self.context.put("PyDM:PVA:BoolValue", random.choice([True, False]))
            self.context.put("PyDM:PVA:FloatArray", (np.random.rand(5) * 10).tolist())


if __name__ == "__main__":
    try:
        print("Starting PVA testing ioc...")
        server = PVServer()
    except KeyboardInterrupt:
        print("\nInterrupted... finishing PVA testing ioc")
