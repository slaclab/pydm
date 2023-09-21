.. _Application:

About the Application
=====================


To demonstrate the concepts and capabilities of PyDM, let's develop a real
application composed of PyDM widgets for beam positioning and alignment.


PyDM allows users to create screens in three ways:

#. Using only the Qt Designer application (.ui file)
#. Using Qt Designer and Python Code (.ui and .py files)
#. Using only Python code (.py file)

In most of the cases users will choose between numbers 1 and 2 and in rare cases
go with number 3.

This tutorial will also cover the three scenarios above while building the proposed
application.

The application is a simulated x-ray beam positioning/alignment application
in which the data from a camera will be presented along with two mirror motor
axes to position the beam in X and Y.

.. figure:: /_static/tutorials/action/application.png
   :scale: 100 %
   :align: center
   :alt: Tutorial Application

   Proposed Application Main Screen

.. _App Components:

Macro Components
----------------

.. figure:: /_static/tutorials/action/components.png
   :scale: 100 %
   :align: center
   :alt: Tutorial Application

- The ``main.ui`` file (Highlighted in Red) uses an embedded display
  (Highlighted in Green) two times, which points to ``inline_motor.ui`` for **Motor X**
  and **Motor Y**.

- Inside of this embedded display there is a related display button (Highlighted
  in Orange) which launches the ``expert_motor.ui`` for configuration of motor
  parameters.

- Finally, the **View All Motors** related display button (Highlighted in Blue)
  launches the ``all_motors.py`` screen in which we can list all motor axes
  available.
