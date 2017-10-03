from .application import PyDMApplication
from .display_module import Display
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
