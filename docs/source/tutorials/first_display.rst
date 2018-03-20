============================================
Building Your First Display with Qt Designer
============================================

Once you have PyDM installed, you can start making displays.  The easiest way
to make a display is to use Qt Designer, which is Qt's drag-and-drop tool for
building user interfaces.  Once you open Designer, you'll be greeted by a mostly
blank screen, with a list of widgets on the left, and a property inspector on the
right.

.. figure:: /_static/tutorials/designer.png
   :scale: 33 %
   :alt: Screenshot of newly-opened Qt Designer.

   A newly-opened Qt Designer.  Notice the PyDM widgets at the bottom of 
   the widget list on the left.
   
To make a new PyDM display, go to File->New..., then choose to build a new Widget.

.. note::
    All PyDM displays must have a Widget for the base - if you try to use MainWindow, your
    display will not work properly.
    
Now you should see a blank form on which you can drag widgets.  Drag a PyDMLabel 
(in the 'PyDM Display Widgets' section) onto the form.  On the right side of the
screen, you can see all the properties for the widget.  Most of these properties
are for the basic QLabel widget that PyDMLabel is based on, and control the label's
appearance and size (things like the font).  At the bottom of the properties list
are the PyDM-specific properties.

.. figure:: /_static/tutorials/pydm_properties.png
   :scale: 33 %
   :alt: Screenshot showing the PyDMLabel's properties.

   The PyDMLabel's properties are highlighted in red.

Lets fill in the 'channel' property for this label, which will connect it to a source
of data.  PyDM comes with a Python-based IOC which is useful for testing widgets out.
We'll use one of the PVs supplied by the testing IOC.  Set the label's 'channel' property
to 'ca://MTEST:Float'.  Once that is done, go to File->Save... and save the .ui file
somewhere.

We can test the display in PyDM by first running the testing IOC.  Open up a new
terminal and run the command::

  $ python examples/testing_ioc/pydm-testing-ioc
  
to launch the IOC.  Once the IOC is running, run the command::
  
  $ pydm <your file name>
  
with the .ui file you just saved.  This will open your display in PyDM.  If everything
works correctly, you should see a label with the text '0.000'.  This value will update
whenever the MTEST:Float PV updates.  You can test this by using 'caput' at the terminal
to change the value of MTEST:Float, and observing the label on the display.

You now know almost all you need to build simple displays!  At this point, the
best thing you can do is play around with the various widgets and their properties.
For example, try adding a slider to your display and connect it to the same PV - you
should see the label change as the slider moves around.

Once you've become comfortable with building displays in Designer, you should
investigate the system for writing your own displays using Python code (see 
:doc:`/tutorials/scripted_displays`).
