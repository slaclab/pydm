# source: https://mdavidsaver.github.io/p4p/rpc.html
from p4p.rpc import rpc, quickRPCServer
from p4p.nt import NTScalar
import logging


class Summer(object):
    @rpc(NTScalar("d"))
    def add(self, lhs, rhs):  # 'lhs' and 'rhs' are arbitrary names.  The method name 'add' will be part of the PV name
        return float(lhs) + float(rhs)


logging.basicConfig(level=logging.DEBUG)
adder = Summer()

quickRPCServer(provider="Example", prefix="pv:call:", target=adder)  # A prefix for method PV names.

# from terminal: pvcall pv:call:add lhs=1 rhs=1
