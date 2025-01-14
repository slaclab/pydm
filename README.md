[![Build Status](https://github.com/slaclab/pydm/actions/workflows/run-tests.yml/badge.svg?branch=master)](https://github.com/slaclab/pydm/actions/workflows/run-tests.yml)

![PyDM: Python Display Manager](pydm_banner_full.png)

<p>
  <img src="pydm_launcher/icons/pydm_128.png" width="128" height="128" align="right"/>
  <h1>PyDM: Python Display Manager</h1>
</p>

<p align="left">
  PyDM is a PyQt-based framework for building user interfaces for control systems.
  The goal is to provide a no-code, drag-and-drop system to make simple screens,
  as well as a straightforward Python framework to build complex applications.
  <br>
  <br>
</p>
<p align="center">
  <strong>« Explore PyDM <a href="https://slaclab.github.io/pydm/">docs</a> and <a href="https://slaclab.github.io/pydm/tutorials/index.html">tutorials</a> »</strong>
  <br>
  <br>
  <a href="https://github.com/slaclab/pydm/issues/new?template=bug-report.md">Report bug</a>
  ·
  <a href="https://github.com/slaclab/pydm/issues/new?template=feature-request.md&labels=request">Request feature</a>
  ·
  <a href="https://github.com/slaclab/pydm/blob/master/CONTRIBUTING.rst">How to Contribute</a>
  ·
  <a href="https://github.com/slaclab/pydm/blob/master/SUPPORT.md">Support</a>
</p>

<br>

# Python Qt Wrapper
PyDM project uses the [qtpy](https://github.com/spyder-ide/qtpy)
as the abstraction layer for the Qt Python wrappers (PyQt5/PyQt4/PySide2/PySide).
**All tests are performed with PyQt5**.

# Prerequisites
* Python 3.9+
* Qt 5.6 or higher
* qtpy
* PyQt5 >= 5.7 or any other Qt Python wrapper.
> **Note:**
> If you'd like to use Qt Designer (drag-and-drop tool to build interfaces) you'll
> need to make sure you have the PyQt plugin for Designer installed.  This usually
> happens automatically when you install PyQt from source, but if you install it
> from a package manager, it may be left out.

Python package requirements are listed in the requirements.txt file, which can
be used to install all requirements from pip: 'pip install -r requirements.txt'

# Running the Tests
In order to run the tests you will need to install some dependencies that are
not part of the runtime dependencies of PyDM.

Assuming that you have cloned this repository do:

```bash
pip install -r dev-requirements.txt

python run_tests.py
```

If you want to see the coverage report do:
```bash
python run_tests.py --show-cov
```

# Running the Examples
There are various examples of some of the features of the display manager.
To launch a particular display run 'python scripts/pydm <filename>'.

There is a 'home' display in the examples directory with buttons to launch all
the examples:
```python
pydm examples/home.ui
```

# Building the Documentation Locally
In order to build the documentation you will need to install some dependencies
that are not part of the runtime dependencies of PyDM.

Assuming that you have cloned this repository do:

```bash
pip install -r docs-requirements.txt

cd docs
make html
```

This will generate the HTML documentation for PyDM at the `<>/docs/build/html`
folder. Look for the `index.html` file and open it with your browser.

# Online Documentation

Documentation is available at http://slaclab.github.io/pydm/.  Documentation is
somewhat sparse right now, unfortunately.

# Widget Designer Plugins
pydm widgets are written in Python, and are loaded into Qt Designer via the PyQt
Designer Plugin.
If you want to use the pydm widgets in Qt Designer, add the pydm directory
(which holds designer_plugin.py) to your PYQTDESIGNERPATH environment variable.
Eventually, this will happen automatically in some kind of setup script.

# Easy Installing PyDM
## Using the source code
```sh
git clone https://github.com/slaclab/pydm.git
cd pydm
pip install .[all]
```

## Using Anaconda

When using Anaconda to install PyDM at a Linux Environment it will automatically
define the PYQTDESIGNERPATH environment variable pointing to /etc/pydm which
will have a file named designer_plugin.py which will make all the PyDM widgets
available to the Qt Designer. For more information please see
our <a href="https://slaclab.github.io/pydm/installation.html">installation guide</a>.
