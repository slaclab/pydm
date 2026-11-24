import logging

logger = logging.getLogger(__name__)

# PyTango is optional, the tango plugin is only available if it is installed
try:
    from pydm.data_plugins.tango_plugins.tango_plugin_component import TangoPlugin
except ImportError:
    TangoPlugin = None
    logger.debug("PyTango not available. Ignoring tango plugin.")
