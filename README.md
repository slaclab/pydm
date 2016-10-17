# pydm: Python Display Manager
pydm is a PyQt-based framework for building user interfaces for control systems.  The goal is to provide a no-code, drag-and-drop system to make simple screens, as well as a straightforward python framework to build complex applications.

# Prerequisites
* Python 2.7 or 3.5
* Qt 4.8 or higher
* PyQt 4.11 or higher or PyQt 5.3 or higher
If you'd like to use Qt Designer (drag-and-drop tool to build interfaces) you'll need to make sure you have the PyQt plugin for Designer installed.  This usually happens automatically when you install PyQt.
* Last version of pyqtgraph from github (https://github.com/pyqtgraph/pyqtgraph): extract the subfolder pyqtgraph on pydm folder

# Running the Examples
There are various examples of some of the features of the display manager.
To launch a particular display run 'python pydm.py <filename>'.

There is a 'home' display in the examples directory with buttons to launch all the examples:
run 'python pydm.py examples/home.ui'

There isn't any documentation yet, hopefully looking at the examples can get you started.

#Widget Designer Plugins
pydm widgets are written in Python, and are loaded into Qt Designer via the PyQt Designer Plugin.
If you want to use the pydm widgets in Qt Designer, add the pydm/widgets/ directory to your PYQTDESIGNERPATH environment variable.  Eventually, this will happen automatically in some kind of setup script.
