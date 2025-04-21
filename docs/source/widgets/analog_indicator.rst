#######################
Analog Indicator
#######################

PyDM analog indicator meant to be an easily scannable widget that provides additional context to the current value of a PV.
It provides context via drawing alarm regions and a normal range region.  When the value is in an alarm region the alarm
region changes color.

.. image:: /_static/widgets/analog_indicator/analog_indicator.png
    :scale: 100%
    :align: center

The indicator and scale are not drawn when the widget is initially dragged in to designer.  The widget must be rescaled for the
indicator and scale to be drawn.

The indicator and scale size do not depend on the size of the widget.  The indicator and scale can be resized with the use
of the scaleHeight and backgroundSizeRate properties.  Smallest suggested size is scaleHeight = 23 and
backgroundSizeRate = 0.4.

.. image:: /_static/widgets/analog_indicator/smallest_size_visual.png
    :scale: 100%
    :align: center
.. image:: /_static/widgets/analog_indicator/smallest_size_set.png
    :scale: 100%
    :align: center

* Suggested Orientations

Horizontal with value displayed on the right.
Vertical with value displayed on bottom.

Alarm Region Configuration
==========================
Alarm regions can be fetched from the channel or hard coded in designer.

Alarm region color change is not tied to the alarmSensitiveContent property.  If the color change is not
desired set the alarm colors to be the same as the alarm region color.

There are a few methods of not drawing alarm regions.
  1. Set the alarm to the corresponding limit. Do not set the alarm to outside of the limits, this will cause drawing errors.
  2. Set userUpperMajorAlarm = userLowerMajorAlarm = 0.  Or set userUpperMinorAlarm = userLowerMinorAlarm = 0.
  3. If any alarm value is set to nan (not a number), those regions won't draw.  Setting an alarm value to nan is not possible in designer.

.. figure:: /_static/widgets/analog_indicator/no_upper_minor.png
    :scale: 100%
    :align: center

    Alarm region value set to corresponding limit

.. figure:: /_static/widgets/analog_indicator/no_minor.png
    :scale: 100%
    :align: center

    Alarm region values both set to zero
