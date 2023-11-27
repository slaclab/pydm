from p4p import Type, Value
from p4p.client.thread import Context

ctxt = Context("pva")
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
                        ("lhs", "d"),
                        ("rhs", "d"),
                    ],
                ),
            ),
        ]
    ),
    {
        "schema": "pva",
        "path": "pv:call:add",
        "query": {
            "lhs": 1,
            "rhs": 1,
        },
    },
)
print(ctxt.rpc("pv:call:add", V))

print(ctxt.rpc("pv:name:add", {"A": 5, "B": 6}))
