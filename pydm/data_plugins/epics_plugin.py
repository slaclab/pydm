# If the user has PSP and pyca installed, use psp, which is faster.
# Otherwise, use PyEPICS, which is slower, but more commonly used.
# To force a particular library, set the PYDM_EPICS_LIB environment
# variable to either pyepics or pyca.
import os
EPICS_LIB = os.getenv("PYDM_EPICS_LIB")
if EPICS_LIB == "pyepics":
    from pydm.data_plugins.epics_plugins.pyepics_plugin_component import PyEPICSPlugin
    EPICSPlugin = PyEPICSPlugin
elif EPICS_LIB == "pyca":
    from pydm.data_plugins.epics_plugins.psp_plugin_component import PSPPlugin
    EPICSPlugin = PSPPlugin
else:
    try:
        from pydm.data_plugins.epics_plugins.psp_plugin_component import PSPPlugin
        EPICSPlugin = PSPPlugin
    except ImportError:
        from pydm.data_plugins.epics_plugins.pyepics_plugin_component import PyEPICSPlugin
        EPICSPlugin = PyEPICSPlugin
EPICSPlugin.protocol = "ca"
