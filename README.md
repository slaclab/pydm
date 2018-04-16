[![Build Status](https://travis-ci.org/slaclab/pydm.svg?branch=master)](https://travis-ci.org/slaclab/pydm) [![Build Status](https://ci.appveyor.com/api/projects/status/github/slaclab/pydm)]()  [![Code Health](https://landscape.io/github/slaclab/pydm/master/landscape.svg?style=flat)](https://landscape.io/github/slaclab/pydm/master) [![codecov](https://codecov.io/gh/slaclab/pydm/branch/master/graph/badge.svg)](https://codecov.io/gh/slaclab/pydm)

# pydm: Python Display Manager
pydm is a PyQt-based framework for building user interfaces for control systems.  The goal is to provide a no-code, drag-and-drop system to make simple screens, as well as a straightforward python framework to build complex applications.

# Prerequisites
* Python 2.7 or 3.5
* Qt 5.7 or higher
* PyQt5 >= 5.7
If you'd like to use Qt Designer (drag-and-drop tool to build interfaces) you'll need to make sure you have the PyQt plugin for Designer installed.  This usually happens automatically when you install PyQt from source, but if you install it from a package manager, it may be left out.

Python package requirements are listed in the requirements.txt file, which can be used to install all requirements from pip: 'pip install -r requirements.txt'

# PyQt4 vs PyQt5
In the early days of PyDM both Qt4 & Qt5 were supported and one could choose which version to use while running PyDM.
This is no longer true as new features were needed, many bugs were faced and most recently the poor support for multiple inheritance with Qt4 and Designer.
Based on that the support for Qt4 and PyQt4 is being dropped since Qt4.8.11 seems to be the last Qt4.x version to be released.

# Running the Examples
There are various examples of some of the features of the display manager.
To launch a particular display run 'python scripts/pydm <filename>'.

There is a 'home' display in the examples directory with buttons to launch all the examples:
run 'python scripts/pydm examples/home.ui'

Documentation is available at http://slaclab.github.io/pydm/.  Documentation is somewhat sparse right now, unfortunately.

# Widget Designer Plugins
pydm widgets are written in Python, and are loaded into Qt Designer via the PyQt Designer Plugin.
If you want to use the pydm widgets in Qt Designer, add the pydm directory (which holds designer_plugin.py) to your PYQTDESIGNERPATH environment variable.  Eventually, this will happen automatically in some kind of setup script.

# Easy Installing PyDM
## Using the source code
```sh
git clone https://github.com/slaclab/pydm.git
cd pydm
pip install .[all]
```

## Using Anaconda

When using Anaconda to install PyDM at a Linux Environment it will automatically define the PYQTDESIGNERPATH environment variable pointing to /etc/pydm which will have a file named designer_plugin.py which
will make all the PyDM widgets available to the Qt Designer.

### Most Recent Development Build
```sh
conda install -c pydm-dev -c conda-forge pydm
```
### Most Recent Tagged Build
```sh
conda install -c pydm-tag -c conda-forge pydm
```
