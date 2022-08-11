# PyEpics and PSP/pyca do not support EPICS V7/pva protocol.
# So use caproto which supports ca and pva.
# To force a particular library, set the PYDM_EPICS_LIB environment variable.
import os
EPICS_LIB = os.getenv("PYDM_EPICS_LIB", "").upper()
if EPICS_LIB == "CAPROTO":
    from pydm.data_plugins.epics_plugins.caproto_plugin_component import CaprotoPlugin
    EPICSPlugin = CaprotoPlugin
else:
    from pydm.data_plugins.epics_plugins.caproto_plugin_component import CaprotoPlugin
    EPICSPlugin = CaprotoPlugin

EPICSPlugin.protocol = "pva"
