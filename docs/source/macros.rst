==================
Macro Substitution
==================

PyDM has support for macro substitution, which is a way to make a template for a display, and fill in variables in the template when the display is opened.

Macro substitution is a useful tool, but PyDM also provides other ways to make dynamically populated displays, like python scripting, which are more powerful.

Inserting Macro Variables
-------------------------
Anywhere in a .ui file, you can insert a macro of the following form: ${variable}.  Note that Qt Designer will only let you use macros in string properties, but you can insert macros anywhere in a .ui file using a text editor.

Replacing Macro Variables at Launch Time
----------------------------------------
When launching a .ui file which contains macro variables, specify values for each variable using the '-m' flag on the command line::

  python pydm.py -m '{"variable": "value"}' my_file.ui
  
Macro Behavior at Run Time
--------------------------
PyDM will remember the macros used to launch a display, and re-use them when navigating with the forward, back, and home buttons.