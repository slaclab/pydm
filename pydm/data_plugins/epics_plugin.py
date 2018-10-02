# If the user has PyEpics, use it... which is slower but more commonly used
# Otherwise, if PSP and pyca installed, use psp, which is faster.
# To force a particular library, set the PYDM_EPICS_LIB environment
# variable to either pyepics or pyca.
import os
EPICS_LIB = os.getenv("PYDM_EPICS_LIB", "").upper()
if EPICS_LIB == "PYEPICS":
    from pydm.data_plugins.epics_plugins.pyepics_plugin_component import PyEPICSPlugin
    EPICSPlugin = PyEPICSPlugin
elif EPICS_LIB == "PYCA":
    from pydm.data_plugins.epics_plugins.psp_plugin_component import PSPPlugin
    EPICSPlugin = PSPPlugin
elif EPICS_LIB == "CAPROTO":
    from pydm.data_plugins.epics_plugins.caproto_plugin_component import CaprotoPlugin
    EPICSPlugin = CaprotoPlugin
else:
    try:
        from pydm.data_plugins.epics_plugins.pyepics_plugin_component import PyEPICSPlugin
        EPICSPlugin = PyEPICSPlugin
    except ImportError:
        from pydm.data_plugins.epics_plugins.psp_plugin_component import PSPPlugin
        EPICSPlugin = PSPPlugin
EPICSPlugin.protocol = "ca"
