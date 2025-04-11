.. _Expert:

Expert Motor Screen
===================

.. important::

    * Make sure the PCASpy tutorial server is :ref:`running <Setup>`

For this screen we will present detailed information to the user for the motors.
Also, to ensure that we can reuse this screen in other displays, it will be
necessary to use :ref:`Macros` that will later be replaced by the proper information
for each motor.

The finished result will look like this:

.. figure:: /_static/tutorials/action/expert/expert.png
   :scale: 75 %
   :align: center
   :alt: Expert Motor Screen

   Expert Motor Screen


* **Step 1.**

  Let's start by opening the :ref:`Qt Designer <Designer>`
  and creating a new ``Widget``.

  .. figure:: /_static/tutorials/action/new_widget.gif
     :scale: 100 %
     :align: center

* **Step 2.**

  With the new form available, let's add a ``Vertical Layout`` widget and make
  it fill the whole form. Let's select ``Layout Vertically`` for the Form.

  .. figure:: /_static/tutorials/action/inline/inline_layout.gif
     :scale: 100 %
     :align: center

* **Step 3.**

  Now that we have a layout, let's take a look at the widgets we'll use on this
  screen:

  .. figure:: /_static/tutorials/action/expert/widgets.png
     :scale: 70 %
     :align: center


  * **Step 3.1.**

    The first ``Label`` will be the title of our screen:

    #. Drag and drop a ``Label`` into the previously added ``Vertical Layout``.
    #. Set the ``text`` property of this label to: ``Configuring Motor: ${MOTOR}``.

       .. note::

          :ref:`Macros` are not something exclusive to PyDM Widgets, they can be
          used with any kind of widget (even the basic Qt widgets) and in any
          property. In this case we are using it to add the motor ``PV`` name
          to the title.  However, due to limitations in Qt Designer, you cannot
          specify a macro for a variable that is numeric-only inside Designer
          itself.  An (unfortunate) work-around is to edit the .ui file in a
          text editor, and insert your macro variable into the XML that defines
          the display.

    #. In order to make the label look better as a title, add the following to
       the ``stylesheet`` property:

       .. code-block:: css

           QLabel {
            qproperty-alignment: AlignCenter;
            border: 1px solid #FF17365D;
            border-top-left-radius: 15px;
            border-top-right-radius: 15px;
            background-color: #FF17365D;
            padding: 5px 0px;
            color: rgb(255, 255, 255);
            max-height: 25px;
            font-size: 14px;
           }

  * **Step 3.2.**

    The second widget that we will add is a ``Frame``, which will be the container
    of the fields in our form:

    #. Drag and drop a ``Frame`` into the previously added ``Vertical Layout`` under
       the ``Label`` that was added at **Step 3.1**.
    #. Set the ``frameShape`` property to ``StyledPanel``.
    #. Set the ``frameShadow`` property to ``Raised``.
    #. In order to add some nice rounded corners to this frame, add the following
       to the ``stylesheet`` property:

       .. code-block:: css

           QFrame#frame{
        	border: 1px solid #FF17365D;
	        border-bottom-left-radius: 15px;
	        border-bottom-right-radius: 15px;
           }

  * **Step 3.3.**

    Now to ensure the alignment and positioning of the form content, let's add a
    ``Form Layout``:

    #. Drag and drop a ``Form Layout`` into the previously added ``Frame``.
    #. Right-click the ``Frame`` and select ``Layout > Layout Vertically``.

       - This will make the ``Form Layout`` fill the whole space of the ``Frame``
         and make our form behave better when resizing.

    #. Set the ``frameShadow`` property to ``Raised``.
    #. In order to add some nice rounded corners to this frame, add the following
       to the ``stylesheet`` property:

       .. code-block:: css

           QFrame#frame{
        	border: 1px solid #FF17365D;
	        border-bottom-left-radius: 15px;
	        border-bottom-right-radius: 15px;
           }

  * **Step 3.4.**

    Now that we have our ``Form Layout`` ready, it is time to start adding the form
    widgets. Let's start with the first pair of ``Label`` and ``PyDMLineEdit`` that
    will be used to edit the **Description** of the Motor:

    #. Drag and drop a ``Label`` into the the previously added ``Form Layout``.
    #. Set the ``text`` property to ``Description:``.
    #. Drag and drop a ``PyDMLineEdit`` into the ``Form Layout`` paying attention to
       add it on the right side of the previously added ``Label``.

       .. note::

          The area that will match the ``Label`` will be highlighted with red
          borders. When that happens you will know that the widget will be placed
          at the expected place.

    #. Set the ``channel`` property to ``ca://${MOTOR}.DESC``.
    #. Set the ``displayFormat`` property to ``String``.

  * **Step 3.5.**

    Let's now add the second pair of ``Label`` and ``PyDMLineEdit`` that
    will be used to edit the **Position** of the Motor:

    #. Drag and drop a ``Label`` into the the previously added ``Form Layout`` right
       under the previously added components.

       .. note::

          The area will be highlighted with blue line. When that happens you will
          know that the widget will be placed at the expected place.

    #. Set the ``text`` property to ``Position:``.
    #. Drag and drop a ``PyDMLineEdit`` into the ``Form Layout`` paying attention to
       add it on the side of the previously added ``Label``.
    #. Set the ``channel`` property to ``ca://${MOTOR}.VAL``.
    #. Set the ``displayFormat`` property to ``Decimal``.
    #. Select the ``showUnits`` property.
    #. Expand the ``maximumSize`` property and set the ``Width`` property to ``150``.

  * **Step 3.6.**

    Let's now add a ``Label``, and this time, a ``PyDMLabel`` that
    will be used to read the **Readback Position** of the Motor:

    #. Drag and drop a ``Label`` into the the previously added ``Form Layout`` right
       under the previously added components.
    #. Set the ``text`` property to ``Readback:``.
    #. Drag and drop a ``PyDMLabel`` to the ``Form Layout`` paying attention to
       add it on the right side of the previously added ``Label``.
    #. Set the ``channel`` property to ``ca://${MOTOR}.RBV``.
    #. Set the ``displayFormat`` property to ``Decimal``.
    #. Select the ``showUnits`` property.

  * **Step 3.7.**

    Let's add another ``Label`` and ``PyDMLineEdit`` pair that will be used
    to edit the **Velocity** of the Motor:

    #. Drag and drop a ``Label`` into the the previously added ``Form Layout`` right
       under the previously added components.
    #. Set the ``text`` property to ``Velocity:``.
    #. Drag and drop a ``PyDMLineEdit`` to the ``Form Layout`` paying attention to
       add it on the side of the previously added ``Label``.
    #. Set the ``channel`` property to ``ca://${MOTOR}.VELO``.
    #. Set the ``displayFormat`` property to ``Decimal``.
    #. Select the ``showUnits`` property.
    #. Expand the ``maximumSize`` property and set the ``Width`` property to ``150``.


  * **Step 3.8.**

    And now to the last ``Label`` and ``PyDMLineEdit`` pair that will be used
    to edit the **Acceleration** of the Motor:

    #. Drag and drop a ``Label`` into the the previously added ``Form Layout`` right
       under the previously added components.
    #. Set the ``text`` property to ``Acceleration:``.
    #. Drag and drop a ``PyDMLineEdit`` to the ``Form Layout`` paying attention to
       add it on the side of the previously added ``Label``.
    #. Set the ``channel`` property to ``ca://${MOTOR}.ACCL``.
    #. Set the ``displayFormat`` property to ``Decimal``.
    #. Select the ``showUnits`` property.
    #. Expand the ``maximumSize`` property and set the ``Width`` property to ``150``.


  * **Step 3.9.**

    Once all the widgets are added to the form, it is now time to adjust the layouts
    and make sure that everything is well-positioned and behaving nicely.

    #. Using the ``Object Inspector`` at the top-right corner of the Qt Designer
       window, select the ``formLayout`` object and set the properties according
       to the table below:

       ==================================  ==================
       Property                            Value
       ==================================  ==================
       layoutTopMargin                     6
       layoutRightMargin                   6
       layoutBottomMargin                  6
       layoutHorizontalSpacing             10
       layoutVerticalSpacing               10
       layoutLabelAlignment > Horizontal   AlignRight
       layoutLabelAlignment > Vertical     AlignVCenter
       layoutFormAlignment > Horizontal    AlignLeft
       layoutFormAlignment > Vertical      AlignVCenter
       ==================================  ==================

    #. Continuing with the ``Object Inspector``, select the ``frame`` object,
       scroll down the ``Property Editor`` until the end and set the properties
       according to the table below:

       ==================================  ==================
       Property                            Value
       ==================================  ==================
       layoutLeftMargin                    0
       layoutTopMargin                     0
       layoutRightMargin                   0
       layoutBottomMargin                  0
       layoutSpacing                       0
       ==================================  ==================

    #. Still with the ``Object Inspector``, now select the ``verticalLayout`` object
       that is right under the ``Form`` object and set the properties according
       to the table below:

       ==================================  ==================
       Property                            Value
       ==================================  ==================
       layoutSpacing                       0
       ==================================  ==================

    #. Finally, with the ``Object Inspector`` select the ``Form`` object
       set the properties according to the table below:

       ==================================  ==================
       Property                            Value
       ==================================  ==================
       geometry > Width                    450
       geometry > Height                   217
       layoutLeftMargin                    0
       layoutTopMargin                     0
       layoutRightMargin                   0
       layoutBottomMargin                  0
       layoutSpacing                       0
       ==================================  ==================

    The end result will be something like this:

    .. figure:: /_static/tutorials/action/expert/expert_all_widgets_ok.png
       :scale: 100 %
       :align: center

* **Step 4.**

  Save this file as ``expert_motor.ui``.

  .. warning::
     For this tutorial it is important to use this file name, as it will be referenced
     at the other sections. If you change it please remember to also change it in the
     next steps when referenced.

* **Step 5.**

  Test the Expert Motor Screen:

  .. code-block:: bash

     pydm -m '{"MOTOR":"IOC:m1"}' expert_motor.ui

  .. figure:: /_static/tutorials/action/expert/expert.png
     :scale: 75 %
     :align: center
     :alt: Expert Motor Screen

.. note::
    You can download this file using :download:`this link <../../../../examples/tutorial/expert_motor.ui>`.