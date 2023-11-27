from p4p.rpc import rpc, quickRPCServer
from p4p.nt import NTScalar


class Summer(object):
    @rpc(NTScalar("f"))
    def add(self, lhs, rhs):  # 'lhs' and 'rhs' are arbitrary names.  The method name 'add' will be part of the PV name
        return lhs + rhs


adder = Summer()

quickRPCServer(provider="Example", prefix="pv:call:", target=adder)  # A prefix for method PV names.

"""
a = [('lhs', 'd'),('rhs', 'd')]
b = [('schema', 's'),('path', 's'),('query', ('s', None, a))]
c = {}
c['schema'] = 'pva'
c['path'] = 'pv:call:add'
d = {}
d['lhs'] = 1
d['rhs'] = 1
c['query'] = d

V = Value(Type(b), c)
print (ctxt.rpc('pv:call:add', V))
"""
