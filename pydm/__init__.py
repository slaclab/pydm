from .application import PyDMApplication
from .display_module import Display
from .data_plugins import set_read_only
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
