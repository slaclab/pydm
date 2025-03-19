.. _Install:

=========================
Installation
=========================

There are a few different ways to install PyDM.  The easiest way to install it
from scratch is probably using the Conda system. We recommended using Conda from `Miniforge <https://conda-forge.org/download/>`. If you have an existing
python environment, and want to install PyDM for use with that, you can do that
with pip.

Please note, this guide is written with Unix in mind, so there are probably some differences when installing on Windows.

Installing PyDM and Prerequisites with Conda
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. warning::
    There is currently no PyQt 5.15+ build available on conda or PyPI that has
    designer support for python plugins. PyDM widgets will not load in these designer versions.

    In order to use PyDM widgets in designer, please make sure to pin the PyQt version to 5.12.3 or lower
    until this is resolved.

    $ conda create -n pydm-environment python=3.10 pyqt=5.12.3 pip numpy scipy six psutil pyqtgraph pydm -c conda-forge

After installing Miniforge (see https://conda-forge.org/download/), create a new
environment for PyDM::
  
  $ conda create -n pydm-environment python=3.10 pyqt=5 pip numpy scipy six psutil pyqtgraph pydm -c conda-forge
  $ source activate pydm-environment

Once you've installed and activated the environment, you should be able to run 'pydm' to launch PyDM, or run 'designer' to launch Qt Designer.  If you are on Windows, run these commands from the Anaconda Prompt.

On MacOS, launching Qt Designer is a little more annoying:
First, use 'which pydm' to figure out where the conda environment's 'bin' directory is::

  $ which pydm
  <your anaconda directory>/base/envs/pydm-environment/bin/pydm

Now, you can use 'open' to open Designer.app::

  $ open <your anaconda directory>/base/envs/pydm-environment/bin/Designer.app


.. note::
  Depending on the version of your MacOS, launching designer (or many other Qt apps) may not work initially.
  If the designer process seems stuck and will not open, run the following command which should fix it, and then relaunch designer:

    $ export QT_MAC_WANTS_LAYER=1

Installing Manually, Without Anaconda
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This alternate installation method is only recommended for large 'site' installations that want to avoid using Anaconda.

Qt 5
++++
First, `download the source code for your platform <https://www1.qt.io/download-open-source/#section-5>`_.
Once you've downloaded and extracted the archive somewhere, its time to configure the build.
To see all the options, run::

  $ ./configure --help

Then, once you are ready::

  $ ./configure <your options here>
  $ make -j4 && make install

SIP
+++
You'll need SIP to build PyQt5.  `Download it <https://www.riverbankcomputing.com/software/sip/download>`_,
and extract the archive.  Then, follow `the instructions <http://pyqt.sourceforge.net/Docs/sip4/installation.html>`_
to build and install SIP.

PyQt5
+++++
`Download the source code for PyQt5 <https://riverbankcomputing.com/software/pyqt/download5>`_,
and extract the archive.  Follow `the provided instructions <http://pyqt.sourceforge.net/Docs/PyQt5/installation.html#building-and-installing-from-source>`_ to
build and install it.  Note that you may need to manually set the '--qmake' option to point to the
qmake binary you created when you built Qt5.

Installing PyDM with PIP
++++++++++++++++++++++++

PyDM is part of the Python Package Index (PyPI), so you can install it with pip:

  $ pip install pydm
  
This will download and install all the necessary python dependencies, then will install 
PyDM.  (You'll still need the Qt and PyQt install from above).

Setting Environment Variables
+++++++++++++++++++++++++++++

PyDM has several environment variables that let you configure its behavior, and
where it looks for certain types of files.  To ensure these variables are always
set, you probably want to add them to your shell startup file (like ~/.bashrc, if you
are using bash).

Designer Plugin Path
####################

If you want to use Designer to build displays with PyDM widgets, you'll need to
add the PyDM install location to the PYQTDESIGNERPATH environment variable.  This
directory might be buried pretty deep, depending on how Python is installed on your
system.  For example, mine lives at '/usr/local/lib/python2.7/site-packages/pydm/'.

Default Data Source
###################

PyDM lets you get data from multiple data sources.  To accomplish this, all
addresses are prefixed by a 'scheme', much like a URL.  For example, the
EPICS plugin that comes with PyDM registers the scheme 'ca', and to specify
an address to a PV, you'd write 'ca://PVNAME'.  Many sites use one data 
source primarily, and if you'd like to avoid always writing out the same scheme,
you can set the PYDM_DEFAULT_PROTOCOL environment variable.  For example,
to use the EPICS plugin by default, set PYDM_DEFAULT_PROTOCOL to 'ca'.  Now
you can use 'PVNAME' as an address without specifying that you want to use
channel access.

Troubleshooting PyDM Widgets in Designer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For Qt Designer to see the PyDM widgets, the PyQt Designer Plugin needs to be
installed.  This is usually done as part of the PyQt install process, but some
package managers (like homebrew on OSX) don't install the plugin when PyQt is
installed.  In that case, you'll probably need to install PyQt from source.
Follow the directions from the PyQt documentation: http://pyqt.sourceforge.net/Docs/PyQt5/installation.html#building-and-installing-from-source

