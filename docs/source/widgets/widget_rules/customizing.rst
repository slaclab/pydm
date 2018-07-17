================================
Customizing Properties for Rules
================================

The rules mechanism is very flexible and allow developers to customize
which properties from the widgets are exposed.

By default, ``PyDMPrimitiveWidget`` (base class for all the PyDM Widgets) defines
two constants:

.. code-block:: python

    DEFAULT_RULE_PROPERTY = "Visible"

    RULE_PROPERTIES = {
        'Enable': ['setEnabled', bool],
        'Visible': ['setVisible', bool],
    }

- **DEFAULT_RULE_PROPERTY**
    Defines the default property to be selected from the list when creating a new
    rule using the ``Rules Editor``.

- **RULE_PROPERTIES**
    This constant holds a dictionary in which the key element is the "user-friendly"
    name of the property and the value is a list in which the first element is the
    property name as a String and the second is the expected data type.

You can customize those constants at your widget and that will reflect on what
users are able to tweak and use when creating new rules.