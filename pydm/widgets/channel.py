class PyDMChannel:
    """
    Object to hold signals and slots for a PyDM Widget interface to an external
    plugin

    The purpose of this class is to create a templated slot and signals list
    that can be sent to an external plugin. The type of plugin is determined by
    the PyDMApplication based on the identifier placed at the beginning of the
    :attr:`.address` attribute. This allows a generic way to connect slots and
    signals to functionality within your PyDM Widget. Slots should be connected
    to functions on your created widget that perfrom actions upon changes. For
    instance, the :attr:`.value_slot` will be automatically called
    everytime a new value is found by the plugin. This should probably linked
    to a function that updates the display to report the new value.  Signals
    perform the reverse operation. These should be used to send new values back
    to the plugin to update the source.

    Using this structure to interface with plugins allows your created PyDM
    Widget a greater flexibility in choosing its underlying source. For
    instance, returning to the example of the :attr:`.value_slot`,
    getting a value to display from channel access or from the EPICS Archiver
    are very different operations. However, actually displaying the value
    should be identical. By simplying attching your PyDM Widget's display
    functionality to the :attr:`.value_slot` you have created a
    Widget that can do either interchangeably, all the user has to do is
    specify the correct address signature and the rest of the work is done by
    the underlying plugins.  

    :param address: The name of the address to be used by the plugin. This
                    should usually be a user inputted field when a specific
                    PyDM widget is initialized 
    :type  address: str

    :param connection_slot: A function to be run when the connection state
                            changes
    :type connection_slot:  pyqtSlot        

    :param value_slot: A function to be run when the value updates
    :type  value_slot: pyqtSlot

    :param severity_slot: A function to be run when the severity changes
    :type  severity_slot: pyqtSlot

    :param waveform_slot: A function to be run when the waveform value changes
    :type  waveform_slot: pyqtSlot

    :param write_access_slot: A function to be run when the write access changes
    :type  write_access_slot: pyqtSlot

    :param enum_strings_slot: A function to be run when the enum_strings change
    :type  enum_strings_slot: pyqtSlot

    :param unit_slot: A function to be run when the unit changes
    :type  unit_slot: pyqtSlot

    :param value_signal: Attach a signal here that emits a desired value
    :type  value_signal: pyqtSignal

    :param waveform_signal: Attach a signal here that emits a desired waveform
    :type  waveform_signal: pyqtSignal
    
    :param prec_slot: A function to be run when the precision value changes
    :type  prec_slot: pyqtSlot
    """
    def __init__(self, address=None, connection_slot=None, value_slot=None, 
                 waveform_slot=None, severity_slot=None, write_access_slot=None, 
                 enum_strings_slot=None, unit_slot=None, prec_slot=None,
                 value_signal=None, waveform_signal=None):

        self.address = address
        
        self.connection_slot   = connection_slot
        self.value_slot        = value_slot
        self.severity_slot     = severity_slot
        self.waveform_slot     = waveform_slot
        self.write_access_slot = write_access_slot
        self.enum_strings_slot = enum_strings_slot
        self.unit_slot         = unit_slot
        self.prec_slot         = prec_slot
        
        self.value_signal    = value_signal
        self.waveform_signal = waveform_signal
