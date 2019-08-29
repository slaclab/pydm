import logging
import os

logger = logging.getLogger(__name__)

PVA_LIB = os.getenv("PYDM_PVA_LIB", "").upper()

try:
    if PVA_LIB == "P4P" or not PVA_LIB:
        from pydm.data_plugins.pva_plugins.p4p_plugin_component import \
            P4PPlugin

        PVAPlugin = P4PPlugin
    elif PVA_LIB == "PVAPY":
        logger.error("PVAPY is not currently supported by PyDM")
        PVAPlugin = None
except ImportError:
    PVAPlugin = None
    logger.info("No PVAccess Python library available. Ignoring pva plugin.")

if PVAPlugin:
    PVAPlugin.protocol = "pva"
