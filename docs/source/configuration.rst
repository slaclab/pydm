========================
Configuration
========================

In order to make PyDM a flexible tool a couple of Environment Variables are used
for configuration and customization.

The following table describe the environment variable as well as its usage and
default values.

======================== ===================================================================
Variable                 What is it used for?
======================== ===================================================================
PYDM_DEFAULT_PROTOCOL    | The default protocol to be used when specifing channels.
                         | This option eliminates the need for users to specify the protocol
                         | for a given Data Plugin. E.g.: `ca`.
                         | **Default:** None
PYDM_DOCS_URL            | This variable point to the base URL for the documentation.
                         | **Default:** https://slaclab.github.io/pydm
PYDM_ARCHIVER_URL        | This is the base URL for the Archiver Appliance Data Plugin it is
                         | concatenated with ``/retrieval/data/getData`` to generate the
                         | retrieval URL.
                         | **Default:** http://lcls-archapp.slac.stanford.edu
PYDM_EPICS_LIB           | Which library to use for Channel Access (ca://) data
                         | plugin. PyDM offers two options: PYCA and PYEPICS.
                         | **Default:** PYEPICS
PYDM_PATH                | Path to `pydm` executable for child processes, such as new windows.
                         | It will only be used if `pydm` is not found in the standard `$PATH`.
                         | **Default:** None
PYDM_DISPLAYS_PATH       | Path in which PyDM should look for ``.ui`` and ``.py`` files when
                         | they are not found. **Note: This is not a recursive search.**
                         | **Default:** None
PYDM_DATA_PLUGINS_PATH   | Path in which PyDM should look for Data Plugins to be loaded.
                         | **Default:** None
PYDM_TOOLS_PATH          | Path in which PyDM should look for External Tools to be loaded.
                         | **Default:** None
PYDM_STRING_ENCODING     | The string encoding to be used when converting arrays to strings.
                         | **Default:** utf-8
PYDM_STYLESHEET          | Path to the QSS file defining the global stylesheet for the
                         | PyDM application. When used, it will override the default look.
                         | **Default:** None
PYDM_DESIGNER_ONLINE     | This flag enables receiving live data in Qt Designer. If disabled,
                         | channels will not be connected to in Qt Designer.
                         | **Default:** None
======================== ===================================================================
