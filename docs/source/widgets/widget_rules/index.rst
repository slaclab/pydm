============================
Widget Rules
============================

Every PyDM Widget has a property named ``rules`` which is a String that holds a
JSON-formatted list of dictionaries describing the rules associated with that
widget.

The widget rules are intended to modify a widget property based on the evaluation
of an expression that can use value of one or more channels in it.

-----------------------------
Creating Rules
-----------------------------

Opening the Editor
******************

With the designer screen open, add a PyDM Widget to the screen and right-click
on it to show the Task Menu and select the ``Edit Rules...`` option.

Here is a step-by-step video on how to open the ``Rules Editor``.

.. figure:: /_static/widgets/widget_rules/open_editor.gif
   :scale: 100 %
   :align: center
   :alt: Rules Editor


Here is a screenshot of the ``Rules Editor`` screen in detail.

.. figure:: /_static/widgets/widget_rules/rules_editor.png
   :align: center
   :alt: Rules Editor


Adding New Rule
***************

With the ``Rules Editor`` screen open, users are able to create new rules by
clicking on the **Add Rule** button on the top left side or delete a rule by
clicking on the **Remove Rule** sign.

- **Rule Name**
   It is very  important to give a meaningful name to a rule in order to troubleshoot
   it as well as make it clear for others what this rule does.

- **Property**
   The property combo box will display all possible options to be configured at this
   widget using the rules mechanism. Most of the widgets will allow users to tweak
   the following properties:

   - **Visible**:
      If the result of the expression is **True** the widget will be visible, otherwise it will be hidden.


   - **Enable**:
      If the result of the expression is **True** the widget will be enabled, otherwise it will be disabled.

   Once a property is selected, it is time to add at least one channel to be used
   as trigger and value for the expression.

- **Channels**
   To do so, click at the **+ Add Channel** button on top of the table and fill in
   the channel address.

   The ``Trigger`` option defines if the expression will be evaluated or not when
   this channel's value is changed. At least one channel must be marked as ``Trigger``.

   The ``Enum?`` option defines if the channel's value will be converted to its
   enumeration string value (when possible). When checked and a conversion is
   possible, the expression should work with a text comparison. (NOTE: Uncheck
   this when using MEDM calculation expressions, which always use the default
   data type from the channel, to prevent automatic conversion to a text value.)

   With the channel(s) added, it is time to create the expression.

- **Initial Value**
   The value set here will be sent to the widget upon instantiation of the Rule.
   The value will be casted to the type expected the property.
   Users can also use macros here and the macro value will be cast as other values.

   .. Note::
      Initial Value does not accept expressions. It is just a simple value to be
      configured into the selected property before the channels connect and the
      rule start being evaluated.

.. _Expression:

- **Expression**
   When the user selects a property, the ``Expected Type`` label is updated with
   the expected data type for the given property.

   It is the user responsibility to cast the data properly and ensure that the
   proper data type or equivalent is the result of the evaluation.  (See the
   ``Enum?`` option above.)

   In order to get data from the ``channels`` configured before, one must use the
   special function ``ch[...]`` and specify the ``channel index`` according to the
   table, **starting from 0**. E.g. ``ch[0]`` will fetch the value from the first
   channel, ``ch[2]`` will fetch the value of the third channel and not the second.

   To make the expression mechanism more flexible, users can make usage of the
   following libraries:

   - **Numpy**: http://www.numpy.org/
      In order to use the Numpy library functions you will need to use the **np.**
      prefix. E.g:
      For Numpy Absolute (https://docs.scipy.org/doc/numpy/reference/generated/numpy.absolute.html)
      you should use: ``np.absolute(...)``.

   - **Math**: https://docs.python.org/3.6/library/math.html
      The math module from Python is imported in full so different than the Numpy
      case, all the functions are already imported and can be used directly without
      the need to explicitly use the module name.

   .. Note::
      For now, PyDM only provide support for Numpy and Math, in case other libraries
      or modules are required for the expression namespace please open an Issue so
      we can add it.
