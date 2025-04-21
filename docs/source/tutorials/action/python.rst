.. _PurePython:

Making Pure Python Displays
===========================

.. important::

    * Make sure the PCASpy tutorial server is :ref:`running <Setup>`

As we saw in the :ref:`A Word About Python Display <Python>` section, it is
possible to make displays using Python code and a .ui file from Qt Designer.
It is also possible to make displays without using the Qt Designer at all,
and write the user interface entirely in code.

To demonstrate this capability we will describe the steps to create the "All Motors"
screen described at the :ref:`Components Section <App Components>`.

This screen will have a ``QLineEdit`` and a ``QPushButton`` that will invoke a
method to filter our list of motors and present a list of
``PyDMEmbeddedDisplays`` in the frame below pointing to the 
``inline_motor.ui`` file that was created in the 
:ref:`Inline Motor Screen <Inline>` section of this tutorial.

Here is how it will look once we are done:

.. figure:: /_static/tutorials/action/python/all_motors.png
   :scale: 75 %
   :align: center
   :alt: All Motors Screen

.. important::

   In order to simplify this tutorial, instead of using a database or other type
   of service, the data to populate the list of motors will come from a simple text file
   named ``motor_db.txt`` that can be downloaded :download:`here </_static/tutorials/code/motor_db.txt>`.

* **Step 1.**

   The first thing that we will do is add the imports needed for the code that
   will follow.

   .. code-block:: python

      import os
      import json
      from qtpy import QtCore
      from pydm import Display
      from qtpy.QtWidgets import (QVBoxLayout, QHBoxLayout, QGroupBox,
          QLabel, QLineEdit, QPushButton, QScrollArea, QFrame,
          QApplication, QWidget)

      from pydm.widgets import PyDMEmbeddedDisplay
      from pydm.utilities import connection


* **Step 2.**

  Let's create our Python Class that will inherit from ``Display`` (See :ref:`Display`).

  .. code-block:: python

     class AllMotorsDisplay(Display):
         def __init__(self, parent=None, args=[], macros=None):
             super().__init__(parent=parent, args=args, macros=None)
             # Placeholder for data to filter
             self.data = []
             # Reference to the PyDMApplication
             self.app = QApplication.instance()
             # Load data from file
             self.load_data()
             # Assemble the Widgets
             self.setup_ui()

         def minimumSizeHint(self):
             # This is the default recommended size
             # for this screen
             return QtCore.QSize(750, 120)

         def ui_filepath(self):
             # No UI file is being used
             return None

  Breaking it down into pieces:

  #. The constructor of the class will call the ``load_data`` method that is
     responsible for opening our database and adding the information to our
     placeholder, ``self.data``, for later filtering, as well as the ``setup_ui``
     method in which the widgets be constructed and configured.
  #. ``minimumSizeHint`` returns the suggested minimum dimensions for the display.
  #. ``ui_filepath`` will return ``None``, as no ``ui`` file is being used in this
     case.

  * **Step 2.1.**

    Add the code to the ``load_data`` method.

    .. note::

       Look at the comments over the lines for explanation on what they do.

    .. code-block:: python

       def load_data(self):
           # Extract the directory of this file...
           base_dir = os.path.dirname(os.path.realpath(__file__))
           # Concatenate the directory with the file name...
           data_file = os.path.join(base_dir, "motor_db.txt")
           # Open the file so we can read the data...
           with open(data_file, 'r') as f:
               # For each line in the file...
               for entry in f.readlines():
                   # Append to the list of data...
                   self.data.append(entry[:-1])

  * **Step 2.2.**

    Add the code to the ``setup_ui`` method.

    .. note::

       Look at the comments over the lines for explanation on what they do.

    .. code-block:: python

       def setup_ui(self):
           # Create the main layout
           main_layout = QVBoxLayout()
           self.setLayout(main_layout)

           # Create a Label to be the title
           lbl_title = QLabel("Motors Diagnostic")
           # Add some StyleSheet to it
           lbl_title.setStyleSheet("\
               QLabel {\
                   qproperty-alignment: AlignCenter;\
                   border: 1px solid #FF17365D;\
                   border-top-left-radius: 15px;\
                   border-top-right-radius: 15px;\
                   background-color: #FF17365D;\
                   padding: 5px 0px;\
                   color: rgb(255, 255, 255);\
                   max-height: 25px;\
                   font-size: 14px;\
               }")

           # Add the title label to the main layout
           main_layout.addWidget(lbl_title)

           # Create the Search Panel layout
           search_layout = QHBoxLayout()

           # Create a GroupBox with "Filtering" as Title
           gb_search = QGroupBox(parent=self)
           gb_search.setTitle("Filtering")
           gb_search.setLayout(search_layout)

           # Create a label, line edit and button for filtering
           lbl_search = QLabel(text="Filter: ")
           self.txt_filter = QLineEdit()
           self.txt_filter.returnPressed.connect(self.do_search)
           btn_search = QPushButton()
           btn_search.setText("Search")
           btn_search.clicked.connect(self.do_search)

           # Add the created widgets to the layout
           search_layout.addWidget(lbl_search)
           search_layout.addWidget(self.txt_filter)
           search_layout.addWidget(btn_search)

           # Add the Groupbox to the main layout
           main_layout.addWidget(gb_search)

           # Create the Results Layout
           self.results_layout = QVBoxLayout()
           self.results_layout.setContentsMargins(0, 0, 0, 0)

           # Create a Frame to host the results of search
           self.frm_result = QFrame(parent=self)
           self.frm_result.setLayout(self.results_layout)

           # Create a ScrollArea so we can properly handle
           # many entries
           scroll_area = QScrollArea(parent=self)
           scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
           scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
           scroll_area.setWidgetResizable(True)

           # Add the Frame to the scroll area
           scroll_area.setWidget(self.frm_result)

           # Add the scroll area to the main layout
           main_layout.addWidget(scroll_area)

  * **Step 2.3.**

    Add the code to connect the ``QPushButton`` click and perform the search
    on our data.

    .. note::

       Look at the comments over the lines for explanation on what they do.

    .. code-block:: python

       def do_search(self):
           # For each widget inside the results frame, lets destroy them
           for widget in self.frm_result.findChildren(QWidget):
               widget.setParent(None)
               widget.deleteLater()

           # Grab the filter text
           filter_text = self.txt_filter.text()

           # For every entry in the dataset...
           for entry in self.data:
               # Check if they match our filter
               if filter_text.upper() not in entry.upper():
                   continue
               # Create a PyDMEmbeddedDisplay for this entry
               disp = PyDMEmbeddedDisplay(parent=self)
               disp.macros = json.dumps({"MOTOR":entry})
               disp.filename = 'inline_motor.ui'
               disp.setMinimumWidth(700)
               disp.setMinimumHeight(40)
               disp.setMaximumHeight(100)
               # Add the Embedded Display to the Results Layout
               self.results_layout.addWidget(disp)


    .. important::

       Since `PyDM v1.6.0 <https://github.com/slaclab/pydm/releases/tag/v1.6.0>`_ it is no longer required to call ``pydm.utilities.connection.establish_widget_connections``
       and ``pydm.utilities.connection.close_widget_connections``.

* **Step 3.**

  Save this file as ``all_motors.py``.

  .. warning::
     For this tutorial it is important to use this file name as it will be referenced
     at the other sections. If you change it please remember to also change at the
     other steps when referenced.

* **Step 4.**

  Test the All Motors Screen:

  .. code-block:: bash

     pydm all_motors.py

  .. figure:: /_static/tutorials/action/python/all_motors.gif
     :scale: 75 %
     :align: center

.. note::
    You can download this file using :download:`this link </_static/tutorials/code/all_motors.py>`.