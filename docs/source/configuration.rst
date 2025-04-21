========================
Configuration
========================

In order to make PyDM a flexible tool, a couple of environment variables are used
for configuration and customization.

The following table describes the environment variables as well as their usage and
default values.

=============================== ==================================================================================
Variable                        What is it used for?
=============================== ==================================================================================
PYDM_DEFAULT_PROTOCOL           | The default protocol to be used when specifying channels.
                                | This option eliminates the need for users to specify the protocol
                                | for a given Data Plugin. E.g.: `ca`.
                                | **Default:** None
PYDM_DOCS_URL                   | This variable point to the base URL for the documentation.
                                | **Default:** https://slaclab.github.io/pydm
PYDM_ARCHIVER_URL               | This is the base URL for the Archiver Appliance Data Plugin it is
                                | concatenated with ``/retrieval/data/getData`` to generate the
                                | retrieval URL.
                                | **Default:** http://lcls-archapp.slac.stanford.edu
PYDM_EPICS_LIB                  | Which library to use for Channel Access (ca://) data
                                | plugin. PyDM offers two options: PYCA and PYEPICS.
                                | **Default:** PYEPICS
PYDM_PATH                       | Path to `pydm` executable for child processes, such as new windows.
                                | It will only be used if `pydm` is not found in the standard `$PATH`.
                                | **Default:** None
PYDM_DISPLAYS_PATH              | Path(s) in which PyDM should look for ``.ui``, ``.py``, and ``.adl`` files when
                                | they are not found. If more than one path is specified, separate with
                                | ``:`` on linux or ``;`` on Windows.
                                | **Note: This is not a recursive search.**
                                | **Default:** None
PYDM_DATA_PLUGINS_PATH          | Path in which PyDM should look for Data Plugins to be loaded.
                                | **Default:** None
PYDM_TOOLS_PATH                 | Path in which PyDM should look for External Tools to be loaded.
                                | **Default:** None
PYDM_HOME_FILE                  | Path to a PyDM display file to use as the home display in the navigation bar.
                                | Will be returned to when the user clicks on the home button. If not set, the
                                | first display opened will be used as the home display. If the command line option
                                | ``--homefile`` is set, that will take precedence over this environment variable.
PYDM_STRING_ENCODING            | The string encoding to be used when converting arrays to strings.
                                | **Default:** utf-8
PYDM_STYLESHEET                 | Path to the QSS files defining the global stylesheets for the
                                | PyDM application. When used, it will override the default look.
                                | If using multiple files they must be separated by the path separator.
                                | Only files are supported, not directories. On this list, like a PATH
                                | variable, the first elements will take precedence over others.
                                | E.g.: ``/path_to/my_style_1.qss:/path_to/other/my_other_style.qss``
                                | **Default:** None
PYDM_STYLESHEET_INCLUDE_DEFAULT | Whether or not to include the PyDM Default stylesheet along with customized
                                | files. Note that the PyDM default stylesheet will have lower precedence compared
                                | to files specified at ``PYDM_STYLESHEET``
                                | **Default:** False
PYDM_DESIGNER_ONLINE            | This flag enables receiving live data in Qt Designer. If disabled,
                                | channels will not be connected to in Qt Designer.
                                | **Default:** None
=============================== ==================================================================================
