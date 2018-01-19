# pydm-examples: Python Display Manager Examples
[PyDM](https://github.com/slaclab/pydm) is a PyQt-based framework for building user interfaces for control systems.  The goal is to provide a no-code, drag-and-drop system to make simple screens, as well as a straightforward python framework to build complex applications.

# Prerequisites for the examples
* Python 2.7 or 3.5
* pydm
* Qt 5.7 or higher
* PyQt5 >= 5.7
* pcaspy (Optional)
pcaspy is needed for the `pydm-testing-ioc` used in most of the examples.

# Running the Examples
There are various examples of some of the features of the display manager.
To launch a particular display run 'pydm <filename>'.

There is a 'home' display in the examples directory with buttons to launch all the examples:
run 'pydm home.ui'

Documentation for the examples is yet to come.
Documentation for PyDM is available at http://slaclab.github.io/pydm/.  Documentation is somewhat sparse right now, unfortunately.

# Starting the testing IOC
The testing IOC provides EPICS PVs for use on most of the examples here provided.
As of now the PVs are generated using [pcaspy](https://pcaspy.readthedocs.io/en/latest/), for instructions on how to install this package please refer 
to the package [documentation](https://pcaspy.readthedocs.io/en/latest/installation.html)

After having the dependency installed run the command:

```sh
./testing_ioc/pydm-testing-ioc
```
