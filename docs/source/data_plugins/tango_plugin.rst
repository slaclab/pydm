========================
Tango Plugin
========================

The Tango Plugin connects PyDM widgets to attributes of `Tango Controls <https://www.tango-controls.org>`_
devices using `PyTango <https://pytango.readthedocs.io>`_. It is only available if PyTango is installed.

General Tango Plugin channel syntax::

    tango://domain/family/member/attribute
    tango://host:port/domain/family/member/attribute
    tango://host:port/domain/family/member/attribute#dbase=no
    tango://device_alias/attribute

Without ``host:port``, the Tango database given by the ``TANGO_HOST`` environment variable is used.

To show the setpoint of a writable attribute, add ``?w_value`` to the address, e.g.
``tango://sys/tg_test/1/double_scalar?w_value``. Such a channel receives the write value of the
attribute with every update of its read value. Writing to it writes the attribute as usual.

Values are received through Tango change events. If an attribute is not configured to send change
events (it is not polled by the device server, or no change thresholds are set), the plugin falls back
to reading the attribute periodically. The period in milliseconds can be set with the
``PYDM_TANGO_POLL_PERIOD`` environment variable (default: 1000).

The attribute configuration is mapped onto the channel metadata, and is kept up to date through
attribute configuration events:

=============================== =========================================
Tango                           PyDM
=============================== =========================================
quality                         alarm severity (``WARNING`` → minor,
                                ``ALARM`` → major, ``INVALID`` → invalid)
writable                        write access
unit                            unit
format (e.g. ``%6.3f``)         precision
min_value / max_value           lower / upper control limit
min_alarm / max_alarm           lower / upper alarm limit
min_warning / max_warning       lower / upper warning limit
enum_labels                     enum strings
=============================== =========================================

``DevState`` and ``DevBoolean`` attributes are sent as integers, together with the state names or
``("False", "True")`` as enum strings, so they can be used with enum widgets such as
``PyDMEnumComboBox``. Spectrum and image attributes are sent as numpy arrays.

Commands
--------

If the device has no attribute of the given name but a command, the channel is a command channel::

    tango://domain/family/member/command
    tango://domain/family/member/command?argout

Connecting to a command channel never executes the command. It is executed whenever a value is
written to the channel, with that value as the input argument (ignored for commands without input).
Before the first execution, the channel has a neutral value of the input type (``0``, ``0.0``, ``""``
or an empty array), so that write widgets can send values and convert user input to the right type.
Afterwards, its value is the last input argument.

The ``?argout`` channel is read only and receives the output argument every time the command is executed
from the application, e.g. to show it in a ``PyDMLabel``. It does not execute the command by itself.

Typical widgets:

* ``PyDMPushButton`` with a ``pressValue`` (e.g. ``1``) for commands without input. Enable
  ``showConfirmDialog`` for commands that should not be executed by accident.
* ``PyDMLineEdit``, ``PyDMSpinbox`` or ``PyDMCheckbox`` for commands with input.

``State`` and ``Status`` are both attributes and commands, the attribute is used. Commands do not send
events, so the connection state of a command channel is checked by pinging the device every
``PYDM_TANGO_POLL_PERIOD`` milliseconds. Errors while executing a command, e.g. because it is not
allowed in the current state, are logged.
