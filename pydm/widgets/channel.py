class PyDMChannel:
    """
    Object to hold signals and slots for a PyDM Widget interface to an external
    plugin

    The purpose of this class is to create a templated slot and signals list
    that can be sent to a plugin based on the identifier placed at the
    beginning of the :attr:`.address` attribute. This allows a generic way to
    connect slots and signals to functionality within your PyDM Widget. Slots
    should be connected to functions on your created widget that perfrom
    actions upon changes. For instance, the :attr:`value slot` will be
    automatically called everytime a new value is found by the plugin. This
    should probably link to a function that updates the display to report the
    new value.  Signals perform the reverse operation. These should be used to
    send new values back to the plugin to update the source.

    Using this structure to interface with plugins allows your created PyDM
    Widget a greater flexibility in choosing its underlying source. For
    instance, returning to the example of the :attr:'value_slot`, getting a
    value to display from channel access or from the EPICS Archiver are very
    different operations. However, displaying the value should be identical. By
    simplying attching your PyDM Widget's display functionality to the
    :attr:`value_slot` you have created a Widget that can do either
    interchangeably, all the user has to do is specify an address pertaining to
    either one and the rest of the work is done by the underlying plugins.  

    :param address: The name of the address to be used by the plugin. This
                    should usually be a user inputted field when a specific
                    PyDM widget is initialized 
    :type  address: str

    :param connection_slot:

    :param value_slot:

    :param severity_slot:

    :param waveform_slot:

    :param write_access_slot:

    :param enum_strings_slot:

    :param unit_slot:

    :param value_signal:

    :param waveform_signal:
    """
  def __init__(self, address=None, connection_slot=None, value_slot=None, 
               waveform_slot=None, severity_slot=None, write_access_slot=None, 
               enum_strings_slot=None, unit_slot=None, value_signal=None, 
               waveform_signal=None):

    self.address = address
    
    self.connection_slot   = connection_slot
    self.value_slot        = value_slot
    self.severity_slot     = severity_slot
    self.waveform_slot     = waveform_slot
    self.write_access_slot = write_access_slot
    self.enum_strings_slot = enum_strings_slot
    self.unit_slot         = unit_slot
    
    self.value_signal    = value_signal
    self.waveform_signal = waveform_signal
