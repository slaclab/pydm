# code adapted from p4p docs: https://mdavidsaver.github.io/p4p/rpc.html
from p4p.rpc import rpc, quickRPCServer
from p4p.nt import NTScalar


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


adder = Demo()
quickRPCServer(provider="Example", prefix="pv:call:", target=adder)
