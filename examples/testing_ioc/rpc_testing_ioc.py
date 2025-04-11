"""
This is an example of a server that sends back RPC results, mimicking the behavior of an ioc.
The server defines three functions with differing names, number of args, and arg types.
To view demo, first run this file with 'python rpc_testing_ioc.py',
and then run 'pydm examples/rpc/rpc_lables.ui' from another terminal.
(code adapted from p4p docs: https://mdavidsaver.github.io/p4p/rpc.html)
"""

from p4p.rpc import rpc, quickRPCServer
from p4p.nt import NTScalar
import random


class Demo(object):
    @rpc(NTScalar("i"))
    def add_two_ints(self, a, b):
        return a + b

    @rpc(NTScalar("f"))
    def add_int_float(self, a, b):
        return a + b

    @rpc(NTScalar("i"))
    def add_three_ints_negate_option(self, a, b, negate):
        res = a + b
        return -1 * res if negate else res

    @rpc(NTScalar("s"))
    def take_return_string(self, a):
        return a + "!!"

    @rpc(NTScalar("f"))
    def no_args(self):
        randomFloat = random.uniform(0, 10)
        return randomFloat


adder = Demo()
quickRPCServer(provider="Example", prefix="pv:call:", target=adder)
