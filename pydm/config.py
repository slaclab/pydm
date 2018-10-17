import os

__all__ = ['DEFAULT_PROTOCOL',
           'DESIGNER_ONLINE'
           ]


DEFAULT_PROTOCOL = os.getenv("PYDM_DEFAULT_PROTOCOL")
if DEFAULT_PROTOCOL is not None:
    # Get rid of the "://" part if it exists
    DEFAULT_PROTOCOL = DEFAULT_PROTOCOL.split("://")[0]

DESIGNER_ONLINE = os.getenv("PYDM_DESIGNER_ONLINE", None) is not None
