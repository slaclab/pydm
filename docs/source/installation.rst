=========================
Installation
=========================

There are a few different ways to install PyDM.  The easiest way to install it
from scratch is probably using the Anaconda system.  If you have an existing
python environment, and want to install PyDM for use with that, you can do that
with pip.

Please note, this guide is written with Unix in mind.

Installing PyDM and Prerequisites with Anaconda
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After installing Anaconda (see https://www.anaconda.com/download/), create a new
environment for PyDM::
  
  $ conda create -n pydm-environment python=3.6 pyqt=5 pip numpy scipy six psutil pyqtgraph -c conda-forge
  $ source activate pydm-environment
  
Once the environment is setup, continue on with the instructions in the `Installing PyDM
with PIP`_ section below.  You do not need to build the prerequisites manually.

Installing the Prerequisites
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^

PyDM is not currently part of the Python Package Index (PyPI), so you'll have to
first `download a release of PyDM <https://github.com/slaclab/pydm/releases/>`_,
or clone PyDM's git repository::

  $ git clone https://github.com/slaclab/pydm.git
  
After you download PyDM, enter the directory where you saved it, and run::

  $ pip install .[all]
  
This will download and install all the necessary dependencies, then will install 
PyDM.

Setting Environment Variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

PyDM has several environment variables that let you configure its behavior, and
where it looks for certain types of files.  To ensure these variables are always
set, you probably want to add them to your shell startup file (like ~/.bashrc, if you
are using bash).

Designer Plugin Path
++++++++++++++++++++

If you want to use Designer to build displays with PyDM widgets, you'll need to
add the PyDM install location to the PYQTDESIGNERPATH environment variable.  This
directory might be buried pretty deep, depending on how Python is installed on your
system.  For example, mine lives at '/usr/local/lib/python2.7/site-packages/pydm/'.

Default Data Source
+++++++++++++++++++

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

