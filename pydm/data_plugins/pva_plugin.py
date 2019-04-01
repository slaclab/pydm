import os
PVA_LIB = os.getenv("PYDM_PVA_LIB", "").upper()
if PVA_LIB == "P4P":
    from pydm.data_plugins.pva_plugins.p4p_plugin_component import P4PPlugin
    PVAPlugin = P4PPlugin
elif PVA_LIB == "PVAPY":
    PVAPlugin = None
else:
    try:
        from pydm.data_plugins.pva_plugins.p4p_plugin_component import P4PPlugin
        PVAPlugin = P4PPlugin
    except ImportError:
        #from pydm.data_plugins.pva_plugins.p4p_plugin_component import P4PPlugin
        PVAPlugin = None

if PVAPlugin:
    PVAPlugin.protocol = "pva"
