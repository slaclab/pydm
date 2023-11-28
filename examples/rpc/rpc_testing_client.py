# code adapted p4p docs: https://mdavidsaver.github.io/p4p/rpc.html
from p4p import Type, Value
from p4p.client.thread import Context


ctxt = Context("pva")
# Example of manually constructing "Value" obj
V = Value(
    Type(
        [
            ("schema", "s"),
            ("path", "s"),
            (
                "query",
                (
                    "s",
                    None,
                    [
                        ("a", "i"),
                        ("b", "i"),
                    ],
                ),
            ),
        ]
    ),
    {
        "schema": "pva",
        "path": "pv:call:add_two_ints",
        "query": {
            "a": 1,
            "b": 1,
        },
    },
)
print(ctxt.rpc("pv:call:add_two_ints", V))


# Same result as above, but can define and use a proxy class if know ahead-of-time
# the signature of the function RPC will call.

"""
from p4p.rpc import rpcproxy, rpccall
from p4p.client.thread import Context
@rpcproxy
class MyProxy(object):
    @rpccall('%sadd_two_ints')
    def add_two_ints(a='i', b='i'):
        pass

ctxt = Context('pva')
proxy = MyProxy(context=ctxt, format='pv:call:')
print(proxy.add_two_ints(1, 1))
"""
