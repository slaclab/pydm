"""
This is an example of a simple client that sends RPCs.
To demo, first run 'python examples/testing_ioc/rpc_testing_ioc.py'
from another terminal,
then run this file with 'python rpc_testing_client.py'
"""

from p4p.client.thread import Context
from p4p.nt import NTURI

ctx = Context("pva")

# NTURI() lets us wrap argument into Value type needed in rpc call
# https://mdavidsaver.github.io/p4p/nt.html#p4p.nt.NTURI
AidaBPMSURI = NTURI([("a", "i"), ("b", "i")])

request = AidaBPMSURI.wrap("pv:call:add_two_ints", scheme="pva", kws={"a": 7, "b": 3})
response = ctx.rpc("pv:call:add_two_ints", request, timeout=10)

print(response)  # should print something like 'Wed Dec 31 16:00:00 1969 10'
