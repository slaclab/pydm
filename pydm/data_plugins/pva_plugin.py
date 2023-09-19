import logging
import os

logger = logging.getLogger(__name__)

# This file gives us flexibility in allowing multiple options for pvAccess plugins in the future if needed.
PVA_LIB = os.getenv("PYDM_PVA_LIB", "").upper()
try:
    if PVA_LIB == "P4P" or not PVA_LIB:
        from pydm.data_plugins.epics_plugins.p4p_plugin_component import P4PPlugin

        PVAPlugin = P4PPlugin
    elif PVA_LIB == "PVAPY":
        logger.error("PVAPY is not currently supported by PyDM")
        PVAPlugin = None
except ImportError:
    PVAPlugin = None
    logger.info("No PVAccess Python library available. Ignoring pva plugin.")

if PVAPlugin:
    PVAPlugin.protocol = "pva"
