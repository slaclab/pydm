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
