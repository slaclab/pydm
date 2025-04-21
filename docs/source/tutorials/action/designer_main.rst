.. _Main:

Main Screen
===========

.. important::

    * Make sure the PCASpy tutorial server is :ref:`running <Setup>`

This will be the main piece of our Beam Positioning application and will group the other
components of this tutorial.

The finished result will look like this:

.. figure:: /_static/tutorials/action/main/main.png
   :scale: 75 %
   :align: center
   :alt: Expert Motor Screen

   Main Screen for Beam Positioning Application


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

  Now that we have a layout, let's take a look at the widgets on this screen:

  .. figure:: /_static/tutorials/action/main/widgets.png
     :scale: 70 %
     :align: center

  * **Step 3.1.**

    The first ``Label`` will be the title of our screen:

    #. Drag and drop a ``Label`` into the previously added ``Vertical Layout``.
    #. Set the ``text`` property of this label to: ``Beam Alignment``.
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

    The second widget that we will add is a ``PyDMImageView``, which will display
    the image coming from our camera:

    #. Drag and drop a ``PyDMImageView`` into the previously added ``Vertical Layout`` under
       the ``Label`` that was added at **Step 3.1**.
    #. Set the ``objectName`` property to ``imageView``.
    #. Set the ``imageChannel`` property to ``ca://IOC:Image``.
    #. Set the ``widthChannel`` property to ``ca://IOC:ImageWidth``.
    #. Set the ``readingOrder`` property to ``Clike``.
    #. Set the ``maxRedrawRate`` property to ``30`` so we can update the image at
       30 Hz.

  * **Step 3.3.**

    The third widget that we will add is a ``Vertical Layout``, which will be the
    placeholder for the controls area of the screen:

    #. Drag and drop a ``Vertical Layout`` into the previously added ``Vertical Layout`` under
       the ``PyDMImageView`` that was added at **Step 3.2**.

  * **Step 3.4.**

    The fourth widget that we will add is a ``Label``, which will be updated with
    the result of the calculation of beam position in the next section (:ref:`LittleCode`):

    #. Drag and drop a ``Label`` into the ``Vertical Layout`` that was added in
       **Step 3.3**.
    #. Set the ``objectName`` property of this widget to ``lbl_blobs``.

       .. important::

          It is very important to set the ``objectName`` property of widgets in
          the designer if you intend to access them using code, otherwise the
          names will be automatically assigned, and will not make much sense later
          on.

    #. Set the ``text`` property to empty so this label will only show information
       when we write to it using the code later on.

  * **Step 3.5.**

    The fifth widget that we will add is another ``Label``, which will show the title
    of our controls area:

    #. Drag and drop a ``Label`` into the ``Vertical Layout`` that was added in
       **Step 3.3** right under the ``Label`` added in **Step 3.5**.
    #. Set the ``text`` property of this label to: ``Controls``.
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

  * **Step 3.6.**

    The sixth widget that we will add is a ``Frame``, which will be the container
    for our two motors' ``Embedded Displays``:

    #. Drag and drop a ``Frame`` under the ``Label`` added in **Step 3.6**.
    #. Set the ``frameShape`` property to ``StyledPanel``.
    #. Set the ``frameShadow`` property to ``Raised``
    #. Set the ``stylesheet`` property to:

       .. code-block:: css

            QFrame#frame{
                border: 1px solid #FF17365D;
                border-bottom-left-radius: 15px;
                border-bottom-right-radius: 15px;
            }

  * **Step 3.7.**

    The seventh widget that we will add is a ``PyDMEmbeddedDisplay``, which will
    display the ``inline_motor.ui`` with information for our first motor axis:

    #. Drag and drop a ``PyDMEmbeddedDisplay`` into the ``Frame`` added in **Step 3.7**.
    #. Right-click the ``Frame`` from **Step 3.7** and select ``Layout >> Layout Vertically``.
    #. Set the ``macros`` property to ``{"MOTOR":"IOC:m1"}``.
    #. Set the ``filename`` property to ``inline_motor.ui``.

  * **Step 3.8.**

    The eighth widget that we will add is a ``PyDMEmbeddedDisplay``, which will
    display the ``inline_motor.ui`` with information for our second motor axis:

    #. Drag and drop a ``PyDMEmbeddedDisplay`` into the ``Frame`` added in **Step 3.7**.
    #. Set the ``macros`` property to ``{"MOTOR":"IOC:m2"}``.
    #. Set the ``filename`` property to ``inline_motor.ui``.

  * **Step 3.9.**

    Finally, the ninth widget that we will add is a ``PyDMRelatedDisplayButton``, which will
    open the ``All Motors`` screen that will be developed :ref:`later <PurePython>`:

    #. Drag and drop a ``PyDMRelatedDisplayButton`` into the ``Vertical Layout`` added in **Step 2**.
    #. Add the string ``all_motors.py`` to the ``filenames`` property.
    #. Uncheck the ``openInNewWindow`` property.
    #. Set the ``text`` property to: ``View All Motors``

  * **Step 3.10.**

    Once all the widgets are added to the form, it is now time to adjust the layouts
    and make sure that all is well positioned and behaving nicely.

    #. Using the ``Object Inspector`` at the top-right corner of the Qt Designer
       window, select the ``frame`` object and set the properties according
       to the table below:

       ==================================  ==================
       Property                            Value
       ==================================  ==================
       layoutLeftMargin                    0
       layoutTopMargin                     0
       layoutRightMargin                   0
       layoutBottomMargin                  0
       layoutSpacing                       0
       ==================================  ==================

    #. Continuing with the ``Object Inspector``, select the ``vertical layout``
       object right before the ``frame`` and set the properties according to the
       table below:

       ==================================  ==================
       Property                            Value
       ==================================  ==================
       layoutSpacing                       0
       ==================================  ==================

    #. Still with the ``Object Inspector``, now select the top most ``verticalLayout``
       object set the properties according to the table below:

       ==================================  ==================
       Property                            Value
       ==================================  ==================
       layoutSpacing                       0
       ==================================  ==================

    The end result will be something like this:

    .. figure:: /_static/tutorials/action/main/main_all_widgets_ok.png
       :scale: 100 %
       :align: center

* **Step 4.**

  Save this file as ``main.ui``.

  .. warning::
     For this tutorial it is important to use this file name, as it will be referenced
     at the other sections. If you change it please remember to also change at the
     next steps when referenced.

* **Step 5.**

  Test the Expert Motor Screen:

  .. code-block:: bash

     pydm main.ui

  .. figure:: /_static/tutorials/action/main/main.png
     :scale: 75 %
     :align: center
     :alt: Main Application Screen

.. note::
    Purple borders will appear around any widgets that have "Alarm Sensitive Border" enabled.
    These can be removed by simply unchecking the setting. (for the purposes of this tutorial,
    these borders are not significant and can be in either the on or off state)

.. note::
    You can download this file using :download:`this link <../../../../examples/tutorial/main.ui>`.

