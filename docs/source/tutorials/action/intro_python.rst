.. _Python:

A Word About Python Displays
============================

PyDM supports making displays that are powered by Python scripts.  This is quite
powerful - you can do anything from generating a simple display at run time
(from a file or database, for example), up to building entire applications that
utilize the PyDM widget set.  In addition to this guide, you can look at some of
PyDM's bundled examples to see how a script-based display works.  In particular,
the 'image_processing' example is a good place to start.

Building Your UI In Designer
----------------------------

When you make a Python-based display, you can still use Qt Designer to lay out
your user interface.  In addition to the PyDM widget set, you may want to consider
using some of Qt's base widgets like Line Edit, Push Button, etc, if your display
will have some internal functionality that does not depend on a data source.

For example, the 'positioner' example uses normal (non-PyDM) Line Edits to take
user input, performs some math on the input, and outputs the result to PVs, which
are displayed with PyDMLabels.  If you want to dynamically generate your display
when it launches, you should still build a UI file, but it might only have an empty
container (like a Vertical Layout, or a Scroll Area), which you will fill with
widgets later in your code.

Writing The Code For Your Display
---------------------------------

Python-based displays in PyDM are mostly just PyQt widgets with a few extra features
on top.  This guide expects that you have a basic familiarity with PyQt and Qt itself.
Good resources for these topics are available online.  The Qt documentation, especially,
is very thorough, and will come in handy as you build your display.

.. _Display:

Subclassing Display
^^^^^^^^^^^^^^^^^^^

Python-based displays are just PyQt widgets, based on PyDM's 'Display' class.
Your display must subclass Display, and implement a few required methods::

  from os import path
  from pydm import Display
  class MyDisplay(Display):
    def __init__(self, parent=None, args=None, macros=None):
      super().__init__(parent=parent, args=args, macros=macros)

    def ui_filename(self):
      return 'my_display.ui'

    def ui_filepath(self):
      return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())

Lets look at this in detail::

  from os import path
  from pydm import Display

First, we import the modules we need.  You will probably want to import more of
your own modules here as well.

Next, we define our Display subclass, and its initializer::

  class MyDisplay(Display):
    def __init__(self, parent=None, args=None):
      super().__init__(parent=parent)

It is important to remember that you must always call the superclass' initializer
in your own, and pass it the 'parent' argument from your initializer.  Otherwise,
your display might get garbage collected by Python and crash.

Now we must implement two methods that tell PyDM where the .ui file for this display
lives::

  def ui_filename(self):
    return 'my_display.ui'

lets PyDM know what the .ui file to load is called, and::

  def ui_filepath(self):
    return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())

lets PyDM know where to find that file.  The implementation of ui_filepath used
here can probably be copied and pasted into your display verbatim: it just joins
the path of the display's .py file to the filename of the .ui file.  Unfortunately,
at the time of writing you must include this yourself, it cannot be done automatically
by PyDM.

PyDM will expose all the widgets from the .ui file as a variable called 'ui'
in your display class.  To access a widget in your code, call
`self.ui.widgetName`

Handling Command Line Arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Displays can accept command line arguments supplied at launch.  Your display's
initializer has a named argument called 'args'::

  def __init__(self, parent=None, args=None, macros=None):

It is recommended to use python's `argparse` module to parse your arguments.
For example, you could write a method like this in your display to do this::

  def parse_args(self, args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', dest='magnet_list', help='File containing a list of magnet names to use.')
    parsed_args, _unknown_args = parser.parse_known_args(args)
    return parsed_args

Using command line arguments can be a good way to make displays that generate
themselves dynamically: you could accept a filename argument, and read the contents
of that file to add widgets to your display.

Handling Macros
^^^^^^^^^^^^^^^
You can also use PyDM's macro system as a way to get user data into your display.
All macros passed into your display are available as a dictionary in the initializer.
In addition, macro substitution will always be performed on the .ui file for
your display.

Building Your Interface Dynamically
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A common reason to build a Python-based display is to generate your UI dynamically,
from some other source of data, like a file or database.  As mentioned in
`Handling Command Line Arguments`_, you can read in command line arguments to help
get data into your display.

Once you have a source of data, you can use PyQt to make new widgets, and add them
to your display.  For example, if you get a list of devices from somewhere, you can
make widgets for each device, and add them to a layout you defined in the .ui file::

  for device_name in device_list:
    device_label = PyDMLabel(parent=self, init_channel=device_name)
    self.ui.deviceListLayout.addWidget(device_label)

You usually want to put code like this in your display's initializer, so that it
happens when the display launches.
