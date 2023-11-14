from p4p.rpc import rpcproxy, rpccall
from p4p.client.thread import Context


@rpcproxy
class MyProxy(object):
    @rpccall("%sadd")
    def add(lhs="d", rhs="d"):
        pass


context = Context("pva")
proxy = MyProxy(context=context, format="RPCTEST:")
print("Sending RPC request to 'RPCTEST:add' function with args 4 and 6...")
print("Result: ", proxy.add(4, 6))
