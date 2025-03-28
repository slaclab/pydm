from pydm.application import PyDMApplication
from pydm.display import Display
from pydm.data_plugins import set_read_only
from pydm.widgets import PyDMChannel

try:
    from pydm._version import version as __version__
except ImportError:
    __version__ = "unknown"


__all__ = [
    "PyDMApplication",
    "Display",
    "set_read_only",
    "PyDMChannel",
]
