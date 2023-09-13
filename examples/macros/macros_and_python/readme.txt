This example illustrates how to write a python-based display that accepts
macro variables and uses them to change the panel with code.  In this case,
two macro variables are added together in the display's initializer.

To run the python-based display and supply the variables it needs,
launch it from the command line with the -m argument and supply two
variables, "a" and "b", like this:
python pydm.py -m '{"a": 3, "b": 5}' examples/macros/macros_and_python/macro_addition.py

Another .ui file, macros_to_python_displays.ui illustrates loading the
python-based display with a related display button, and using the button
to supply macros to the display.  This example also demonstrates how PyDM
cascades macros from one display to the next when a related display button
is clicked.

To run the .ui file, supply one macro variable, "a":
python pydm.py -m '{"a": 3}' examples/macros/macros_and_python/macros_to_python_displays.ui
