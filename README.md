# pydm: Python Display Manager
pydm is a PyQt-based framework for building user interfaces for control systems.  The goal is to provide a no-code, drag-and-drop system to make simple screens, as well as a straightforward python framework to build complex applications.

# Prerequisites
* Python 2.7 or 3.5
* Qt 4.8 or higher
* PyQt4 >=4.11 or PyQt5 >= 5.7
If you'd like to use Qt Designer (drag-and-drop tool to build interfaces) you'll need to make sure you have the PyQt plugin for Designer installed.  This usually happens automatically when you install PyQt from source, but if you install it from a package manager, it may be left out.

Python package requirements are listed in the requirements.txt file, which can be used to install all requirements from pip: 'pip install -r requirements.txt'

# PyQt4 and PyQt5
PyDM can use either version of PyQt.  By default, it will first try to use PyQt4, and if that fails to import, it will try to use PyQt5.  If you'd like to force PyDM to use one or the other, you can set an environment variable named PYDM_QT_LIB to either 'PyQt4' or 'PyQt5'.  If you force a particular PyQt version, you will also have to force pyqtgraph to use the same version as PyDM, which you can do with its own environment variable: PYQTGRAPH_QT_LIB.

# Running the Examples
There are various examples of some of the features of the display manager.
To launch a particular display run 'python pydm.py <filename>'.

There is a 'home' display in the examples directory with buttons to launch all the examples:
run 'python pydm.py examples/home.ui'

There isn't any documentation yet, hopefully looking at the examples can get you started.

#Widget Designer Plugins
pydm widgets are written in Python, and are loaded into Qt Designer via the PyQt Designer Plugin.
If you want to use the pydm widgets in Qt Designer, add the pydm directory (which holds designer_plugin.py) to your PYQTDESIGNERPATH environment variable.  Eventually, this will happen automatically in some kind of setup script.