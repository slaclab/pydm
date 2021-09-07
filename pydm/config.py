import os

__all__ = ['DEFAULT_PROTOCOL',
           'DESIGNER_ONLINE',
           'STYLESHEET',
           'STYLESHEET_INCLUDE_DEFAULT',
           'CONFIRM_QUIT'
           ]


DEFAULT_PROTOCOL = os.getenv("PYDM_DEFAULT_PROTOCOL")
if DEFAULT_PROTOCOL is not None:
    # Get rid of the "://" part if it exists
    DEFAULT_PROTOCOL = DEFAULT_PROTOCOL.split("://")[0]

DESIGNER_ONLINE = os.getenv("PYDM_DESIGNER_ONLINE", None) is not None

STYLESHEET = os.getenv("PYDM_STYLESHEET", None)

STYLESHEET_INCLUDE_DEFAULT = os.getenv("PYDM_STYLESHEET_INCLUDE_DEFAULT", False)

CONFIRM_QUIT = os.getenv("PYDM_CONFIRM_QUIT", "n").lower() in ("y", "t", "1", "true")