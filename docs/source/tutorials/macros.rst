==================
Macro Substitution
==================

PyDM has support for macro substitution, which is a way to make a .ui template for a display, and fill in variables in the template when the display is opened.

The macro system is also a good way to supply data to python-based displays when launching them from the command line, related display button, or as an embedded display.

Inserting Macro Variables
-------------------------
Anywhere in a .ui file, you can insert a macro of the following form: ${variable}.  Note that Qt Designer will only let you use macros in string properties, but you can insert macros anywhere in a .ui file using a text editor.


Replacing Macro Variables at Launch Time
----------------------------------------
When launching a .ui file which contains macro variables, specify values for each variable using the '-m' flag on the command line.
Use either JSON or plain syntax, such as one of these examples::

  python pydm.py -m '{"variable": "value"}' my_file.ui
  python pydm.py -m variable=value,variable2=value2 my_file.ui
  python pydm.py -m "variable = value, variable2=value2" my_file.ui
  
Note that if you use the JSON syntax, you can define a macro variable with a numeric value by leaving the quotes off, i.e.::
  python pydm.py -m '{"number": 5}' my_file.ui
If you use the plain syntax, all values will be interpreted as strings.

Macros in Python-based Displays
-------------------------------
If you open a python file and specify macros (via the command line, related display button, or embedded display widget), the macros will be passed as a dictionary to the Display class initializer, where they can be accessed and used to generate the display.  In addition, if the Display class specifies a .ui file to generate its user interface, macro substitution will occur inside the .ui file.  When handling macro variables in your Display class, a good practice is to assume all variables will be string values, and convert to numeric values as necessary.

Macro Behavior at Run Time
--------------------------
PyDM will remember the macros used to launch a display, and re-use them when navigating with the forward, back, and home buttons. When a new display is opened, any macros defined on the current window are also passed to the new display.  This lets you cascade macros to child displays.
